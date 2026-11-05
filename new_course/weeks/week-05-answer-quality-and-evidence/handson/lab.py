"""Week 5 lab: check RAG answers for faithfulness, citations, correctness, relevance,
abstention and source access.

Usage, from new_course/:
    python3 weeks/week-05-answer-quality-and-evidence/handson/lab.py report               # fixed evidence
    python3 weeks/week-05-answer-quality-and-evidence/handson/lab.py report --retrieval filtered
    python3 weeks/week-05-answer-quality-and-evidence/handson/lab.py case a-009
    python3 weeks/week-05-answer-quality-and-evidence/handson/lab.py ragas --live          # PAID: model-judged

`report` and `case` are local and deterministic. `ragas --live` calls a model judge and
prints its scores in separate, labeled columns, never mixed with the local checks.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
COURSE = HERE.parents[2]
sys.path.insert(0, str(COURSE))

from shared.answerer import Answer, answer_v1  # noqa: E402
from shared.retrieval import Chunk, Retriever, chunk_documents, load_documents  # noqa: E402

CASES = COURSE / "datasets" / "answers" / "answer-cases-v1.jsonl"
CHECK_SEVERITY = {
    "faithfulness": "major", "citation_support": "major", "correctness": "major",
    "relevance": "minor", "abstention": "major", "stale_source": "major", "restricted_source": "critical",
}


@dataclass
class CheckResult:
    check: str
    passed: bool
    reason: str

    @property
    def severity(self) -> str:
        return CHECK_SEVERITY[self.check]


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def norm(text: str) -> str:
    return " ".join(text.lower().split())


# --- The checks ------------------------------------------------------------------
# Each takes the case, the chunks the writer received and the answer.

def check_faithfulness(case: dict, chunks: list[Chunk], answer: Answer) -> CheckResult:
    """Every answer sentence must appear in some chunk the writer was given."""
    evidence = " ".join(norm(c.text) for c in chunks)
    unsupported = [s for s, _cid in answer.sentences if norm(s) not in evidence]
    if answer.abstained:
        return CheckResult("faithfulness", True, "abstained: nothing to support")
    reason = "every sentence is in the evidence" if not unsupported else f"unsupported: {unsupported}"
    return CheckResult("faithfulness", not unsupported, reason)


def check_citation_support(case: dict, chunks: list[Chunk], answer: Answer) -> CheckResult:
    """Each sentence's cited chunk must itself contain the sentence."""
    by_id = {c.chunk_id: c for c in chunks}
    wrong = [cid for s, cid in answer.sentences
             if cid is None or cid not in by_id or norm(s) not in norm(by_id[cid].text)]
    reason = "every citation supports its sentence" if not wrong else f"citations that do not support: {wrong}"
    return CheckResult("citation_support", not wrong, reason)


def check_correctness(case: dict, chunks: list[Chunk], answer: Answer) -> CheckResult:
    """The answer states the required facts and none of the forbidden ones.

    Required facts apply only when the case expects an answer. Forbidden facts apply
    always: an abstain case can still leak a fact it must not state.
    """
    text = norm(answer.text)
    required = case["must_include"] if case["expected_behavior"] == "answer" else []
    missing = [f for f in required if norm(f) not in text]
    present = [f for f in case["must_not_include"] if norm(f) in text]
    ok = not missing and not present
    reason = "required facts present" if ok else f"missing {missing}, forbidden {present}"
    return CheckResult("correctness", ok, reason)


def check_relevance(case: dict, chunks: list[Chunk], answer: Answer) -> CheckResult:
    """The answer draws on at least one section that answers the question."""
    if case["expected_behavior"] == "abstain":
        return CheckResult("relevance", True, "abstain case: no gold section")
    cited_sections = set(answer.citations())
    ok = bool(cited_sections & set(case["gold_sections"]))
    return CheckResult("relevance", ok, "cites a gold section" if ok else f"cites none of {case['gold_sections']}")


