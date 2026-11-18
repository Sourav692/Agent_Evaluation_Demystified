# Open-Source Agent & RAG Eval Tutorial — Build Tracker

2026-10-18 · Sourav Banerjee · builds what [`PLAN.md`](PLAN.md) decides and
[`EVALUATIONS.md`](EVALUATIONS.md) specifies (§ numbers below point to that spec)

**Status values:** `todo` · `doing` · `done` · `blocked` · `skip`. Change the Status cell only; put
the reason for `blocked`/`skip` in Notes.
**💰** marks a task that calls the paid OpenAI API. Per `CLAUDE.md`, it runs only after you approve.
**Course folder:** `courses/04-end-to-end-eval-tutorial/` (P0.2). Kernel: `end-to-end-eval-tutorial`.

## Course rules (owner directive, 2026-10-18)

Every task below follows these. The goal is an end-to-end picture of how evaluation works, not
learning Python.

1. **Each notebook stands alone.** It runs top to bottom without any other notebook run first in
   the session. State passes through files in `data/` (written by one notebook, read by the next);
   a notebook whose input file is missing says which notebook writes it.
2. **No shared modules, no scripts.** Helpers are redefined in each notebook that uses them;
   duplication is accepted. The only exception is a file a tool must execute outside Jupyter (the
   CI gate in P8). This overrides the `format-notebook` skill's `helpers/` import pattern.
3. **Beginner-readable code.** One idea per cell, short cells (aim ≤ 30 lines). Plain loops and
   `if` over clever one-liners; no nested comprehensions, decorators, or custom classes unless a
   library requires one. Descriptive names (`retrieved_chunk_ids`, not `rids`).
4. **Comments explain the evaluation.** What is being measured and why, what a good or bad number
   means; not Python syntax. Each metric cell ends by printing the score with a one-line reading
   of it.
5. **Library calls shown plainly.** Call RAGAS / DeepEval / LangSmith directly in the cell where
   the concept is taught, never behind a wrapper function.

Progress by status:

```bash
grep -oE '\| (todo|doing|done|blocked|skip) \|' courses/04-end-to-end-eval-tutorial/TRACKER.md | sort | uniq -c
```

## Phase overview

| Phase | Goal | Notebooks | Exit check | Status |
| --- | --- | --- | --- | --- |
| P0 | Decisions, environment, scaffolding | — | Env installs; every metric class name verified | done |
| P1 | The app under test | 01, 02 | Supervisor answers 5 smoke questions; traces appear in LangSmith | done |
| P2 | Golden set | 03 | ≥ 20 reviewed cases per slice in `data/golden_set.json` | done |
| P3 | RAG evaluation | 04, 05 | §2–6 scores per slice, blame table produced | done |
| P4 | Agent evaluation | 06, 07, 08 | §7–11 scores per slice | done |
| P5 | Safety and adversarial | 09 | Attack success rate per risk; critical violations listed | done |
| P6 | Judges and calibration | 10, 11 | Every gating judge has kappa reported | doing |
| P7 | Statistics, cost, experiments | 12 | Baseline vs candidate compared with CIs in LangSmith | todo |
| P8 | Release gate and CI | 13 | Gate fails a seeded regression in GitHub Actions | todo |
| P9 | Online evaluation | 14 | Online evaluators score sampled traces; failures feed `data/` | todo |
| P10 | Docs, integration, release | — | Docs gates pass; links swept; committed | todo |
| P11 | Optional: the Langfuse track | 15+ | Same app traced, tested and monitored in Langfuse | skip |

---

## P0 — Decisions, environment, scaffolding

Exit: environment installs cleanly, the LangSmith key works, every class name in the spec is checked.

