"""Week 13 acceptance tests. Run from new_course/:
    python3 -m pytest weeks/week-13-tracing-and-online-evaluation
"""

import importlib.util
import json
import re
import sys
from pathlib import Path

_spec = importlib.util.spec_from_file_location("week13_lab", Path(__file__).parents[1] / "lab.py")
lab = importlib.util.module_from_spec(_spec)
sys.modules["week13_lab"] = lab
_spec.loader.exec_module(lab)

from shared import tracing  # noqa: E402

RUN = lab.replay(True)


def row(request_id):
    return lab.find_row(RUN, request_id)


def test_ids_follow_w3c_trace_context_and_traceparent_round_trips():
    tracer = tracing.Tracer(seed=1)
    with tracer.span("outer", "AGENT") as outer:
        with tracer.span("inner", "TOOL") as inner:
            pass
    assert re.fullmatch(r"[0-9a-f]{32}", outer.trace_id) and re.fullmatch(r"[0-9a-f]{16}", outer.span_id)
    assert (inner.trace_id, inner.parent_id) == (outer.trace_id, outer.span_id)
    header = tracing.traceparent(inner)
    assert tracing.parse_traceparent(header) == (inner.trace_id, inner.span_id, True)
    with tracer.span("remote child", "TOOL", parent=tracing.parse_traceparent(header)[:2]) as remote:
        pass
    assert (remote.trace_id, remote.parent_id) == (inner.trace_id, inner.span_id)
    for bad in ("00-" + "0" * 32 + "-" + "1" * 16 + "-01", "01-abc-def-01"):
        try:
            tracing.parse_traceparent(bad)
            raise AssertionError(f"accepted {bad}")
        except ValueError:
            pass


def test_one_request_is_one_tree_of_openinference_spans_with_simulated_durations():
    r = row("r-3211")
    names = [(s.name, s.kind, s.status) for s in r["spans"]]
    assert names == [("support_request", "AGENT", "OK"), ("get_order", "TOOL", "OK"), ("search_policy", "TOOL", "OK"),
                     ("retrieve", "RETRIEVER", "OK"), ("create_refund", "TOOL", "ERROR"),
                     ("create_refund", "TOOL", "OK"), ("compose_reply", "LLM", "OK")]
    root, by_name = r["spans"][0], {s.name: s for s in r["spans"]}
    assert all(s.trace_id == root.trace_id for s in r["spans"])
    assert by_name["retrieve"].parent_id == by_name["search_policy"].span_id
    assert by_name["compose_reply"].attributes[tracing.LLM_MODEL_NAME] == tracing.STAND_IN_MODEL
    assert by_name["retrieve"].attributes["retrieval.documents.0.document.id"] == "refund-policy-2026-01#R3"
    assert root.end_ms - root.start_ms == 6010            # 40 + 30 + 90 + 5000 + 250 + 600, all SIMULATED


def test_traffic_and_traces_are_reproducible_from_the_seed():
    traffic = lab.build_traffic()
    assert len(traffic) == 5600 and traffic == lab.build_traffic()
    assert traffic[0]["message"] == "My order #123 arrived damaged. Can I get a refund?"
    again = lab.run_request(traffic[0], "v2.2", tracing.Tracer(seed=lab.CONFIG["seed"]))
    assert again["trace_id"] == RUN["rows"][0]["trace_id"]


def test_online_checks_need_no_reference_and_catch_a_false_failure():
    assert row("r-3211")["checks"]["refund_failure"] is False                # the retry recovered
    failed = row("r-3372")["checks"]                                         # v2.3, no retry
    assert failed["refund_failure"] and not failed["claim_mismatch"]
    lie = row("r-1528")                                                      # v2.2, two timeouts
    assert lie["outcome"] == "refund_failed" and [r["refund_id"] for r in lie["ledger"]] == ["refund-210-7"]
    assert lie["checks"]["claim_mismatch"]


def test_the_deploy_is_detected_and_rolled_back_and_the_counterfactual_is_worse():
    assert [(lab.hour_label(h), kind) for h, kind, _ in RUN["log"]] == [
        ("day 9 10:00", "deploy"), ("day 9 16:00", "rollback decided"), ("day 9 16:00", "rollback")]
    assert lab.incident_summary(RUN) == {"deploy_hour": 202, "detect_hours": 5, "mitigate_hours": 6,
                                         "requests_on_bad_version": 113, "refund_failures": 3, "claim_mismatches": 0}
    never = lab.incident_summary(lab.replay(False))
    assert (never["mitigate_hours"], never["requests_on_bad_version"], never["refund_failures"],
            never["claim_mismatches"]) == (None, 2229, 64, 31)