def check_abstention(case: dict, chunks: list[Chunk], answer: Answer) -> CheckResult:
    """Abstain exactly when the case says the evidence cannot support an answer."""
    want = case["expected_behavior"] == "abstain"
    ok = answer.abstained == want
    reason = ("abstained as expected" if ok and want else "answered as expected" if ok
              else "answered when it should abstain" if want else "abstained when it should answer")
    return CheckResult("abstention", ok, reason)


def check_stale_source(case: dict, chunks: list[Chunk], answer: Answer) -> CheckResult:
    """No sentence may be cited to a superseded policy."""
    by_id = {c.chunk_id: c for c in chunks}
    stale = [cid for cid in answer.citations() if cid in by_id and by_id[cid].status != "current"]
    return CheckResult("stale_source", not stale, "no superseded sources" if not stale else f"cites superseded {stale}")


def check_restricted_source(case: dict, chunks: list[Chunk], answer: Answer) -> CheckResult:
    """No sentence may come from an internal document. This is the access check."""
    by_id = {c.chunk_id: c for c in chunks}
    leaked = [cid for cid in answer.citations() if cid in by_id and by_id[cid].audience != "public"]
    return CheckResult("restricted_source", not leaked,
                       "no internal sources" if not leaked else f"quotes internal {leaked}")


CHECKS = [check_faithfulness, check_citation_support, check_correctness, check_relevance,
          check_abstention, check_stale_source, check_restricted_source]


# --- Runner --------------------------------------------------------------------------

def evidence_for(case: dict, by_id: dict[str, Chunk], retriever: Retriever | None) -> list[Chunk]:
    """The fixed evidence from the case, or a fresh filtered hybrid search."""
    if retriever is None:
        return [by_id[cid] for cid in case["retrieved"]]
    return retriever.search(case["question"], 3, filtered=True)


def run_cases(writer=answer_v1, retrieval: str = "fixed", cases: list[dict] | None = None) -> list[dict]:
    cases = cases or read_jsonl(CASES)
    chunks = chunk_documents(load_documents())
    by_id = {c.chunk_id: c for c in chunks}
    retriever = Retriever(chunks, "hybrid") if retrieval == "filtered" else None
    rows = []
    for case in cases:
        evidence = evidence_for(case, by_id, retriever)
        answer = writer(case["question"], evidence)
        results = [check(case, evidence, answer) for check in CHECKS]
        rows.append({"case": case, "evidence": evidence, "answer": answer, "results": results})
    return rows


def print_report(rows: list[dict], title: str) -> None:
    print(title)
    names = [c.__name__.removeprefix("check_") for c in CHECKS]
    short = {"faithfulness": "faith", "citation_support": "cite", "correctness": "correct",
             "relevance": "relev", "abstention": "abstain", "stale_source": "stale",
             "restricted_source": "restrict"}
    print(f"{'slice (cases)':<20}" + "".join(f"{short[n]:>9}" for n in names) + f"{'all':>7}")
    groups: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        groups[r["case"]["slice"]].append(r)
    for name, group in [*groups.items(), ("overall", rows)]:
        cells = "".join(f"{sum(x['results'][i].passed for x in group):>6}/{len(group):<2}" for i in range(len(names)))
        all_ok = sum(all(res.passed for res in x["results"]) for x in group)
        print(f"{name + f' ({len(group)})':<20}{cells}{all_ok:>4}/{len(group)}")
    critical = [r["case"]["case_id"] for r in rows
                if any(not res.passed and res.severity == "critical" for res in r["results"])]
    faithful_but_wrong = [r["case"]["case_id"] for r in rows
                          if r["results"][0].passed and not r["results"][2].passed]
    print(f"\nCritical failures (internal text in an answer): {critical}")
    print(f"Faithful to the evidence but incorrect: {faithful_but_wrong}")


def print_case(case_id: str, retrieval: str) -> None:
    rows = [r for r in run_cases(retrieval=retrieval) if r["case"]["case_id"] == case_id]
    if not rows:
        sys.exit(f"unknown case ID: {case_id}")
    r = rows[0]
    print(f"{case_id} ({r['case']['slice']}): {r['case']['question']}")
    print(f"evidence: {[c.chunk_id for c in r['evidence']]}")
    for s, cid in r["answer"].sentences:
        print(f"  answer: {s}  [{cid}]")
    print(f"reference: {r['case']['reference_answer']}")
    for res in r["results"]:
        print(f"  {'PASS' if res.passed else 'FAIL'}  {res.check:<18} [{res.severity}] {res.reason}")