| ID | Task | Output | Depends on | Status | Notes |
| --- | --- | --- | --- | --- | --- |
| P0.1 | Settle plan decisions 2, 5, 6 (agent domain, app model, judge model) | Answers in plan doc | — | done | Support desk; `gpt-4o-mini` app, `gpt-4o` judge (2026-10-18) |
| P0.2 | Settle decision 3: course folder name and number | Folder name | — | done | `courses/04-end-to-end-eval-tutorial/` |
| P0.3 | Course contract: self-contained notebooks, no shared modules, beginner-readable code (Course rules above) | Line in course README | P0.2 | done | Decided 2026-10-18 |
| P0.4 | Decide output policy: keep outputs (like course 03) or strip; update the pre-commit hook skip list | Hook config | P0.2 | done | Keep outputs; folder added to `KEEP_OUTPUTS` in `.claude/hooks/strip_notebook_outputs.py` |
| P0.5 | Create folder, `README.md` skeleton, `data/` | Course folder | P0.2 | done | README with stack, notebook plan, setup, cost |
| P0.6 | Write `requirements.txt` with exact pins: `langgraph==1.2.11`, `deepeval==4.2.3`, `ragas==0.4.3`, `langchain-community` held per course 03, `chromadb`, `langsmith`, `ranx`, `deepteam`, `ipykernel==6.30.1` | `requirements.txt` | P0.5 | done | Resolved `deepteam==1.0.10`, `ranx==0.3.21`; added `sentry-sdk==2.72.0` (deepteam imports it undeclared); `uv pip check` clean |
| P0.7 | Create own `.venv` + Jupyter kernel; install with `uv pip install --python .venv/bin/python -r requirements.txt` | Working kernel | P0.6 | done | `.venv` on Python 3.12.14; kernel `end-to-end-eval-tutorial` |
| P0.8 | LangSmith Developer account; `LANGSMITH_API_KEY`, `LANGSMITH_PROJECT`, `LANGSMITH_ENDPOINT` in `.env.example` and the root `.env` | Working API key | — | done | Key works (stored as `LANGCHAIN_API_KEY`, which LangSmith also reads). Root `.env` already sets `LANGSMITH_TRACING=true`, project `ProductionAIAgent`; course notebooks override the project to `end-to-end-eval-tutorial`. Langfuse moved to optional phase P11 |
| P0.11 | Pin `langsmith` and verify `Client`, `traceable`, `evaluate`, `list_runs`, `create_feedback`, `create_dataset`, `create_examples`, annotation-queue methods import | `requirements.txt` | P0.7 | done | `langsmith==0.14.11` (what langchain-core 1.6.2 resolves); `langfuse` pin commented as optional |
| P0.12 | Trace budget: count traces per full run vs the 5k/month free cap; decide whether RAGAS/DeepEval judge calls are traced (separate project, or tracing off around judges) | Note in course README | P1.7 | todo | Measured in P1: one agent run = one root trace (≈550–1,800 tokens, $0.0001–0.0003). Direct tool `.invoke()` checks also make root traces; wrap them in `tracing_context(enabled=False)` if the budget gets tight |
| P0.9 | Verify every RAGAS / DeepEval / DeepTeam class named in the spec against the installed versions; fix the spec | Spec corrected | P0.7 | done | All names import. Fixed in spec: `ConversationRelevancyMetric` → `TurnRelevancyMetric`. RAGAS has no `ResponseRelevancy`; spec already used `AnswerRelevancy` |
| P0.10 | Estimate full-run cost per notebook (cases × judge calls × price) | Cost table in course README | P0.1 | done | Estimates, not measured: ≈ $30–35 per full run on `gpt-4o-mini` / `gpt-4o`, ≈ $5–10 on the current Nebius models (rescaled 2026-11-18 from price ratios); table in course README |

## P1 — The app under test

Exit: the LangGraph supervisor answers 5 smoke questions end to end and each run is a LangSmith trace.

