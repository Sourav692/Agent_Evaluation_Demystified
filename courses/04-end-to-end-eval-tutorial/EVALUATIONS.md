# Open-Source Agent & RAG Eval Tutorial — Evaluation Spec

2026-10-18 · Sourav Banerjee · companion to [`PLAN.md`](PLAN.md)

Every evaluation the tutorial teaches, in teaching order, with the metric, how it is computed and
the tool that runs it. The stack follows the plan's recommended picks and your notes: LangGraph
only, OpenAI models, hand-written golden set plus RAGAS-generated cases.

**Code style:** each notebook runs on its own, with no shared modules or scripts (except the CI
gate). Library calls appear directly in the cell that teaches them, and comments explain the
evaluation rather than the Python. Full rules: tracker, "Course rules".

> **Verified 2026-10-18 (P0.9).** Every class name below imports in the course venv
> (`deepeval==4.2.3`, `ragas==0.4.3`, `deepteam==1.0.10`, `ranx==0.3.21`, `langsmith==0.14.11`):
> RAGAS metrics from `ragas.metrics.collections` (async `ascore()`), DeepEval from
> `deepeval.metrics`, DeepTeam vulnerabilities from `deepteam.vulnerabilities` and attacks from
> `deepteam.attacks.single_turn` / `.multi_turn`. Names checked only by import; argument shapes
> are confirmed when each notebook is written. DeepEval 4.x `GEval` takes `SingleTurnParams`.

> **API shapes confirmed while writing notebooks 03–09 (2026-10-19).**
> - RAGAS `ragas.metrics.collections` metrics need `llm_factory(model, client=AsyncOpenAI())`
>   (a sync client raises `Cannot use agenerate() with a synchronous client`); in Jupyter use
>   `await metric.ascore(...)` in a plain loop (`abatch_score` has no concurrency cap).
> - DeepEval 4.2.3: `HallucinationMetric` is now higher-is-better; `TaskCompletionMetric(task=...)`
>   sets what "done" means (without it the judge guesses the goal); `ToolCorrectnessMetric`
>   makes no LLM call without `available_tools`; `ConversationSimulator` needs async mode in Jupyter
>   (`max_concurrent=1` when runs share the mock DB); pass `_show_indicator=False` to `measure()`
>   to keep notebook outputs clean.
> - DeepTeam 1.0.10: `red_team(..., async_mode=False)` takes a sync `model_callback(input) -> str`;
>   scores 1 = resisted, 0 = attack worked; set `DEEPTEAM_SHOW_PROGRESS=false` before import.
> - LangSmith 0.14.11: `list_runs()` / `read_run()` are deprecated; use `client.runs.query()` /
>   `client.runs.retrieve()`.

---

## Stack

| Layer | Tool |
| --- | --- |
| App under test | LangGraph supervisor: router, RAG agent, account-tools agent, escalation node |
| App model / judge model | `databricks-gpt-oss-120b` / `databricks-qwen35-122b-a10b`, both Databricks Model Serving (owner decision 2026-10-19; was `gpt-4o-mini` / `gpt-4o`). Reasoning `"none"` except the tool agent (`"low"`) |
| Embeddings + store | `text-embedding-3-small` in Chroma |
| Golden set | Hand-written stratified JSON in `data/` + RAGAS `TestsetGenerator` |
| Metrics | stdlib, `ranx`, RAGAS, DeepEval, DeepTeam |
| Traces, datasets, experiments, labels, online scoring | LangSmith (free Developer plan): LangGraph traces automatically with `LANGSMITH_TRACING=true`. Langfuse is an optional open-source track |
| Release gate | stdlib gate script in GitHub Actions; paid job on `workflow_dispatch` only |

## Evaluation map

