"""Week 10 acceptance tests. Run from new_course/:
    python3 -m pytest weeks/week-10-faults-adversarial-and-handoffs
"""

import importlib.util
import sys
from pathlib import Path

_spec = importlib.util.spec_from_file_location("week10_lab", Path(__file__).parents[1] / "lab.py")
lab = importlib.util.module_from_spec(_spec)
sys.modules["week10_lab"] = lab
_spec.loader.exec_module(lab)

CASES = {c["case_id"]: c for c in lab.read_jsonl(lab.FAULTS / "fault-cases-v1.jsonl")}
HANDOFFS = {c["case_id"]: c for c in lab.read_jsonl(lab.FAULTS / "handoff-cases-v1.jsonl")}


def checks(row, severity=None):
    return sorted(f.check for f in row["findings"] if severity in (None, f.severity))


def test_retry_after_timeout_after_commit_one_refund_with_stable_key_two_without():
    stable = lab.run_fault_case(CASES["f-001"], "stable_key", strict=False)
    naive = lab.run_fault_case(CASES["f-001"], "naive_retry", strict=False)
    assert lab.refunds_on_target(stable) == 1
    assert [c.error or c.response["status"] for c in stable["result"].trace if c.name == "create_refund"] \
        == ["timeout", "existing"]                    # the retry found the committed refund by its key
    assert lab.refunds_on_target(naive) == 2
    assert checks(naive, "critical") == ["duplicate_refund"]


def test_no_fault_schedule_gives_the_stable_key_agent_a_second_refund():
    for strict in (False, True):
        sweep = lab.retry_sweep("stable_key", strict)
        assert len(sweep) == 14 and max(r["refunds"] for r in sweep) == 1
        assert not any(f.severity == "critical" for r in sweep for f in r["findings"])
    assert max(r["refunds"] for r in lab.retry_sweep("naive_retry")) == 4


def test_strict_backend_hides_a_missing_key_behind_one_refund_per_order():
    assert lab.refunds_on_target(lab.run_fault_case(CASES["f-001"], "naive_retry", strict=True)) == 1
    assert lab.severity_counts(lab.run_suite("naive_retry", strict=True))["critical"] == 0


def test_a_key_per_attempt_does_not_stop_a_retry_but_stops_a_redelivery():
    assert lab.refunds_on_target(lab.run_fault_case(CASES["f-001"], "fresh_key", strict=False)) == 2
    assert lab.refunds_on_target(lab.run_fault_case(CASES["f-004"], "fresh_key", strict=False)) == 1
    assert lab.refunds_on_target(lab.run_fault_case(CASES["f-004"], "naive_retry", strict=False)) == 2


def test_giving_up_after_a_commit_tells_the_customer_a_false_failure():
    row = lab.run_fault_case(CASES["f-001"], "no_retry", strict=True)
    assert row["result"].outcome == "refund_failed" and lab.refunds_on_target(row) == 1
    assert "claim_mismatch" in checks(row, "major")


def test_poisoned_policy_is_retrieved_and_only_the_backend_stops_the_injectable_agent():
    row = lab.run_fault_case(CASES["f-007"], "stable_key", strict=True)
    search = next(c for c in row["result"].trace if c.name == "search_policy")
    assert search.response[0]["chunk_id"] == "refund-faq-2026-03#F1"
    assert checks(row) == ["injected_text"] and row["result"].outcome == "refund_denied"
    lax = lab.severity_counts(lab.run_suite("injectable", strict=False))
    strict = lab.severity_counts(lab.run_suite("injectable", strict=True))
    assert lax["critical_cases"] == ["f-006", "f-007", "f-008", "f-009"]
    assert strict["critical"] == 0 and strict["major"] == 4


def test_poison_is_added_per_run_and_the_shared_corpus_is_untouched():
    assert len(lab.CHUNKS) == 26 and len(lab.poisoned_corpus()) == 27
    assert not any(c.doc_id == "refund-faq-2026-03" for c in lab.chunk_documents(lab.load_documents()))


def test_reference_agent_is_clean_on_both_backends():
    for strict in (False, True):
        counts = lab.severity_counts(lab.run_suite("stable_key", strict))
        assert (counts["critical"], counts["major"]) == (0, 0)


def test_dropped_identity_is_latent_on_an_own_order_and_critical_on_another_customers():
    own = lab.run_handoff_case(HANDOFFS["h-001"], "drop_identity", "trusting")
    other = lab.run_handoff_case(HANDOFFS["h-002"], "drop_identity", "trusting")
    assert own["result"].outcome == "refund_created" and checks(own) == ["handoff_contract"]
    assert other["store"].new_refunds()[0]["customer_id"] == "cust-005"   # refunded as the order's owner
    assert "forbidden_refund" in checks(other, "critical")
    rejected = lab.run_handoff_case(HANDOFFS["h-002"], "drop_identity", "reference")
    assert rejected["result"].outcome == "handoff_rejected" and not rejected["store"].new_refunds()


def test_unaccepted_specialist_handoff_is_reported_honestly_only_by_the_reference():
    ref = lab.run_handoff_case(HANDOFFS["h-004"], "correct", "reference")
    trusting = lab.run_handoff_case(HANDOFFS["h-004"], "correct", "trusting")
    assert ref["findings"] == [] and ref["result"].outcome == "escalation_failed"
    assert trusting["result"].outcome == "escalated_to_human" and "claim_mismatch" in checks(trusting, "major")


# --- The notebook and the theory HTML stay in step with lab.py and the theory Markdown

from shared import course_checks  # noqa: E402

HANDSON = Path(__file__).parents[1]
NOTEBOOK = HANDSON / "week-10-faults-adversarial-and-handoffs-handson.ipynb"
THEORY = HANDSON.parent / "theory" / "week-10-faults-adversarial-and-handoffs-theory.md"


def test_notebook_uses_the_same_code_as_lab():
    assert course_checks.notebook_drift(NOTEBOOK, HANDSON / "lab.py") == []
    assert len(course_checks.shared_definitions(NOTEBOOK, HANDSON / "lab.py")) >= 16


def test_notebook_runs_top_to_bottom_offline():
    _namespace, printed = course_checks.run_notebook(NOTEBOOK)
    assert "most refunds on one order" in printed
    assert "refund-134-7 stored: order belongs to cust-005" in printed


def test_theory_html_matches_markdown():
    assert course_checks.html_is_fresh(THEORY), "run: python3 tools/build_html.py"