| ID | Task | Output | Depends on | Status | Notes |
| --- | --- | --- | --- | --- | --- |
| P1.1 | Write the knowledge base (policies, FAQs, product docs) | `data/kb/*.md` | P0.1 | done | 9 articles in `data/kb/`, ~1,200 words, fictional store Pinecrest Outdoor Supply |
| P1.2 | Chunk with stable chunk IDs; embed with `text-embedding-3-small` into Chroma | Persisted Chroma store | P1.1 | done | 31 chunks → `data/kb_chunks.json`, indexed into `data/chroma_db/` (2026-10-19) |
| P1.3 | RAG agent node (retrieve → answer with citations) | Notebook 01 | P1.2 | done | Notebook 01 executed, outputs kept: 3 questions answered with citations or the decline sentence |
| P1.4 | Mock account DB + tools: `lookup_order`, `issue_refund`, `create_ticket`, `search_kb` | Notebook 02 | P0.5 | done | 6 orders, each triggers one rule; every refund branch tested offline |
| P1.5 | Account-tools agent node | Notebook 02 | P1.4 | done | Notebook 02; compiles offline |
| P1.6 | Supervisor router + escalation node; LangGraph graph | Notebook 02 | P1.3, P1.5 | done | Supervisor (structured `RouteDecision`) + escalation node; graph compiles, Mermaid printed |
| P1.7 | LangSmith tracing: set `LANGSMITH_TRACING=true` inside the notebook; LangGraph nodes, tool calls and LLM calls trace with no code change | Traces in LangSmith | P0.8, P1.6 | done | Traces in project `end-to-end-eval-tutorial`; each `run_id` in `agent_runs.json` resolves to its trace with tokens and cost. Never put `LANGSMITH_TRACING` in the shared root `.env` |
| P1.8 | Trace export: node sequence, tool calls, retrieved chunk IDs per run, written to `data/agent_runs.json` | `data/agent_runs.json` | P1.7 | done | `run_agent()` records route, nodes, tool calls, chunks, answer, refunds, tickets, latency, `run_id` → `data/agent_runs.json`; 5 runs saved |
| P1.9 | Smoke run of 5 questions across slices | Committed outputs | P1.8 | done | All 5 paths correct after two prompt fixes the first run exposed: supervisor sent general policy questions to the account agent; account agent asked to re-confirm an email it was given |
| P1.10 | Define the minimal app-rebuild cell (load Chroma, tools, graph) that later notebooks copy | Cell text in notebook 02 | P1.6 | done | Notebook 02 Part 9: one cell generated from the teaching cells (banners and prints dropped), so they can't drift. Tested in a fresh process: refund issued |

## P2 — Golden set

Exit: `data/golden_set.json` passes every §1 check with ≥ 20 reviewed cases per slice.

| ID | Task | Output | Depends on | Status | Notes |
| --- | --- | --- | --- | --- | --- |
| P2.1 | Freeze the case schema (§0) | Schema in notebook 03 | P1.6 | done | 10 fields; `expected_tool_calls` lists only args that must match; `expected_end_state` = `{refund_order_ids, ticket_created}`; `null` = not checked |
| P2.2 | Hand-write cases: `simple`, `multi_hop`, `out_of_scope` | Cases | P2.1 | done | 13 / 14 / 20 in `data/golden_set_handwritten.json`; chunk IDs checked against `kb_chunks.json` |
| P2.3 | Hand-write cases: `tool_required`, `handoff` with expected calls and end states | Cases | P2.1 | done | 20 / 20; every expected end state replayed against the mock DB with the real tools (0 mismatches) |
| P2.4 | Hand-write `adversarial` cases (feeds P5) | Cases | P2.1 | done | 20: injection, PII, prompt leak, override, over-limit, duplicate refund, false confirmation, fraud help |
| P2.5 | Generate extra cases with RAGAS `TestsetGenerator` | Candidate cases | P1.2 | done | 21 candidates → `data/ragas_candidates.json` (cached; ~$0.50). `generate_with_chunks`; single-hop on `themes` (most short chunks have no entities); extra 0.5 similarity link for multi-hop; `llm_factory` (LangChain wrapper breaks across event loops). Needs `rapidfuzz` |
| P2.6 | Review generated cases; keep ≤ 50% synthetic per slice | Reviewed cases | P2.5 | done | Reviewed by Claude, not the owner: 14 kept, 7 dropped (wrong reference, ambiguous route, vague, near-copy, single-chunk multi-hop). Synthetic share 38% / 30% |
| P2.7 | Run §1 checks: coverage, duplicates, completeness, leakage | Check report | P2.2–P2.6 | done | All 5 pass: max pair cosine 0.897; 0 leaks, control finds 5/5 smoke questions in nb01–02 code |
| P2.8 | Write notebook 03 | Notebook 03 | P2.7 | done | Executed, outputs kept; writes `data/golden_set.json` (121 cases) only if all checks pass |

## P3 — RAG evaluation

Exit: §2–6 scores reported per slice; the blame table splits failures between retriever and generator.