| # | Evaluation | Scorer | Needs reference | Tool | Runs in |
| --- | --- | --- | --- | --- | --- |
| 1 | Golden set quality | Deterministic | — | stdlib | Offline |
| 2 | Retrieval, ranked | Deterministic | Relevant chunk IDs | stdlib, `ranx` | Offline, CI |
| 3 | Retrieval, judged | LLM | Optional | RAGAS, DeepEval | Offline, CI |
| 4 | Generation, reference-free | LLM | No | RAGAS, DeepEval | Offline, CI, online |
| 5 | Generation, reference-based | LLM + embedding | Reference answer | RAGAS, DeepEval `GEval` | Offline, CI |
| 6 | Retriever vs generator blame | Derived | From 2–5 | stdlib | Offline |
| 7 | Tool calls | Deterministic + LLM | Expected calls | stdlib, DeepEval | Offline, CI |
| 8 | Trajectory | Deterministic + LLM | Expected path | stdlib, DeepEval `GEval` | Offline, CI |
| 9 | Routing and handoffs | Deterministic + LLM | Expected agent | stdlib, `GEval` | Offline, CI |
| 10 | Task completion | State check + LLM | Expected end state | stdlib, DeepEval, RAGAS | Offline, CI |
| 11 | Multi-turn conversation | LLM | Scenario | DeepEval conversational metrics + simulator | Offline |
| 12 | Safety and adversarial | Attack + LLM + classifier | Policy | DeepTeam, `GEval`, OpenAI Moderation | Offline, CI |
| 13 | Custom judges | LLM | Rubric | DeepEval `GEval`, `DAGMetric` | Offline, CI |
| 14 | Judge calibration | Human vs LLM | Human labels | LangSmith annotation queues, stdlib | Offline |
| 15 | Statistics and slices | Derived | — | stdlib, `ranx` | Offline, CI |
| 16 | Cost and latency | Trace metrics | — | LangSmith | Offline, CI, online |
| 17 | Regression experiments | Comparison | Baseline run | LangSmith datasets + experiments | Offline |
| 18 | Release gate | Rules | Thresholds | stdlib, GitHub Actions | CI |
| 19 | Online evaluation | LLM + signals | No | LangSmith online evaluators | Production |

---

## 0. Test case contract

One record per case; every evaluation reads the fields it needs.

```json
{
  "id": "rag-017",
  "slice": "multi_hop",
  "input": "Can I return a sale item after 30 days?",
  "reference_answer": "No. Sale items are final after 14 days.",
  "relevant_chunk_ids": ["policy-returns-03", "policy-sale-01"],
  "expected_agent": "rag_agent",
  "expected_tool_calls": [],
  "expected_end_state": null,
  "policy_tags": ["no_refund_promise"]
}
```

Slices: `simple`, `multi_hop`, `out_of_scope`, `tool_required`, `handoff`, `adversarial`.

## 1. Golden set quality

Checks the test set before trusting any score built on it.

| Check | Rule | Tool |
| --- | --- | --- |
| Slice coverage | ≥ 20 cases per slice | stdlib `Counter` |
| Duplicates | No two inputs with embedding cosine ≥ 0.95 | `text-embedding-3-small` + stdlib |
| Label completeness | Every case has the fields its slice needs | stdlib |
| Synthetic share | RAGAS-generated cases ≤ 50% of each slice, each one reviewed | stdlib |
| Leakage | No golden input appears verbatim in prompts or few-shot examples | stdlib |

Generation: RAGAS `TestsetGenerator` over the knowledge base, with `gpt-4o` as the generator.
As built (notebook 03): `generate_with_chunks` on the 31 chunks, single-hop synthesizer on
`themes`, an extra 0.5 summary-similarity link for multi-hop, `llm_factory` clients.

## 2. Retrieval — deterministic

Did the retriever rank the labelled chunks near the top? Free, exact and repeatable.

| Metric | Definition |
| --- | --- |
| Hit rate@k | 1 if any relevant chunk is in the top k |
| Recall@k | `|relevant ∩ top_k| / |relevant|` |
| Precision@k | `|relevant ∩ top_k| / k` |
| MRR | `1 / rank of first relevant chunk`, mean over cases |
| nDCG@k | `DCG@k / IDCG@k`, `DCG = Σ rel_i / log2(i + 1)` |

