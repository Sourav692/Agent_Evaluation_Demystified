"""Week 16 acceptance tests. Run from new_course/:
    python3 -m pytest weeks/week-16-distributed-evaluation-capstone
"""

import importlib.util
import json
import sys
from pathlib import Path

import pytest

_spec = importlib.util.spec_from_file_location("week16_lab", Path(__file__).parents[1] / "lab.py")
lab = importlib.util.module_from_spec(_spec)
sys.modules["week16_lab"] = lab
_spec.loader.exec_module(lab)


@pytest.fixture(scope="module")
def fair(tmp_path_factory):
    return lab.simulate("fair", tmp_path_factory.mktemp("fair"))


@pytest.fixture(scope="module")
def fifo(tmp_path_factory):
    return lab.simulate("fifo", tmp_path_factory.mktemp("fifo"))


def by_candidate(sim, candidate):
    return next(r for r in lab.request_rows(sim) if r["spec"].get("candidate") == candidate)


def test_release_requests_get_the_week_12_verdicts_through_the_queue(fair):
    assert by_candidate(fair, "v2.1")["outcome"]["verdict"] == "SHIP"
    blocked = by_candidate(fair, "v2.3")["outcome"]
    assert blocked["verdict"] == "BLOCK"
    assert blocked["reasons"][0] == "no-unauthorized-refunds FAIL (release 0, safety_probe 1) cases ['t-015']"


def test_sharded_runs_equal_the_single_process_runs(fair, tmp_path):
    rid = by_candidate(fair, "v2.1")["request_id"]
    lab.W12.produce("v2.1", tmp_path, lab.RELEASE_POLICY, now=lambda: "-")
    for run in ("release", "safety_probe"):
        merged = json.loads((fair["out"] / rid / "v2.1" / run / "results.json").read_text())
        single = json.loads((tmp_path / run / "results.json").read_text())
        assert merged["config"]["workers"] == 4
        for k in ("started_at", "config"):
            merged.pop(k), single.pop(k)
        assert merged == single                                     # same run_id, cases, summary and versions
        assert lab.W11.verify_artifact(fair["out"] / rid / "v2.1" / run) == []


def test_admission_checks_role_budget_quota_and_duplicates(fair):
    got = [(a["actor"], a["what"], a["status"], a["reason"]) for a in fair["admissions"] if a["status"] != "admitted"]
    assert got == [("rag.engineer", "hybrid@k10", "denied", "quota"),
                   ("refunds.engineer", "v2.1", "duplicate", ""),
                   ("refunds.viewer", "v2.4", "denied", "role"),
                   ("refunds.engineer", "v2.4", "denied", "budget")]
    budget = next(a for a in fair["admissions"] if a["reason"] == "budget")
    assert budget["detail"] == "spent 0.0000 + reserved 0.2700 + this request 0.0900 > 0.3"
    v23 = next(a for a in fair["admissions"] if a["what"] == "v2.3")
    assert (v23["jobs"], v23["new"]) == (12, 6)                     # the baseline's 6 shards are shared, not rerun
    resubmitted = fair["admissions"][-1]
    assert (resubmitted["at"], resubmitted["what"], resubmitted["status"]) == (240, "hybrid@k10", "admitted")


def test_a_budget_check_without_reservations_admits_what_the_budget_cannot_cover(tmp_path):
    loose = lab.simulate("fair", tmp_path, check_reserved=False)
    v24 = next(a for a in loose["admissions"] if a["what"] == "v2.4" and a["actor"] == "refunds.engineer")
    assert v24["status"] == "admitted" and v24["reserved"] == 0.09


def test_a_full_queue_refuses_new_work(monkeypatch):
    monkeypatch.setitem(lab.QUEUE, "capacity", 12)
    platform = lab.build_platform(lab.DayClock())
    lab.W14.seed(platform)
    spec = {"kind": "release", "dataset": "tool-cases", "candidate": "v2.1", "baseline": "v2"}
    assert lab.admit(platform, "refunds.engineer", spec, 0)["status"] == "admitted"
    full = lab.admit(platform, "safety.engineer", {"kind": "suite", "dataset": "fault-cases", "suite": "faults",
                                                    "agent": "stable_key", "backend": "lax"}, 1)
    assert (full["status"], full["reason"]) == ("denied", "capacity")
    assert full["detail"] == "12 active + 2 new > queue capacity 12: retry later"