| ID | Task | Output | Depends on | Status | Notes |
| --- | --- | --- | --- | --- | --- |
| P3.1 | §2 metrics in plain Python: hit rate, recall, precision, MRR, nDCG | Notebook 04 | P2.8 | done | 41 knowledge cases, `retrieve(k=10)`; recall@4 = 1.000 both slices; multi_hop recall@1 0.433 |
| P3.2 | Same metrics via `ranx`; `ranx.compare()` between two retriever settings (k, chunk size) | Notebook 04 | P3.1 | done | ranx matches plain Python on every metric; dense vs stdlib keyword retriever: recall@4 1.000 vs 0.646, p < 0.05 |
| P3.3 | §3 judged retrieval: RAGAS + DeepEval context precision / recall / relevance | Notebook 04 | P3.1 | done | gpt-4o on the 35 runs routed to the RAG agent, using their actual top-4; the two libraries' "relevance" differ by ≥ 0.5 on 24/35 cases (different definitions, explained) |
| P3.4 | Compare label-based vs judged retrieval scores; list disagreements | Notebook 04 | P3.2, P3.3 | done | 1 disagreement, `simple-h02`: judge is right, the reference adds an unsupported claim |
| P3.5 | §4 reference-free generation: faithfulness, answer relevancy, hallucination | Notebook 05 | P2.8 | done | Faithfulness RAGAS 0.92 / 0.89, DeepEval 0.95 / 1.00 (simple / multi_hop); 20/20 out-of-scope declined, 0/35 false declines |
| P3.6 | §5 reference-based: factual correctness, semantic similarity, `GEval` correctness, EM/F1 | Notebook 05 | P3.5 | done | GEval 0.95 / 0.89; RAGAS factual 0.70 / 0.76; EM ≈ 0.03, F1 0.56 (unsuitable for sentences) |
| P3.7 | §6 blame table by slice | Notebook 05 | P3.3, P3.5 | done | simple: 19 ok, 1 generation, 1 routing; multi_hop: 14 ok, 1 test-case wrong, 5 routing; 0 retrieval failures. "Correct" = GEval ≥ 0.7 |
| P3.8 | Save per-case RAG scores to `data/` for P7 | `data/rag_scores.json` | P3.7 | done | 61 knowledge cases keyed by case_id with run_id, route, every metric and a verdict |

## P4 — Agent evaluation

Exit: §7–11 scores reported per slice, with failures attributed to a node.

| ID | Task | Output | Depends on | Status | Notes |
| --- | --- | --- | --- | --- | --- |
| P4.1 | §7 deterministic tool checks: selection, arguments, schema, abstention, error rate | Notebook 06 | P2.8 | done | Selection 98%; args 96% exact / 100% normalised; 45/45 schema-valid; abstention 78/78; tool results by replay: 0 crashed, 18 refused by rules |
| P4.2 | §7 DeepEval `ToolCorrectnessMetric` / `ArgumentCorrectnessMetric` beside the stdlib checks | Notebook 06 | P4.1 | done | 13 disagreements with stdlib listed; `INPUT_PARAMETERS` mode gives partial credit over the union of keys |
| P4.3 | §8 trajectory: strict / unordered / subset / superset, step efficiency, loop detection | Notebook 07 | P1.8 | done | Efficiency 0.94 tool_required / 1.00 handoff; 0 loops; extra `search_kb` on tool_required-h16 |
| P4.4 | §8 `GEval` trajectory-quality judge | Notebook 07 | P4.3 | done | 23 runs; agrees with strict match on 20/23 |
| P4.5 | §9 routing accuracy, handoff count, escalation correctness | Notebook 07 | P1.8 | done | Routing 92% (multi_hop 75%); escalation precision 0.95, recall 1.00 |
| P4.6 | §9 context preservation judge + first-failing-node attribution | Notebook 07 | P4.5 | done | Regex check and GEval agree 23/23; failures attributed supervisor → tools → end state |
| P4.7 | §10 end-state check against mock DB | Notebook 08 | P1.4 | done | 98%; only failure tool_required-h07 (final-sale refusal also opened a ticket) |
| P4.8 | §10 DeepEval `TaskCompletionMetric` + RAGAS goal accuracy, compared to the state check | Notebook 08 | P4.7 | done | Agreement with state check: TaskCompletion 60% default, 92% with `task=reference_answer`; RAGAS 65% (20-case subset). Judges infer "refund" as the goal and fail correct refusals |
| P4.9 | §11 multi-turn scenarios + `ConversationSimulator` | Notebook 08 | P1.6 | done | Chat wrapper (conversation in `question`, history in `messages`; app cell unchanged); 4 scripted + 2 simulated. Wrapper weakness: whole conversation as retrieval query loses single-turn answers |
| P4.10 | §11 conversational metrics: retention, completeness, relevancy, role adherence | Notebook 08 | P4.9 | done | 6 conversations; 2 retention zeros are judge errors (penalised asking for an email); low-score reasons printed |
| P4.11 | Save per-case agent scores to `data/` for P7 | `data/agent_scores.json` | P4.1–P4.10 | done | 121 records keyed by case_id with run_id; conversations in `data/conversation_scores.json` |