Tools: each metric in plain Python first (≈5 lines), then `ranx.evaluate()` for the same numbers
and `ranx.compare()` for significance between two retrievers. Starting threshold: Recall@5 ≥ 0.80.

## 3. Retrieval — LLM-judged

Is the retrieved context relevant and sufficient, judged by the model rather than by labels.

| Metric | Question | RAGAS | DeepEval |
| --- | --- | --- | --- |
| Context precision | Are relevant chunks ranked above irrelevant ones? | `ContextPrecision` (with/without reference) | `ContextualPrecisionMetric` |
| Context recall | Does the context contain every claim of the reference? | `ContextRecall` | `ContextualRecallMetric` |
| Context relevance | How much of the context is about the question? | `ContextRelevance` | `ContextualRelevancyMetric` |

Judge: `gpt-4o`. Lesson: compare with section 2 to show where labels and judge disagree.

## 4. Generation — reference-free

Did the answer stay inside the retrieved context and address the question? These also run in
production, where no reference exists.

| Metric | Question | RAGAS | DeepEval |
| --- | --- | --- | --- |
| Faithfulness | Is every claim supported by the context? | `Faithfulness` | `FaithfulnessMetric` |
| Answer relevancy | Does the answer address the question? | `AnswerRelevancy` | `AnswerRelevancyMetric` |
| Hallucination | Does the answer contradict the context? | — | `HallucinationMetric` |

Faithfulness = `supported claims / total claims`. Starting threshold: ≥ 0.90.

## 5. Generation — reference-based

Is the answer correct against the expected answer?

| Metric | Method | Tool |
| --- | --- | --- |
| Factual correctness | Claim-level precision/recall/F1 against the reference | RAGAS `FactualCorrectness` |
| Semantic similarity | Cosine of answer and reference embeddings | RAGAS `SemanticSimilarity` + `text-embedding-3-small` |
| Answer correctness | Rubric judge: correct / partially correct / wrong | DeepEval `GEval` |
| Exact match, token F1 | For short factual answers (order IDs, dates) | stdlib |

## 6. Retriever vs generator blame

Which component caused a failed case? Derived from sections 2–5, no new model calls.

| Context recall | Faithfulness | Verdict |
| --- | --- | --- |
| Low | — | Retrieval failure |
| High | Low | Generation failure (ignored or contradicted context) |
| High | High, answer still wrong | Knowledge base or reference is wrong |

Tool: stdlib, grouped with `defaultdict` by slice.

## 7. Tool calls

Right tool, right arguments, and no call when none is needed. Tools in the app:
`lookup_order`, `issue_refund`, `create_ticket`, `search_kb`.

| Metric | Definition | Tool |
| --- | --- | --- |
| Tool selection accuracy | Called tool names = expected names | stdlib, DeepEval `ToolCorrectnessMetric` |
| Argument correctness | Arguments match expected values (exact, or normalised for dates/case) | stdlib, DeepEval `ArgumentCorrectnessMetric` |
| Schema validity | Arguments validate against the tool's JSON schema | stdlib `json` |
| Abstention | No tool call on `out_of_scope` and pure-RAG cases | stdlib |
| Tool error rate | Calls that raised or returned an error / total calls | stdlib over traces |

Alternative: RAGAS `ToolCallAccuracy` on multi-turn samples.

## 8. Trajectory

Was the sequence of steps sound, not only the final answer?

| Metric | Definition | Tool |
| --- | --- | --- |
| Strict match | Actual call sequence = expected sequence | stdlib |
| Unordered match | Same set of calls, any order | stdlib |
| Subset / superset | Actual ⊆ expected (missed steps) or ⊇ expected (extra steps) | stdlib |
| Step efficiency | `expected steps / actual steps`, capped at 1 | stdlib |
| Loop detection | Same tool + same arguments called twice in a run | stdlib |
| Trajectory quality | Judge reads the full trace: were steps necessary and well ordered? | DeepEval `GEval` |

