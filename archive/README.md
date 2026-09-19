# archive

Superseded material. Kept because it records how the courses were built, not because
anything here should be read first. Nothing in `courses/`, `labs/` or `docs/` depends on it.

| File | Why it is here |
|---|---|
| `Agent_RAG_Tools_Evaluation_MASTER.ipynb` | A straight concatenation of `evaluation.ipynb` and the two fullest `langgraph-agent-rag-eval` notebooks, with dividers added and nothing condensed. Superseded by `courses/01-rag-agent-tool-evaluation/`, which covers the same ground as a designed sequence. |
| `TUTORIAL_PLAN.md` | The build plan and design rationale for course 01 — what each module was built from, what was condensed and why, and the API-drift and dependency traps hit along the way. Still the best explanation of *why* course 01 is shaped the way it is. |
| `Evaluation_and_Eval_Harnesses_README.md` | The index of the old flat `Evaluation_and_Eval_Harnesses/` folder, before it was split into `courses/` and `labs/`. |
| `rag_agent_eval_langgraph_openai_copy.ipynb` | An untracked-scratch copy that got committed. Differs from the original; kept rather than guessed at. |
| `Evaluation_Questions_for_Agentic_System_Design.md` | The 35 interview questions, before they were merged with the 19 case studies into `docs/interview-prep/QUESTION_BANK.md`. Text carried over whole; only the front matter was rewritten. |
| `Agentic_AI_Evaluation_Decomposition_Case_Studies.md` | The 19 case studies plus the Decomposition Spine, taxonomy and four appendices, before the same merge. Text carried over whole. |
| `Agentic_AI_Evaluation_Decomposition_Case_Studies.html` | A styled render of the file above. Superseded by `docs/interview-prep/evaluation-round-drill.html`, which carries the same cases interactively. |
| `rag-agent-tool-evaluation-THEORY_GUIDE.md` | A theory companion for course 01 that lived inside the course folder. About three quarters of its prose is already in `docs/concepts/rag-agent-tool-evaluation.md`, which is the designated companion and is indexed as such; what it had on top was DeepEval and RAGAS class names, which the course's own notebooks carry. Its header also described a 14-notebook course — course 01 has 15. |
| `labs-companion-00-evaluation-index.md` | The written index for `docs/interactive-labs/`. Its unique parts — the *what breaks where* triage table and the lab↔notebook mapping — moved to `docs/concepts/rag-agent-tool-evaluation.md` §0.1b and `docs/interactive-labs/README.md`; the rest restated the field guide's Part 0. |
| `labs-companion-01-…` through `-05-…` (5 files) | The prose companions to interactive labs 01–05. Nothing linked to them. Their narratives are now Part 6 of `docs/concepts/rag-agent-tool-evaluation.md`; their 25 interview questions are Part 10 of `docs/interview-prep/QUESTION_BANK.md`. Kept because the merge reordered and re-levelled headings. |
| `rag-agent-tool-evaluation-30pp.pdf` | The later of two tutorial PDF exports (30pp, Chrome print, 4.1MB) — previously the live one at `docs/interactive-labs/`. A derived artifact: everything in it is in the HTML labs and the field guide. |
| `AI_Engineer_Interview_Kit_RAG_Agents_Production_Failure_Scenarios_FINAL.pdf` | A 66-page Word-authored interview kit. Unique content, but nothing in the repo ever linked to it and it cannot be merged into the Markdown. Archived rather than left unreferenced in `docs/`. |
| `databricks-mlflow-evals-README.md` | The index for the old `docs/concepts/databricks-mlflow-evals/` folder, before its four documents were merged into the single `docs/concepts/databricks-mlflow-evals.md`. Its rationale for why the folder exists is now that file's header. |
| `databricks-mlflow-evals-AGENT_UNDER_TEST.md` | TelcoAssist, the agent course 02 evaluates. Now Part 1 of `docs/concepts/databricks-mlflow-evals.md`. |
| `databricks-mlflow-evals-CONCEPTS.md` | The concept map plus its two appendices. Now Part 2 of the same file. |
| `databricks-mlflow-evals-GOTCHAS.md` | The 32 traps. Now Part 3. |
| `databricks-mlflow-evals-QUICK_REFERENCE.md` | The numbers and decision rules. Now Part 4. |
| `ragas_RAG_copy.py` | Same — a `RAG copy.py` scratch file from `labs/rag-evaluation/ragas-scripts/`. |
| `openai-evaluation-guide-plain-english.md` | A prose explainer of OpenAI's evaluation guide, written 2026-09-20 and folded into `docs/guide-audits/openai-eval-guide-tutorial.md` the same day. It covered the same nine concepts against the same notebooks, in the same order, and cited **no notebook the tutorial did not already cite** — so it was a second rendering rather than a second audience. Its distinctive parts moved across whole: the `ACC-99231` running example, the v1-vs-v2 regression table, the code/judge/human cost table, the wine-judge analogy, and the five one-line mistakes. |
| `rag-agent-tools-eval-tutorial-2026-09-14-0156.pdf` | The earlier of two near-identical tutorial PDF exports (32pp). Both exports now live here — see `rag-agent-tool-evaluation-30pp.pdf` for the later one. Neither is authoritative; the HTML labs and the field guide are. |

Paths quoted inside `TUTORIAL_PLAN.md` were updated to the current layout, but the
document describes a repository state that no longer exists — read it as history.
