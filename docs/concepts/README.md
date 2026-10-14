# Concepts

Theory companions. These do not repeat the notebooks' explanations — they do what a
sequential notebook can't: random access.

| Document | Companion to | Use it for |
|---|---|---|
| [`rag-agent-tool-evaluation.md`](rag-agent-tool-evaluation.md) | [course 01](../../courses/01-rag-agent-tool-evaluation/) | The taxonomy of evaluation surfaces, every check as catches / misses / when-to-use, LLM-as-judge failure modes, what each looks like on a live system, a debugging loop and a cheat sheet. Tool-agnostic — the notebooks carry the framework specifics |
| [`databricks-mlflow-evals.md`](databricks-mlflow-evals.md) | [course 02](../../courses/02-databricks-mlflow-evals/) | Five parts: **1** what TelcoAssist is (tools, data, models, trace shape, deliberate non-goals) · **2** every concept in a line or two, grouped by theme, pointing at the phase that demonstrates it · **3** 32 traps as symptom → cause → fix, led by the silent failures that look like success · **4** the numbers, thresholds and decision rules |
| [`customer-support-multi-agent-case-study.md`](customer-support-multi-agent-case-study.md) | [course 03](../../courses/03-agentic-eval-harness/) | One multi-tenant support system evaluated stage by stage — every check applied to one system, then the offline suite, the release gate, the canary and online signals |
| [`cost-tracking-and-guardrails.md`](cost-tracking-and-guardrails.md) | the case study | The same system's cost: tracking per call, agent and tenant; budgets; five guardrail boundaries; cost as a blocking release check |
