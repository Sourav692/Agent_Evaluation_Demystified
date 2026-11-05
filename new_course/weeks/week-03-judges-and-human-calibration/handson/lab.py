"""Week 3 lab: grade agent replies with a model judge and compare the grades with human labels.

Usage, from new_course/:
    python3 weeks/week-03-judges-and-human-calibration/handson/lab.py prompt case-0024
    python3 weeks/week-03-judges-and-human-calibration/handson/lab.py report
    python3 weeks/week-03-judges-and-human-calibration/handson/lab.py report --labels my_sheet.csv
    python3 weeks/week-03-judges-and-human-calibration/handson/lab.py pairwise
    python3 weeks/week-03-judges-and-human-calibration/handson/lab.py samples          # rebuild samples.jsonl
    python3 weeks/week-03-judges-and-human-calibration/handson/lab.py judge --live     # PAID: calls a real model

Everything except `judge --live` runs offline on dataset files. The judge responses in
dataset/ are mock responses written by hand in the judge's output format. They
exercise the parser and the report. They are not output from any model.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
COURSE = HERE.parents[2]
sys.path.insert(0, str(COURSE))

from shared.support_agent import load_world, run_agent  # noqa: E402

FIXTURES = HERE.parent / "dataset"
SAMPLES = FIXTURES / "samples.jsonl"
PROMPT = HERE / "judge_prompt.md"
POLICY = COURSE / "datasets" / "policies" / "refund-policy-2026-01.md"
WEEK1_CASES = COURSE / "weeks" / "week-01-evaluation-basics" / "dataset" / "cases.jsonl"
MOCK_RESPONSES = FIXTURES / "mock_judge_responses.jsonl"
EXAMPLE_LABELS = FIXTURES / "example_review_sheet.csv"
MOCK_PAIRWISE = FIXTURES / "mock_pairwise_responses.jsonl"


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def policy_text() -> str:
    """The policy without its front matter: what the judge and the reviewer read."""
    return POLICY.read_text().split("---", 2)[2].strip()


def policy_rule_ids(text: str) -> set[str]:
    return set(re.findall(r"^## (R\d+)\.", text, flags=re.MULTILINE))


# --- Samples: frozen v1 runs, so this week does not change when the agent does ---

def build_samples() -> list[dict]:
    world = load_world()
    samples = []
    for case in read_jsonl(WEEK1_CASES):
        run = run_agent(case, world)
        samples.append({
            "case_id": case["case_id"],
            "message": case["message"],
            "customer_id": case["customer_id"],
            "expected_outcome": case["expected_outcome"],
            "forbidden_actions": case["forbidden_actions"],
            **{k: v for k, v in run.to_dict().items() if k != "case_id"},
        })
    return samples


def forbidden_call(sample: dict) -> bool:
    """The Week 1 deterministic safety check, applied to a frozen sample."""
    return any(call["name"] in sample["forbidden_actions"] for call in sample["tool_calls"])


# --- The judge prompt -------------------------------------------------------------

def render_prompt(sample: dict, template: str | None = None) -> str:
    template = template or PROMPT.read_text()
    return (template.replace("{{policy}}", policy_text())
                    .replace("{{message}}", sample["message"])
                    .replace("{{reply}}", sample["final_text"]))


# --- Parsing a judgment, failing closed ---------------------------------------------

def parse_judgment(raw: str, policy: str) -> tuple[dict | None, str | None]:
    """Return (judgment, None) for a valid response or (None, reason) for an invalid one."""
    text = raw.strip()
    fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", text, flags=re.DOTALL)
    if fenced:  # models often wrap JSON in a Markdown code fence
        text = fenced.group(1)
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None, "not JSON"
    if not isinstance(data, dict):
        return None, "not a JSON object"

    verdict, score = data.get("verdict"), data.get("score")
    rule_ids, quotes = data.get("rule_ids"), data.get("quotes")
    if verdict not in ("pass", "fail"):
        return None, f"verdict {verdict!r} is not pass or fail"
    if not isinstance(score, int) or isinstance(score, bool) or not 1 <= score <= 5:
        return None, f"score {score!r} is not an integer from 1 to 5"
    if (verdict == "pass") != (score >= 3):
        return None, f"verdict {verdict} contradicts score {score}"
    if not isinstance(rule_ids, list) or not rule_ids:
        return None, "no rule_ids cited"
    unknown = sorted(set(rule_ids) - policy_rule_ids(policy))
    if unknown:
        return None, f"cites rules that do not exist: {unknown}"
    if not isinstance(quotes, list) or not quotes:
        return None, "no quotes cited"
    flat_policy = " ".join(policy.split())
    for quote in quotes:
        if not isinstance(quote, str) or " ".join(quote.split()) not in flat_policy:
            return None, f"quote not found in policy: {quote!r}"
    return {"verdict": verdict, "score": score, "rule_ids": rule_ids,
            "quotes": quotes, "reasoning": str(data.get("reasoning", ""))}, None


# --- Human labels -------------------------------------------------------------------

def load_labels(path: Path) -> dict[str, dict]:
    with path.open(newline="") as f:
        rows = list(csv.DictReader(f))
    labels = {}
    for row in rows:
        if not row["human_verdict"].strip():
            continue  # not reviewed yet
        if row["human_verdict"] not in ("pass", "fail"):
            raise ValueError(f"{row['case_id']}: human_verdict must be pass or fail")
        labels[row["case_id"]] = row
    return labels


# --- Agreement ------------------------------------------------------------------------

def agreement(pairs: list[tuple[str, str]]) -> dict:
    """Compare (human, judge) verdict pairs. Positive class: "fail", a bad reply caught."""
    n = len(pairs)
    cells = Counter(pairs)
    tp, fp = cells[("fail", "fail")], cells[("pass", "fail")]
    fn, tn = cells[("fail", "pass")], cells[("pass", "pass")]
    observed = (tp + tn) / n if n else 0.0
    human_fail, judge_fail = (tp + fn) / n if n else 0, (tp + fp) / n if n else 0
    expected = human_fail * judge_fail + (1 - human_fail) * (1 - judge_fail)
    kappa = (observed - expected) / (1 - expected) if expected < 1 else 0.0
    return {"n": n, "tp": tp, "fp": fp, "fn": fn, "tn": tn,
            "observed": observed, "expected": expected, "kappa": kappa}


def build_report(samples, responses, labels, policy) -> dict:
    judgments, invalid = {}, {}
    for r in responses:
        judgment, error = parse_judgment(r["raw"], policy)
        if judgment:
            judgments[r["case_id"]] = judgment
        else:
            invalid[r["case_id"]] = error
    reviewed = [s for s in samples if s["case_id"] in labels]
    pairs = [(labels[s["case_id"]]["human_verdict"], judgments[s["case_id"]]["verdict"])
             for s in reviewed if s["case_id"] in judgments]
    scores = [(int(labels[s["case_id"]]["human_score"]), judgments[s["case_id"]]["score"])
              for s in reviewed if s["case_id"] in judgments and labels[s["case_id"]]["human_score"]]
    return {
        "judgments": judgments,
        "invalid": invalid,
        "agreement": agreement(pairs),
        "score_exact": sum(h == j for h, j in scores) / len(scores) if scores else 0.0,
        "score_within_1": sum(abs(h - j) <= 1 for h, j in scores) / len(scores) if scores else 0.0,
        "disagreements": [s["case_id"] for s in reviewed if s["case_id"] in judgments
                          and labels[s["case_id"]]["human_verdict"] != judgments[s["case_id"]]["verdict"]],
        "label_sources": Counter(labels[s["case_id"]]["label_source"] for s in reviewed),
        "unreviewed": [s["case_id"] for s in samples if s["case_id"] not in labels],
        "judge_passed_forbidden": [s["case_id"] for s in samples if forbidden_call(s)
                                   and judgments.get(s["case_id"], {}).get("verdict") == "pass"],
    }


def print_report(report: dict, labels: dict) -> None:
    if not labels:
        print("No reviewed samples yet. Fill in human_verdict and human_score in the sheet first.")
        return
    sources = report["label_sources"]
    if set(sources) != {"human"}:
        print("LABEL STATUS: these labels are not all from human review "
              f"({dict(sources)}).\nThe agreement numbers below test the code. "
              "They are not a calibration result.\n")
    if report["unreviewed"]:
        print(f"Unreviewed samples: {len(report['unreviewed'])}\n")

    print(f"Judge responses: {len(report['judgments'])} valid, {len(report['invalid'])} invalid")
    for case_id, reason in sorted(report["invalid"].items()):
        print(f"  INVALID {case_id}: {reason}")

    a = report["agreement"]
    print(f"\nVerdicts compared on {a['n']} samples (positive = fail):")
    print(f"  both fail={a['tp']}  judge-only fail={a['fp']}  "
          f"human-only fail={a['fn']}  both pass={a['tn']}")
    print(f"  agreement={a['observed']:.3f}  chance agreement={a['expected']:.3f}  "
          f"Cohen's kappa={a['kappa']:.3f}")
    print(f"  scores: exact match {report['score_exact']:.0%}, within one point "
          f"{report['score_within_1']:.0%}")

    print("\nDisagreements:")
    for case_id in report["disagreements"]:
        j = report["judgments"][case_id]
        h = labels[case_id]
        print(f"  {case_id}  human={h['human_verdict']}/{h['human_score']}  "
              f"judge={j['verdict']}/{j['score']}  judge says: {j['reasoning']}")
        if h.get("notes"):
            print(f"  {'':<10}human note: {h['notes']}")

    print(f"\nJudge passed runs that made a forbidden tool call: {report['judge_passed_forbidden']}")


# --- Pairwise comparison ----------------------------------------------------------------

def pairwise_consistency(rows: list[dict]) -> dict[str, str]:
    """Each comparison is judged twice with the replies swapped. Keep a winner only if both agree."""
    by_pair: dict[str, dict[str, str]] = {}
    for row in rows:
        shown_first = row["order"][0]                          # "A" or "B"
        winner = shown_first if row["preferred"] == "first" else row["order"][1]
        by_pair.setdefault(row["pair_id"], {})[row["order"]] = winner
    result = {}
    for pair_id, verdicts in by_pair.items():
        winners = set(verdicts.values())
        result[pair_id] = winners.pop() if len(winners) == 1 else "position-dependent"
    return result


# --- Live judge (paid, opt-in) ------------------------------------------------------------

def judge_live(samples: list[dict], model: str, out: Path) -> None:
    """Call a real model once per sample. Costs money. Requires `openai` and OPENAI_API_KEY."""
    if not os.environ.get("OPENAI_API_KEY"):
        sys.exit("OPENAI_API_KEY is not set. The live judge is optional; the offline report does not need it.")
    from openai import OpenAI  # requirements-integrations.txt

    client = OpenAI()
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w") as f:
        for sample in samples:
            response = client.chat.completions.create(
                model=model,
                temperature=0,
                response_format={"type": "json_object"},
                messages=[{"role": "user", "content": render_prompt(sample)}],
            )
            raw = response.choices[0].message.content or ""
            f.write(json.dumps({"case_id": sample["case_id"], "raw": raw,
                                "source": f"live:{model}"}) + "\n")
            print(f"{sample['case_id']}: {raw[:80]}")
    print(f"wrote {out}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("prompt", help="print the judge prompt for one sample")
    p.add_argument("case_id")
    r = sub.add_parser("report", help="judge-versus-human disagreement report")
    r.add_argument("--labels", type=Path, default=EXAMPLE_LABELS)
    r.add_argument("--responses", type=Path, default=MOCK_RESPONSES)
    sub.add_parser("pairwise", help="position-bias check on pairwise judgments")
    sub.add_parser("samples", help="rebuild dataset/samples.jsonl from agent v1")
    j = sub.add_parser("judge", help="PAID: grade every sample with a real model")
    j.add_argument("--live", action="store_true", required=True)
    j.add_argument("--model", default="gpt-4o-mini")
    j.add_argument("--out", type=Path, default=HERE / "runs" / "live_judge_responses.jsonl")
    args = parser.parse_args()

    if args.command == "samples":
        SAMPLES.write_text("".join(json.dumps(s) + "\n" for s in build_samples()))
        print(f"wrote {SAMPLES.relative_to(COURSE)}")
        return
    samples = read_jsonl(SAMPLES)
    if args.command == "prompt":
        match = [s for s in samples if s["case_id"] == args.case_id]
        if not match:
            sys.exit(f"unknown case ID: {args.case_id}")
        print(render_prompt(match[0]))
    elif args.command == "report":
        labels = load_labels(args.labels)
        print_report(build_report(samples, read_jsonl(args.responses), labels, policy_text()), labels)
    elif args.command == "pairwise":
        for pair_id, winner in pairwise_consistency(read_jsonl(MOCK_PAIRWISE)).items():
            print(f"{pair_id}: {winner}")
    else:
        judge_live(samples, args.model, args.out)


if __name__ == "__main__":
    main()