Input: the LangGraph trace (node sequence + tool messages), exported from LangSmith with `Client().runs.query()` (`list_runs()` is deprecated in langsmith 0.14.11).

## 9. Routing and handoffs

Did the supervisor send the request to the right agent, and did context survive the handoff?

| Metric | Definition | Tool |
| --- | --- | --- |
| Routing accuracy | First agent chosen = `expected_agent` | stdlib on LangGraph state |
| Handoff count | Handoffs per case vs expected; flags ping-pong | stdlib |
| Context preservation | Facts from earlier turns present in the receiving agent's input | DeepEval `GEval` |
| Failure attribution | First node whose output failed its check | stdlib over per-node scores |
| Escalation correctness | Escalated exactly when policy requires | stdlib |

## 10. Task completion

Did the user's goal actually get done?

| Metric | Method | Tool |
| --- | --- | --- |
| End-state check | Compare mock DB state after the run to `expected_end_state` (refund row exists, ticket open) | stdlib |
| Task completion | Judge infers the goal from the trace and scores completion | DeepEval `TaskCompletionMetric` |
| Goal accuracy | Judge compares outcome to a reference goal | RAGAS `AgentGoalAccuracyWithReference` |

Lesson: the state check is ground truth; the two judges are compared against it.

## 11. Multi-turn conversation

Does the agent stay correct and consistent across a conversation?

| Metric | Question | Tool |
| --- | --- | --- |
| Knowledge retention | Does it remember facts the user gave earlier? | DeepEval `KnowledgeRetentionMetric` |
| Conversation completeness | Were all user intents in the conversation satisfied? | DeepEval `ConversationCompletenessMetric` |
| Turn relevancy | Is each reply relevant to the turns before it? | DeepEval `TurnRelevancyMetric` |
| Role adherence | Does it stay in the support-agent role? | DeepEval `RoleAdherenceMetric` |

Test data: scripted scenarios + DeepEval `ConversationSimulator` driving a simulated user with
`gpt-4o-mini`.

## 12. Safety and adversarial

What must never happen, tested by attacking the app.

| Risk | Attack / check | Tool |
| --- | --- | --- |
| Prompt injection via retrieved text | Poisoned KB chunk with instructions | DeepTeam prompt-injection attack + `GEval` |
| Jailbreak | Roleplay and multi-turn jailbreak attacks | DeepTeam |
| PII leakage | Ask for another customer's order or email | DeepTeam PII-leakage vulnerability |
| System prompt leakage | Ask the agent to reveal its instructions | DeepTeam prompt-leakage vulnerability |
| Excessive agency | Refund without verification, refund over limit | DeepTeam excessive-agency + stdlib end-state check |
| Policy violation | Promises a refund policy does not allow | `GEval` safety rubric on `gpt-4o` |
| Harmful content | Generic harm categories | OpenAI Moderation (`omni-moderation-latest`, free) |

Metrics: attack success rate per risk = `successful attacks / attempts`; critical violations
(PII, unauthorised refund) must be 0.

## 13. Custom judges

House rules no built-in metric covers: tone, policy wording, escalation phrasing.

| Pattern | Use | Tool |
| --- | --- | --- |
| Rubric judge | Criteria + evaluation steps, binary pass/fail with reason | DeepEval `GEval` |
| Decision-tree judge | Fixed branches (asked for order ID? → verified? → refunded?) | DeepEval `DAGMetric` |
| Pairwise judge | Candidate vs baseline answer, run twice with positions swapped | `GEval` + stdlib |

Rules: binary or 3-point scale, reason before verdict, judge model ≠ app model.

## 14. Judge calibration

A judge is used only after it agrees with humans.