def test_a_crashed_worker_loses_no_job_and_charges_once(fair):
    events = lab.job_history(fair, "job-4366b8ce3d")
    assert [(at, w, kind) for at, w, kind, _d in events] == [
        (5, None, "enqueued"), (90, "w2", "leased"), (150, "w2", "retry"), (160, "w4", "leased"), (180, "w4", "done")]
    assert fair["workers"]["w2"] == {"alive": False, "leases": 4}
    rows = fair["conn"].execute("SELECT COUNT(*) FROM usage WHERE run_id='job-4366b8ce3d'").fetchone()[0]
    assert rows == 1


def test_a_stalled_worker_cannot_overwrite_or_double_charge(fair):
    events = lab.job_history(fair, "job-0fef34a3a7")
    assert [(at, w, kind) for at, w, kind, _d in events][-3:] == [(200, "w4", "leased"), (230, "w4", "done"),
                                                                  (260, "w3", "stale")]
    assert lab.job(fair["conn"], "job-0fef34a3a7")["lease_token"] == 2
    assert fair["stale"] == [{"job_id": "job-0fef34a3a7", "worker": "w3", "at": 260}]
    assert round(fair["wasted_usd"], 4) == 0.0132                     # work done twice, charged once


def test_a_poison_job_stops_after_three_attempts_and_the_run_is_recorded_unfinished(fair):
    events = lab.job_history(fair, "job-aa6554ec60")
    assert [(at, kind) for at, _w, kind, _d in events] == [
        (10, "enqueued"), (50, "leased"), (51, "retry"), (71, "leased"), (72, "retry"), (102, "leased"), (103, "dead")]
    sweep = next(r for r in lab.request_rows(fair) if r["tenant"] == "trust-safety")
    assert sweep["state"] == "unfinished"
    assert sweep["outcome"]["problems"] == [
        "incomplete run: 10 of 11 cases (dead-lettered shards: job-aa6554ec60)"]


def test_every_finished_job_is_charged_exactly_once(fair):
    assert lab.charges(fair) == {("done", 1): 64, ("dead", 0): 1}
    usage = {u["tenant"]: (u["runs"], u["cost_usd"]) for u in fair["platform"].usage("platform.auditor")}
    assert usage == {"support-rag": (45, 0.09), "refunds-agent": (18, 0.174), "trust-safety": (1, 0.012)}


def test_fair_dispatch_protects_the_quiet_tenants_from_the_flood(fifo, fair):
    a, b = lab.tenant_stats(fifo), lab.tenant_stats(fair)
    assert {t: (s["p50"], s["p95"]) for t, s in a.items()} == {
        "refunds-agent": (455, 510), "support-rag": (180, 370), "trust-safety": (470, 490)}
    assert {t: (s["p50"], s["p95"]) for t, s in b.items()} == {
        "refunds-agent": (135, 320), "support-rag": (313, 510), "trust-safety": (20, 40)}
    assert [by_candidate(fifo, c)["latency"] for c in ("v2.1", "v2.3")] == [495, 530]
    assert [by_candidate(fair, c)["latency"] for c in ("v2.1", "v2.3")] == [245, 340]


def test_the_slo_report_shows_what_fairness_cannot_fix(fair):
    report = {(s["subject"], s["slo"][:7]): (s["measured"], s["met"]) for s in lab.slo_report(fair)}
    rid = {c: by_candidate(fair, c)["request_id"] for c in ("v2.1", "v2.3")}
    assert report[(rid["v2.1"], "release")] == (245, True)
    assert report[(rid["v2.3"], "release")] == (340, False)            # a capacity problem, not a fairness one
    assert report[("trust-safety", "queue w")] == (40, True)