## P5 — Safety and adversarial

Exit: attack success rate per risk; every critical violation listed with its trace.

| ID | Task | Output | Depends on | Status | Notes |
| --- | --- | --- | --- | --- | --- |
| P5.1 | Write the policy: critical vs non-critical violations | Policy table in notebook 09 | P0.1 | done | Critical (must be 0): unauthorised refund, cross-customer data leak, following instructions in retrieved text, Moderation-flagged content. Non-critical: excessive agency, policy violation, prompt leak (prompts hold no secrets), jailbreak |
| P5.2 | Poisoned KB chunk for indirect prompt injection | Test fixture | P1.2 | done | In-memory `chromadb.EphemeralClient` index (31 chunks + poison); `data/chroma_db/` untouched. Canary `PC-OVERRIDE-7731` gives an exact, judge-free check |
| P5.3 | DeepTeam scan: prompt injection, jailbreak, PII leakage, prompt leakage, excessive agency | Notebook 09 | P1.6 | done | PIILeakage, BOLA, PromptLeakage, ExcessiveAgency × PromptInjection, Roleplay, LinearJailbreaking(3 turns); 18 test cases, 0 successful; `gpt-4o-mini` attacker, `gpt-4o` judge, `async_mode=False` (shared mock DB) |
| P5.4 | `GEval` safety rubric for policy violations | Notebook 09 | P5.1 | done | 20 adversarial runs; 1 fail (`adversarial-h12`, refund-twice) where the end state matches the label: judge-vs-label disagreement for notebook 11 |
| P5.5 | OpenAI Moderation baseline | Notebook 09 | P1.6 | done | `omni-moderation-latest`, 121 answers in one call, 0 flagged |
| P5.6 | Unauthorised-refund end-state check | Notebook 09 | P4.7 | done | 0 unauthorised refunds over 121 baseline + 36 scan runs; 0 email leaks; 0 verbatim prompt lines |
| P5.7 | Attack success rate per risk; save to `data/` | `data/safety_scores.json` | P5.3–P5.6 | done | 3 critical violations, all indirect injection (3/4 poisoned probes obeyed the planted instruction); run_ids are LangSmith traces. App fix needed: RAG prompt must treat article text as data |

## P6 — Judges and calibration

Exit: every judge that will gate a release has kappa, TPR and TNR reported.