# --- Optional: Ragas, model-judged (paid) --------------------------------------------------

def ragas_live(model: str = "gpt-4o-mini") -> None:
    """Score the same answers with Ragas 0.4.3. Needs requirements-integrations.txt and OPENAI_API_KEY.

    Four metrics per case: about 24 x 4 judge calls plus embeddings for answer relevancy.
    """
    import asyncio
    import os
    if not os.environ.get("OPENAI_API_KEY"):
        sys.exit("OPENAI_API_KEY is not set. ragas --live is optional; `report` runs offline.")
    from openai import AsyncOpenAI
    from ragas.embeddings import OpenAIEmbeddings
    from ragas.llms.base import llm_factory
    from ragas.metrics.collections import AnswerRelevancy, ContextPrecision, ContextRecall, Faithfulness

    client = AsyncOpenAI()
    judge = llm_factory(model, client=client)
    metrics = {
        "faithfulness": Faithfulness(llm=judge),
        "answer_relevancy": AnswerRelevancy(llm=judge, embeddings=OpenAIEmbeddings(
            client=client, model="text-embedding-3-small")),
        "context_precision": ContextPrecision(llm=judge),
        "context_recall": ContextRecall(llm=judge),
    }

    async def score(row: dict) -> dict:
        case, contexts = row["case"], [c.text for c in row["evidence"]]
        q, a, ref = case["question"], row["answer"].text, case["reference_answer"]
        return {
            "faithfulness": (await metrics["faithfulness"].ascore(
                user_input=q, response=a, retrieved_contexts=contexts)).value,
            "answer_relevancy": (await metrics["answer_relevancy"].ascore(user_input=q, response=a)).value,
            "context_precision": (await metrics["context_precision"].ascore(
                user_input=q, reference=ref, retrieved_contexts=contexts)).value,
            "context_recall": (await metrics["context_recall"].ascore(
                user_input=q, retrieved_contexts=contexts, reference=ref)).value,
        }

    rows = run_cases()
    print(f"{'case':<7}{'slice':<14}{'local: faith':>13}{'local: correct':>15}"
          f"{'ragas: faith':>13}{'ragas: relev':>13}{'ragas: ctx P':>13}{'ragas: ctx R':>13}")
    for row in rows:
        s = asyncio.run(score(row))
        local = row["results"]
        print(f"{row['case']['case_id']:<7}{row['case']['slice']:<14}"
              f"{'pass' if local[0].passed else 'FAIL':>13}{'pass' if local[2].passed else 'FAIL':>15}"
              f"{s['faithfulness']:>13.2f}{s['answer_relevancy']:>13.2f}"
              f"{s['context_precision']:>13.2f}{s['context_recall']:>13.2f}")
    print(f"\nRagas columns are model-judged by {model} and vary between runs. Local columns are deterministic.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    r = sub.add_parser("report", help="all checks, by slice")
    r.add_argument("--retrieval", choices=["fixed", "filtered"], default="fixed")
    c = sub.add_parser("case", help="one case in full")
    c.add_argument("case_id")
    c.add_argument("--retrieval", choices=["fixed", "filtered"], default="fixed")
    g = sub.add_parser("ragas", help="PAID: Ragas model-judged scores beside the local checks")
    g.add_argument("--live", action="store_true", required=True)
    g.add_argument("--model", default="gpt-4o-mini")
    args = parser.parse_args()
    if args.command == "report":
        label = ("fixed evidence from each case" if args.retrieval == "fixed"
                 else "evidence from a filtered hybrid search, top 3")
        print_report(run_cases(retrieval=args.retrieval), f"Writer v1, {label}:")
    elif args.command == "case":
        print_case(args.case_id, args.retrieval)
    else:
        ragas_live(args.model)


if __name__ == "__main__":
    main()