| Step | Method | Tool |
| --- | --- | --- |
| Label | Humans give pass/fail on 50–100 sampled cases per judge | LangSmith annotation queues |
| Agreement | Cohen's kappa, TPR, TNR, confusion matrix | stdlib |
| Bias checks | Position (swap order), verbosity (pad answer), self-preference (judge = app model, i.e. gpt-oss-120b judging its own answers) | stdlib + `GEval` |
| Reference judge | `gpt-4o` scores the calibration cases beside the Qwen judge; compare each to humans and to each other | stdlib + the same metrics with a second model |
| Iterate | Fix rubric where judge and humans disagree; re-measure | — |

Kappa = `(p_o − p_e) / (1 − p_e)`. Starting bar: kappa ≥ 0.6 before a judge gates a release.

Primary judge: Qwen 3.5 on Databricks (owner decision 2026-10-19). Reference judge: `gpt-4o` on the
calibration subset only. Self-preference check: gpt-oss-120b (the app model) judging its own answers.

## 15. Statistics and slices

Is a change real, and for which slice?

| Method | Use | Tool |
| --- | --- | --- |
| Per-slice pass rate | Report every metric per slice, never one blended number | stdlib `defaultdict` |
| Bootstrap 95% CI | Resample cases 1,000 times; report the interval | stdlib `random` |
| Paired comparison | Same cases, baseline vs candidate: paired bootstrap or McNemar | stdlib |
| Retrieval significance | Paired test between two runs | `ranx.compare()` |
| Sample size | Minimum cases per slice to detect a 5-point drop | stdlib |

## 16. Cost and latency

Non-functional checks read straight from traces.

| Metric | Tool |
| --- | --- |
| Latency p50 / p95 per case and per node | LangSmith traces |
| Tokens and USD cost per case | LangSmith cost tracking |
| LLM calls per case | LangSmith traces |
| Eval run cost (judge calls) | LangSmith traces of the judge |

## 17. Regression experiments

Compare prompt, model or retriever versions on the same dataset.

| Step | Tool |
| --- | --- |
| Upload golden set as a dataset | LangSmith `client.create_dataset()` + `create_examples()` |
| Run each version as an experiment | LangSmith `evaluate()` over the LangGraph app |
| Attach scores from sections 2–13 | LangSmith feedback (`client.create_feedback()`) or `evaluate()` evaluators |
| Compare runs side by side, per slice | LangSmith experiment compare view + section 15 statistics |

## 18. Release gate

Ship or don't ship, decided by rules in CI.

| Rule | Example |
| --- | --- |
| Critical safety | 0 PII leaks, 0 unauthorised refunds |
| Slice floors | Every slice ≥ its threshold (e.g. faithfulness ≥ 0.90, tool selection ≥ 0.95) |
| No significant regression | Candidate CI not below baseline on any slice |
| Judge trust | Only judges with kappa ≥ 0.6 count toward the gate |
| Budget | Cost per case ≤ baseline × 1.2 |

Wiring: `gate` job (stdlib, free) runs on every push and reads committed scores; `evaluate` job
(paid, `OPENAI_API_KEY`) runs on `workflow_dispatch` only and skips itself without the secret.
Alternative runner: `deepeval test run`.

## 19. Online evaluation

In production there is no reference answer. Score a sample of live traces and watch for drift.

| Signal | Method | Tool |
| --- | --- | --- |
| Faithfulness, answer relevancy, safety | Reference-free judges on a 5–10% trace sample | LangSmith online evaluators (`gpt-4o`) |
| Retrieval health | Empty-retrieval rate, top-1 similarity trend | LangSmith traces |
| Outcome proxies | Escalation rate, repeat-contact rate, thumbs up/down | LangSmith feedback |
| Drift | Weekly score and slice-mix trend vs launch week (simulated dates: free-plan traces expire after 14 days) | LangSmith monitoring charts |
| Feedback loop | Failing traces → reviewed → added to the golden set | LangSmith annotation queue → dataset → `data/` |

## Optional — External benchmark

| Benchmark | Measures | Tool |
| --- | --- | --- |
| τ-bench | Tool-using customer-service tasks; pass^k reliability | τ-bench harness with `gpt-4o-mini` |
