"""Week 14 acceptance tests. Run from new_course/:
    python3 -m pytest weeks/week-14-multi-tenant-governance
"""

import importlib.util
import sys
from pathlib import Path

import pytest

_spec = importlib.util.spec_from_file_location("week14_lab", Path(__file__).parents[1] / "lab.py")
lab = importlib.util.module_from_spec(_spec)
sys.modules["week14_lab"] = lab
_spec.loader.exec_module(lab)

from shared import governance  # noqa: E402
from shared.governance import PUBLIC_DENIAL, Denied  # noqa: E402


@pytest.fixture
def day():
    return lab.build_day()


def test_the_scripted_day_runs_every_team_and_denies_one_run_on_budget(day):
    _platform, refs, runs = day
    assert [r.get("run_id") for r in runs] == ["run-0001", "run-0002", "run-0003", "run-0004", "run-0005",
                                              "run-0006", None]
    verdicts = {r["run_id"]: [e["verdict"] for e in r["evaluators"]] for r in runs if "run_id" in r}
    assert verdicts["run-0003"] == ["FAIL", "FAIL"] and verdicts["run-0004"] == ["PASS", "PASS"]   # v1, v2
    assert verdicts["run-0005"] == ["FAIL"] and verdicts["run-0006"] == ["PASS"]   # naive_retry, stable_key
    assert runs[4]["metrics"]["duplicate_refunds"] == 3
    assert runs[-1]["denied"] == "budget exceeded for refunds-agent"
    assert refs["refund-safety"] == "trust-safety/refund-safety@v1"


def test_tenant_and_role_come_from_the_platform_not_the_caller(day):
    platform, refs, _runs = day
    assert platform.principal("refunds.viewer") == governance.Principal("refunds.viewer", "refunds-agent", "viewer")
    with pytest.raises(Denied):
        platform.read_dataset("mallory", refs["tool-cases"])
    with pytest.raises(Denied, match="eval.run is not permitted for role viewer"):
        platform.run_eval("refunds.viewer", refs["tool-cases"], [refs["task-success"]])
    reasons = [e["reason"] for e in platform.audit("platform.auditor") if e["decision"] == "deny"]
    assert reasons[-2:] == ["unknown_principal", "role"]


def test_access_matrix_follows_the_role_table(day):
    matrix = lab.access_matrix(*day)
    allowed = {actor: {k for k, v in row.items() if v == "allow"} for actor, row in matrix.items()}
    assert allowed["platform.auditor"] == {"read usage", "read audit"}
    assert allowed["rag.viewer"] == {"read own dataset", "read own run"}
    assert allowed["refunds.viewer"] == {"read own dataset", "read own run", "use refund-safety"}
    assert allowed["rag.owner"] == {"read own dataset", "write dataset", "write evaluator", "read own run",
                                    "read usage", "read audit"}
    assert all(row["read other team's dataset"] == row["read other team's run"] == "deny" for row in matrix.values())


def test_cross_tenant_probes_are_denied_and_look_like_missing_resources(day):
    platform, _refs, _runs = day
    answers = [answer for _m, _t, answer in lab.probe(platform)]
    assert answers[:-1] == [PUBLIC_DENIAL] * 7
    assert answers[-1] == "evaluator.write is not permitted for role engineer"
    denials = [e for e in platform.audit("platform.auditor") if e["actor"] == "refunds.engineer" and e["decision"] == "deny"]
    assert [e["reason"] for e in denials] == ["budget", "cross_tenant", "cross_tenant", "missing", "cross_tenant",
                                              "cross_tenant", "missing", "cross_tenant", "role"]
    seen_by_rag = [e for e in platform.audit("rag.owner") if e["decision"] == "deny"]
    assert len(seen_by_rag) == 4 and all(e["owner"] == "support-rag" for e in seen_by_rag)


def test_a_shared_evaluator_can_be_used_but_not_changed_by_the_grantee(day):
    platform, refs, _runs = day
    assert platform.read_evaluator("refunds.engineer", refs["refund-safety"])["rules"][0]["limit"] == 0
    with pytest.raises(Denied):
        platform.read_evaluator("rag.engineer", refs["refund-safety"])              # never shared with support-rag
    with pytest.raises(Denied, match=PUBLIC_DENIAL):
        platform.share_evaluator("refunds.owner", refs["refund-safety"], "support-rag")
    shadow = platform.register_evaluator("refunds.owner", "refund-safety", {"rules": []})
    assert shadow == "refunds-agent/refund-safety@v1" != refs["refund-safety"]     # same name, other namespace


def test_registry_entries_are_immutable_and_reads_check_the_hash(day):
    platform, _refs, _runs = day
    lines = lab.registry_story(platform)
    assert [line.split("-> ")[1] for line in lines[:4]] == [
        "refunds-agent/tool-cases@v1", "refunds-agent/tool-cases@v1", "refunds-agent/tool-cases@v2", "high"]
    assert "registry entries are immutable" in lines[4]
    assert "does not match its recorded sha256" in lines[5]