def test_each_request_is_one_trace_across_the_queue(fair):
    rid = by_candidate(fair, "v2.1")["request_id"]
    root = fair["roots"][rid]
    spans = [s for s in fair["tracer"].spans if s.trace_id == root.trace_id]
    children = [s for s in spans if s is not root]
    assert len(children) == 13 and all(s.parent_id == root.span_id and s.kind == "EVALUATOR" for s in children)
    failed = [s for s in children if s.status == "ERROR"]
    assert [s.attributes["job.id"] for s in failed] == ["job-4366b8ce3d"]
    assert failed[0].status_message == "lease expired on w2"
    assert (root.start_ms, root.end_ms) == (5000, 250000)


def test_the_audit_log_records_each_request_and_the_chain_holds(fair):
    rid = by_candidate(fair, "v2.3")["request_id"]
    trail = lab.request_audit(fair, rid)
    assert [e["action"] for e in trail] == ["eval.run", "eval.admit", "release.decided"]
    assert trail[1]["detail"].startswith("refunds-agent/tool-cases@v1 sha256 ")
    assert trail[2]["detail"].startswith("BLOCK; decision sha256 ")
    assert fair["platform"].verify_audit() == []
    denied = [e["reason"] for e in fair["platform"].audit("platform.auditor") if e["decision"] == "deny"]
    assert denied == ["quota", "role", "budget"]


def test_drill_1_charging_inside_the_job_double_charges_a_retried_job():
    broken = lab.double_charge_drill(fixed=False)
    assert [(r[0], r[3]) for r in broken] == [("run-0001", 0.0288), ("run-0002", 0.0288)]
    assert lab.double_charge_drill(fixed=True) == [("job-drill-1", "refunds-agent", 30, 0.0288)]


def test_drill_2_merging_only_present_shards_hides_the_lost_case(fair):
    sweep = next(r for r in lab.request_rows(fair) if r["tenant"] == "trust-safety")
    jobs = [lab.job(fair["conn"], j) for j in json.loads(fair["conn"].execute(
        "SELECT job_ids FROM requests WHERE request_id=?", (sweep["request_id"],)).fetchone()[0])]
    results = [json.loads(j["result"]) if j["result"] else None for j in jobs]
    expected = [c for j in jobs for c in json.loads(j["payload"])["cases"]]
    skeleton = lab.execute({**json.loads(jobs[0]["payload"]), "cases": []}, "-")[0]
    hidden = lab.merge_present_shards(skeleton, results, expected, 4, [])
    assert (hidden["complete"], hidden["expected_cases"]) == (True, 10)
    honest = lab.merge_shards(skeleton, results, expected, 4, ["job-aa6554ec60"])
    assert (honest["complete"], honest["expected_cases"], honest["completed_cases"]) == (False, 11, 10)
    assert {c["case_id"] for c in expected} - {c["case_id"] for c in hidden["cases"]} == {"f-011"}


def test_real_threads_finish_every_job_and_charge_each_once(tmp_path):
    result = lab.thread_trial(tmp_path / "queue.db", n_jobs=150, n_threads=4)
    assert result["done"] == result["usage_rows"] == result["charged_jobs"] == 150
    assert result["crashed_worker"] is not None and result["retried"] >= 1


# --- The notebook and the theory HTML stay in step with lab.py and the theory Markdown

from shared import course_checks  # noqa: E402

HANDSON = Path(__file__).parents[1]
NOTEBOOK = HANDSON / "week-16-distributed-evaluation-capstone-handson.ipynb"
THEORY = HANDSON.parent / "theory" / "week-16-distributed-evaluation-capstone-theory.md"


def test_notebook_uses_the_same_code_as_lab():
    assert course_checks.notebook_drift(NOTEBOOK, HANDSON / "lab.py") == []
    assert len(course_checks.shared_definitions(NOTEBOOK, HANDSON / "lab.py")) >= 30


def test_notebook_runs_top_to_bottom_offline():
    _namespace, printed = course_checks.run_notebook(NOTEBOOK)
    assert "BLOCK: no-unauthorized-refunds FAIL" in printed
    assert "usage rows per job: dead x0: 1, done x1: 64" in printed


def test_theory_html_matches_markdown():
    assert course_checks.html_is_fresh(THEORY), "run: python3 tools/build_html.py"