def test_no_refund_page_before_the_deploy_and_drift_alerts_only_around_the_sale():
    fired = [(e["alert"], e["fired"]) for e in RUN["events"]]
    assert all(h >= 202 for a, h in fired if a == "refund_failure_rate_high")
    drift_and_feedback = [h for a, h in fired if a in ("input_drift", "thumbs_down_rate_high")]
    assert drift_and_feedback and all(3 * 24 <= h <= 7 * 24 for h in drift_and_feedback)
    days = lab.daily_rows(RUN)
    assert all(d["failure_rate"] < 0.02 for d in days[3:6])                  # the sale moved feedback, not failures


def test_head_sampling_misses_failures_and_tail_sampling_keeps_them():
    report = {r["sampler"]: r for r in lab.sampling_report(RUN)}
    assert report["head 5%"]["failures"] == 8 and report["head 5%"]["failures_kept"] == 0
    assert report["tail + head 5%"]["failures_kept"] == 8
    assert report["head 5%"]["traces"] == 299 and report["tail + head 5%"]["traces"] == 898
    kept_1 = {r["trace_id"] for r in RUN["rows"] if tracing.head_sampled(r["trace_id"], 0.01)}
    kept_5 = {r["trace_id"] for r in RUN["rows"] if tracing.head_sampled(r["trace_id"], 0.05)}
    assert kept_1 <= kept_5                                                  # a ratio sampler nests
    assert lab.alert_on_sample(RUN, 0.05) == []                              # too little volume to ever fire


def test_export_redacts_names_emails_card_numbers_and_customer_ids():
    patterns_only = lab.leaks([s for r in RUN["rows"] for s in lab.export_trace(r, identity_aware=False)])
    exported = [s for r in RUN["rows"] for s in lab.export_trace(r)]
    assert patterns_only["name"] == 1619 and sum(lab.leaks(exported).values()) == 0
    text = json.dumps(exported)
    for customer in lab.WORLD["customers"].values():
        assert customer["name"] not in text and lab.email_for(customer["name"]) not in text
    assert not any(card in text for card in lab.TEST_CARDS)


def test_dashboard_links_every_alert_to_an_exported_trace(tmp_path):
    page = lab.write_dashboard(RUN, tmp_path).read_text()
    links = re.findall(r"href='(traces/[0-9a-f]{32}\.json)'", page)
    assert links and len(links) == sum(len(e["examples"]) for e in RUN["events"])
    for link in links:
        spans = json.loads((tmp_path / link).read_text())
        assert spans[0]["kind"] == "AGENT" and "cust-" not in json.dumps(spans)
    assert "SIMULATED" in page


def test_optional_opentelemetry_export_matches_or_reports_missing():
    exported = [s for r in RUN["rows"][:5] for s in lab.export_trace(r)]
    finished = lab.otel_export(exported)
    if finished is None:                                                     # the core install has no SDK
        return
    assert len(finished) == len(exported) and lab.otel_matches(exported, finished) == []


# --- The notebook and the theory HTML stay in step with lab.py and the theory Markdown

from shared import course_checks  # noqa: E402

HANDSON = Path(__file__).parents[1]
NOTEBOOK = HANDSON / "week-13-tracing-and-online-evaluation-handson.ipynb"
THEORY = HANDSON.parent / "theory" / "week-13-tracing-and-online-evaluation-theory.md"


def test_notebook_uses_the_same_code_as_lab():
    assert course_checks.notebook_drift(NOTEBOOK, HANDSON / "lab.py") == []
    assert len(course_checks.shared_definitions(NOTEBOOK, HANDSON / "lab.py")) >= 20


def test_notebook_runs_top_to_bottom_offline():
    _namespace, printed = course_checks.run_notebook(NOTEBOOK)
    assert "detected after 5 h, rolled back after 6 h" in printed
    assert "tail + head 5%" in printed and "8 of 8" in printed


def test_theory_html_matches_markdown():
    assert course_checks.html_is_fresh(THEORY), "run: python3 tools/build_html.py"