def test_runs_pin_the_dataset_and_evaluator_hashes(day):
    platform, refs, runs = day
    run = platform.read_run("refunds.viewer", "run-0004")
    stored = dict(platform.db.execute("SELECT name, sha256 FROM artifacts WHERE tenant = 'refunds-agent'").fetchall())
    assert run["dataset"] == {"ref": refs["tool-cases"], "sha256": stored["tool-cases"]}
    assert run["dataset"]["sha256"] == governance.sha256_json(platform.read_dataset("refunds.viewer", refs["tool-cases"]))
    assert [e["ref"] for e in run["evaluators"]] == [refs["task-success"], refs["refund-safety"]]
    assert run["runner_args"] == {"agent": "v2"} and run["metrics"]["pass_rate"] == 1.0


def test_a_metric_the_run_did_not_produce_fails_the_rule():
    spec = next(e["spec"] for e in lab.EVALUATORS["evaluators"] if e["name"] == "refund-safety")
    result = governance.evaluate_rules(spec, {"cases": 50, "recall_at_5": 0.9})
    assert result["verdict"] == "FAIL" and {r["status"] for r in result["rules"]} == {"MISSING"}


def test_personal_data_is_redacted_before_anything_is_stored(tmp_path):
    report = lab.redaction_report(tmp_path / "platform.db")
    assert report["raw upload"] == {"emails": 4, "card numbers": 2, "customer IDs": 1, "names": 6}
    assert report["patterns only"]["names"] == 6
    assert report["database file"] == {"emails": 0, "card numbers": 0, "customer IDs": 41, "names": 0}
    assert report["customer_id fields"] == 41                                 # structured, synthetic, needed to replay
    assert report["recall raw"] == report["recall redacted"] == 0.8125


def test_the_audit_log_records_allowed_and_denied_actions_and_hides_other_tenants(day):
    platform, _refs, _runs = day
    events = platform.audit("platform.auditor")
    assert len(events) == 47 and events[-1]["action"] == "audit.read"
    assert sum(e["decision"] == "deny" for e in events) == 1
    rag_view = platform.audit("rag.owner")
    assert rag_view and all("support-rag" in (e["tenant"], e["owner"]) for e in rag_view)
    with pytest.raises(Denied):
        platform.audit("rag.engineer")
    assert all("@example.com" not in str(e) for e in events)


def test_the_chain_catches_a_deletion_and_only_the_anchor_catches_a_rewrite(day):
    platform, _refs, _runs = day
    anchor = platform.audit_head()
    platform.audit("platform.auditor")                                    # event 47
    assert platform.verify_audit(anchor) == []
    lab.delete_event(platform, 46)
    assert platform.verify_audit()[0] == "seq 47: expected seq 46, events are missing"
    lab.rewrite_chain(platform)
    assert platform.verify_audit() == []
    assert platform.verify_audit(anchor) == ["anchor seq 46: hash differs from the one stored outside the database"]


def test_deleting_the_newest_event_is_invisible_to_the_chain_alone(day):
    platform, _refs, _runs = day
    anchor = platform.audit_head()
    lab.delete_event(platform, anchor[0])                                 # the budget denial, the last event
    assert platform.verify_audit() == []
    assert platform.verify_audit(anchor) == ["anchor seq 46: hash differs from the one stored outside the database"]


def test_cost_is_charged_to_the_team_that_ran_the_evaluation(day):
    platform, _refs, _runs = day
    usage = {u["tenant"]: u for u in platform.usage("platform.auditor")}
    assert {t: (u["runs"], u["cases"], u["cost_usd"]) for t, u in usage.items()} == {
        "support-rag": (2, 58, 0.0116), "refunds-agent": (2, 60, 0.068), "trust-safety": (2, 22, 0.0264)}
    assert [u["tenant"] for u in platform.usage("refunds.owner")] == ["refunds-agent"]
    budget = [e for e in platform.audit("platform.auditor") if e["reason"] == "budget"]
    assert budget[0]["detail"] == "spent 0.0680 + estimate 0.0900 > 0.15"


def test_drill_1_trusting_the_callers_tenant_leaks_another_teams_run(day):
    platform, _refs, _runs = day
    leaked = lab.read_run_trusting_caller(platform, "refunds.engineer", "support-rag", "run-0001")
    assert leaked["tenant"] == "support-rag"
    with pytest.raises(Denied, match=PUBLIC_DENIAL):
        platform.read_run("refunds.engineer", "run-0001")


# --- The notebook and the theory HTML stay in step with lab.py and the theory Markdown

from shared import course_checks  # noqa: E402

HANDSON = Path(__file__).parents[1]
NOTEBOOK = HANDSON / "week-14-multi-tenant-governance-handson.ipynb"
THEORY = HANDSON.parent / "theory" / "week-14-multi-tenant-governance-theory.md"


def test_notebook_uses_the_same_code_as_lab():
    assert course_checks.notebook_drift(NOTEBOOK, HANDSON / "lab.py") == []
    assert len(course_checks.shared_definitions(NOTEBOOK, HANDSON / "lab.py")) >= 15


def test_notebook_runs_top_to_bottom_offline():
    _namespace, printed = course_checks.run_notebook(NOTEBOOK)
    assert "DENIED: budget exceeded for refunds-agent" in printed
    assert "anchor seq 46: hash differs" in printed


def test_theory_html_matches_markdown():
    assert course_checks.html_is_fresh(THEORY), "run: python3 tools/build_html.py"