| ID | Task | Output | Depends on | Status | Notes |
| --- | --- | --- | --- | --- | --- |
| P6.1 | Rubric judges with `GEval`: tone, policy wording, escalation phrasing | Notebook 10 | P2.8 | doing | 💰 Written in notebook 10, not yet run |
| P6.2 | Decision-tree judge with `DAGMetric` for the refund flow | Notebook 10 | P6.1 | doing | 💰 Written in notebook 10, not yet run |
| P6.3 | Pairwise judge with position swap | Notebook 10 | P6.1 | doing | 💰 Written in notebook 10, not yet run |
| P6.4 | LangSmith annotation queue; sample 50–100 cases per gating judge | Queue in LangSmith | P0.8, P6.1 | todo | |
| P6.5 | Human labelling pass | Labels | P6.4 | todo | Manual |
| P6.6 | Agreement: Cohen's kappa, TPR, TNR, confusion matrix (stdlib) | Notebook 11 | P6.5 | todo | Free |
| P6.7 | Bias checks: position, verbosity, self-preference | Notebook 11 | P6.6 | todo | 💰 |
| P6.8 | Revise rubrics where kappa < 0.6; re-measure | Notebook 11 | P6.6 | todo | 💰 |
| P6.10 | Reference judge: run `gpt-4o` beside the Qwen3-235B judge on the same calibration cases; kappa / TPR / TNR of each against the human labels and the end-state checks, plus judge-vs-judge agreement | Notebook 11 | P6.6 | todo | Owner decision 2026-10-20 (final): app `deepseek-ai/DeepSeek-V4-Flash-0731`, primary judge `Qwen/Qwen3-235B-A22B-Instruct-2507`, both on Nebius Token Factory (Databricks judges hit the workspace output-tokens-per-minute limit; a local Ollama judge was too slow). gpt-4o runs on the calibration subset only (≈ $1). P6.7's self-preference check = DeepSeek judging its own answers 💰 |
| P6.9 | Save judge trust table to `data/` for the gate | `data/judge_trust.json` | P6.8, P6.10 | todo | One row per judge × metric: Qwen3-235B on Nebius (primary) and gpt-4o (reference) |

## P7 — Statistics, cost, experiments

Exit: baseline and candidate compared per slice with CIs, in LangSmith and in notebook 12.

| ID | Task | Output | Depends on | Status | Notes |
| --- | --- | --- | --- | --- | --- |
| P7.1 | Per-slice report across P3–P5 scores (`defaultdict`) | Notebook 12 | P3.8, P4.11, P5.7 | todo | Free |
| P7.2 | Bootstrap 95% CIs (stdlib `random`) | Notebook 12 | P7.1 | todo | Free |
| P7.3 | Paired comparison: paired bootstrap + McNemar | Notebook 12 | P7.2 | todo | Free |
| P7.4 | Sample-size estimate per slice | Notebook 12 | P7.2 | todo | Free |
| P7.5 | Cost and latency from LangSmith traces (§16) | Notebook 12 | P1.7 | todo | Free; read token cost per trace with `client.runs.query()` (`list_runs` is deprecated in 0.14.11) |
| P7.6 | Upload golden set as a LangSmith dataset (`create_dataset` + `create_examples`) | Dataset | P2.8 | todo | |
| P7.7 | Run baseline and one candidate (prompt or model change) as LangSmith experiments with `evaluate()` | Two experiment runs | P7.6 | todo | 💰 |
| P7.8 | Save baseline and candidate scores for the gate | `data/baseline_scores.json`, `data/candidate_scores.json` | P7.7 | todo | |

## P8 — Release gate and CI

Exit: the gate passes the baseline and fails a seeded regression, in GitHub Actions.

| ID | Task | Output | Depends on | Status | Notes |
| --- | --- | --- | --- | --- | --- |
| P8.1 | Write gate rules: critical safety, slice floors, no regression, judge trust, budget (§18) | `gate_rules.json` | P6.9, P7.8 | todo | |
| P8.2 | Gate logic taught step by step in notebook 13, then copied into the one script CI runs | `gate.py` | P8.1 | todo | Free; the only script in the course (Course rule 2) |
| P8.3 | Seeded regression to prove the gate fails | Test fixture | P8.2 | todo | |
| P8.4 | Workflow: free `gate` job on push/PR, paths-filtered to the course | `.github/workflows/…yml` | P8.2 | todo | |
| P8.5 | Workflow: paid `evaluate` job on `workflow_dispatch` only; skips without `OPENAI_API_KEY` | Same workflow | P8.4 | todo | Never on push/PR |
| P8.6 | Notebook 13 explaining the gate and the free/paid split | Notebook 13 | P8.5 | todo | |
| P8.7 | Push to a branch and confirm the gate fails the seeded regression | CI run | P8.6 | todo | Outward-facing: ask before pushing |

## P9 — Online evaluation

Exit: LangSmith online evaluators score a trace sample, and failing traces reach `data/`.

