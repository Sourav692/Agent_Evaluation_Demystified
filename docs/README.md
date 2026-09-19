# docs

Prose. Nothing here executes.

| Folder | What it is |
|---|---|
| [`concepts/`](concepts/) | Theory companions to both courses — definitions, gotchas, quick-reference tables. Written for random access, not sequential reading. |
| [`interactive-labs/`](interactive-labs/) | Six standalone HTML labs you can open in a browser and manipulate. Built from course 01's notebooks; the written companions are Part 6 of the field guide. Start at [`README.md`](interactive-labs/README.md). |
| [`interview-prep/`](interview-prep/) | Evaluation questions for agentic system-design rounds and 19 decomposition case studies — plus a [self-quiz drill](interview-prep/evaluation-round-drill.html), standalone HTML. |
| [`study-guide/`](study-guide/) | The staged [study plan](study-guide/evaluation-study-plan.html) through the interview-prep question bank — seven stages with time estimates, a 2–3 day fast path, a skip list and a readiness check. Standalone HTML. |

Two standalone audits sit outside those folders, each mapping this repo against an external
evaluation guide:

- [`openai-eval-guide-coverage-gaps.md`](openai-eval-guide-coverage-gaps.md) — against
  OpenAI's *Evaluation best practices*. Every topic mapped to the notebook that teaches it,
  badged ✅ / 🟡 / ⏭️ / ❌ and verified per course, plus the gap list, the three claims in
  course 02's own map that have drifted, and the terminology the guide names differently.
- [`genai-eval-playbook-coverage-map.md`](genai-eval-playbook-coverage-map.md) — against *LLM
  Evaluation for GenAI Forward Deployed Engineers*, a customer-facing playbook. All 20 sections
  mapped, then thirteen open gaps grouped into commercial apparatus, retrieval operations and
  measurement details.
- [`openai-eval-guide-tutorial.md`](openai-eval-guide-tutorial.md) — the teaching companion to
  the first audit. The same guide in plain language, 3–4 lines per concept, each with the
  notebook that teaches it and a TODO that asks you to produce something. 21 TODOs; the file
  is its own progress tracker.

## concepts/

- [`rag-agent-tool-evaluation.md`](concepts/rag-agent-tool-evaluation.md) — the field
  guide to course 01: the taxonomy, a what-breaks-where triage table, every check as
  what-it-catches / what-it-misses / when-to-reach-for-it, LLM-as-judge failure modes, what
  each check looks like on a live system, a debugging loop, a one-page cheat sheet, and
  **Part 6**, the worked narrative behind each of the six interactive labs. Tool-agnostic —
  no framework APIs, no code, nothing to run.
- [`databricks-mlflow-evals.md`](concepts/databricks-mlflow-evals.md) — the companion to
  course 02, in four parts: the agent under test, concepts by theme, 32 gotchas as
  symptom → cause → fix, and the numbers and decision rules in one sitting.
- [`online_vs_offline_evaluation.md`](concepts/online_vs_offline_evaluation.md) — the two
  regimes side by side: what offline catches that online cannot and the reverse, what flows
  between them, and the sampling-resolution argument — why a 5% sample cannot see a
  two-point regression, and when the answer is to move the comparison offline rather than
  sample harder. §5.1 is the same argument in plain English.
- [`openai-evaluation-guide-plain-english.md`](concepts/openai-evaluation-guide-plain-english.md)
  — OpenAI's evaluation-best-practices guide in plain language, with one example running all
  the way through: a phone-company support bot. The five steps, where checks go for each
  agent shape, code vs. judge vs. human, the two judge biases, edge cases by kind, and what
  still works in production. Every section links to the notebook that implements it.
