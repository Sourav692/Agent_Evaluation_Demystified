"""Week 9 acceptance tests. Run from new_course/:
    python3 -m pytest weeks/week-09-multi-turn-state
"""

import importlib.util
import sys
from pathlib import Path

import pytest

_spec = importlib.util.spec_from_file_location("week09_lab", Path(__file__).parents[1] / "lab.py")
lab = importlib.util.module_from_spec(_spec)
sys.modules["week09_lab"] = lab
_spec.loader.exec_module(lab)

from shared.session_agent import SessionAgentV2, SessionStore  # noqa: E402

SCENARIOS = lab.read_jsonl(lab.SCENARIO_FILE)
V1, V2 = lab.run_suite("v1"), lab.run_suite("v2")


def by_id(rows):
    return {r["id"]: r for r in rows}


def test_dataset_has_25_scenarios_in_five_slices_with_restart_points():
    assert len(SCENARIOS) == 25 and len({s["scenario_id"] for s in SCENARIOS}) == 25
    assert {s["slice"] for s in SCENARIOS} == set(lab.SLICES)
    assert sum(t["restart_before"] for s in SCENARIOS for t in s["turns"]) == 10
    assert sum(len(s["turns"]) for s in SCENARIOS) == 86


def test_reference_agent_passes_every_scenario_and_v1_fails_13():
    assert sum(r["passed"] for r in V2) == 25
    failed = sorted(r["id"] for r in V1 if not r["passed"])
    assert failed == ["conv-01", "conv-03", "conv-04", "conv-07", "conv-08", "conv-13", "conv-14",
                      "conv-15", "conv-16", "conv-17", "conv-20", "conv-22", "conv-25"]


def test_restart_loses_v1_order_but_not_v2():
    v1, v2 = by_id(V1)["conv-01"]["run"], by_id(V2)["conv-01"]["run"]
    assert v1["agents_built"] == v2["agents_built"] == 2
    assert v1["turns"][1]["outcome"] == "no_action" and v1["refunds"] == []
    assert v2["turns"][1]["outcome"] == "refund_created"
    assert v2["refunds"] == [{"order_id": "ord-123", "amount": 64.0}]


def test_clarification_answer_is_bound_to_the_question():
    v1, v2 = by_id(V1)["conv-08"]["run"], by_id(V2)["conv-08"]["run"]
    assert v1["refunds"] == [{"order_id": "ord-201", "amount": 58.0}]       # v1 took the first candidate
    assert v2["refunds"] == [{"order_id": "ord-217", "amount": 110.0}]      # "The second one."


def test_v1_loses_the_order_after_three_digressions():
    results = by_id(V1)
    assert results["conv-11"]["passed"] and results["conv-12"]["passed"]     # 1 and 2 questions
    assert not results["conv-13"]["passed"]                                  # 3 questions
    assert results["conv-13"]["run"]["turns"][-1]["outcome"] == "clarification_requested"


def test_shared_session_id_leaks_an_order_and_a_lax_backend_refunds_it():
    isolation = {c.check: c for c in by_id(V1)["conv-16"]["results"]}
    assert not isolation["tenant_isolation"].passed and isolation["ledger"].passed   # strict backend blocked it
    lax = by_id(lab.run_suite("v1", strict=False))["conv-16"]
    assert lax["run"]["refunds"] == [{"order_id": "ord-123", "amount": 64.0}]       # cust-025 refunded cust-001's order
    assert all(r["passed"] for r in V2 if r["slice"] == "isolation")


def test_restart_invariance_separates_durable_state_from_memory():
    assert all(r["same"] for r in lab.invariance("v2"))
    assert not any(r["same"] for r in lab.invariance("v1"))


def test_state_checks_survive_rewording_and_exact_text_does_not():
    assert lab.compare_checkers("v2", lab.REPLIES) == {"exact_text": 25, "state_checks": 25, "n": 25}
    assert lab.compare_checkers("v2", lab.REWORDED_REPLIES) == {"exact_text": 0, "state_checks": 25, "n": 25}
    golden = lab.load_golden()
    conv22 = by_id(V1)["conv-22"]
    assert lab.check_exact_text(conv22["run"], golden) and not conv22["passed"]   # same words, order forgotten


def test_harness_refuses_scenarios_without_restart_flags():
    broken = [{**s, "turns": [{k: v for k, v in t.items() if k != "restart_before"} for t in s["turns"]]}
              for s in SCENARIOS]
    with pytest.raises(ValueError, match="restart_before"):
        lab.run_suite("v1", scenarios=broken)


def test_checkpoint_survives_a_reopened_store(tmp_path):
    path = str(tmp_path / "cp.sqlite")
    store = SessionStore(path)
    store.save("cust-001", "web-1", {"order_id": "ord-123"})
    store.close()
    reopened = SessionStore(path)
    assert reopened.load("cust-001", "web-1") == {"order_id": "ord-123"}
    assert reopened.load("cust-025", "web-1") is None                        # same session ID, other customer
    assert isinstance(SessionAgentV2(lab.WORLD, None, path).checkpoints, SessionStore)


# --- The notebook and the theory HTML stay in step with lab.py and the theory Markdown

from shared import course_checks  # noqa: E402

HANDSON = Path(__file__).parents[1]
NOTEBOOK = HANDSON / "week-09-multi-turn-state-handson.ipynb"
THEORY = HANDSON.parent / "theory" / "week-09-multi-turn-state-theory.md"


def test_notebook_uses_the_same_code_as_lab():
    assert course_checks.notebook_drift(NOTEBOOK, HANDSON / "lab.py") == []
    assert len(course_checks.shared_definitions(NOTEBOOK, HANDSON / "lab.py")) >= 18


def test_notebook_runs_top_to_bottom_offline():
    _namespace, printed = course_checks.run_notebook(NOTEBOOK)
    assert "Session agent v1, strict backend: 12/25 scenarios pass" in printed
    assert "conv-19: turn 3: no_action, expected refund_created" in printed


def test_theory_html_matches_markdown():
    assert course_checks.html_is_fresh(THEORY), "run: python3 tools/build_html.py"