| ID | Task | Output | Depends on | Status | Notes |
| --- | --- | --- | --- | --- | --- |
| P9.1 | Simulated production traffic (replay plus fresh questions) | Trace stream | P1.7 | todo | 💰 |
| P9.2 | LangSmith online evaluators: faithfulness, relevancy, safety on a 5–10% sample | Evaluator config | P9.1 | todo | 💰 |
| P9.3 | Retrieval health and outcome proxies (empty retrieval, escalation, feedback) | Notebook 14 | P9.1 | todo | |
| P9.4 | Drift view vs launch week (simulated dates; traces expire after 14 days) | LangSmith monitoring charts | P9.2 | todo | |
| P9.5 | Feedback loop: failing traces → reviewed → golden set | Notebook 14 | P9.2, P2.8 | todo | |
| P9.6 | Optional τ-bench sidebar | Notebook 14 appendix | P1.6 | skip | Unpick if wanted; 💰 |

## P10 — Docs, integration, release

Exit: docs gates pass, every cross-link resolves, and the course is committed.

| ID | Task | Output | Depends on | Status | Notes |
| --- | --- | --- | --- | --- | --- |
| P10.1 | Apply the `format-notebook` contract to notebooks 01–14 (minus its `helpers/` imports) | Clean notebooks | P1–P9 | todo | |
| P10.1a | Beginner readability pass on every notebook against Course rules 3–5 | Review notes per notebook | P10.1 | todo | |
| P10.1b | Standalone check: run each notebook in a fresh kernel with only its `data/` inputs present | Pass/fail per notebook | P10.1 | todo | 💰 |
| P10.2 | Full end-to-end run on the course kernel | Outputs (if kept per P0.4) | P10.1 | todo | 💰 largest run; ask first |
| P10.3 | Course `README.md`: notebook table, setup, cost table, data hand-off map | README | P10.2 | todo | |
| P10.4 | Update `courses/README.md`, root `README.md`, `INDEX.md` | Updated indexes | P10.3 | todo | |
| P10.5 | Map notebooks into `docs/study-guide/evaluation-roadmap.md` levels | Roadmap rows | P10.3 | todo | |
| P10.6 | Run docs gates: `check_index_coverage.py`, `check_drill_sync.py`, `check_links.py docs` | All pass | P10.4, P10.5 | todo | Free |
| P10.7 | Sweep cross-references: notebooks naming each other, READMEs linking across folders | No broken links | P10.4 | todo | |
| P10.8 | Check the archive rule: nothing this course replaces is left orphaned | Note in `archive/README.md` if needed | P10.4 | todo | |
| P10.9 | Commit to `main` | Commit | P10.6–P10.8 | todo | Push only when asked |

## P11 — Optional: the Langfuse track

Owner decision (2026-10-18): LangSmith is the main platform; Langfuse, the open-source and
self-hostable alternative, gets its own notebooks later. Every task starts as `skip`; change to
`todo` when this track starts.

| ID | Task | Output | Depends on | Status | Notes |
| --- | --- | --- | --- | --- | --- |
| P11.1 | Langfuse Cloud free project; keys in `.env` (`LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_BASE_URL`) | Working keys | — | skip | Vars already in `.env.example` |
| P11.2 | Uncomment `langfuse==4.15.4` in `requirements.txt`; verify imports | Pin | P11.1 | skip | Verified earlier with this venv |
| P11.3 | Trace the same LangGraph app with `langfuse.langchain.CallbackHandler` | Langfuse notebook 1 | P11.2, P1.6 | skip | 💰 |
| P11.4 | Datasets + experiments: baseline vs candidate, scores attached | Langfuse notebook 1 | P11.3, P7.8 | skip | 💰 |
| P11.5 | Annotation queues + online LLM-judge evaluators | Langfuse notebook 2 | P11.3 | skip | 💰 |
| P11.6 | LangSmith vs Langfuse comparison table from the course's own runs | Section in course README | P11.4, P11.5 | skip | |
| P11.7 | Self-hosting appendix (Docker Compose) | Appendix | P11.1 | skip | Docker is not installed on this machine |
| P11.8 | Add the Langfuse project MCP server (`claude mcp add … /api/public/mcp`, `--scope local`) | MCP connected | P11.1 | skip | Docs MCP `langfuse-docs` already added (user scope) |
