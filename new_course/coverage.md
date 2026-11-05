# Coverage matrix

Every concept and deliverable in the [roadmap](enterprise-rag-agent-evaluation-roadmap.md) maps to the lesson section that teaches it, the exercise that practises it and the evidence that shows it was learned. Each week has a theory file and a hands-on file, and section numbers say which one.

## Week 1: Evaluation lifecycle and basic metrics

Files: [theory](weeks/week-01-evaluation-basics/theory/week-01-evaluation-basics-theory.md) · [hands-on](weeks/week-01-evaluation-basics/handson/week-01-evaluation-basics-handson.md) · [dataset](weeks/week-01-evaluation-basics/dataset/README.md)

| Roadmap concept | Taught in | Practised in | Completion evidence |
|---|---|---|---|
| Offline vs online evaluation | Theory §4 Offline and online evaluation | Design review Q4 | Learner explains the online-to-offline loop |
| Deterministic vs probabilistic checks | Theory §5 Deterministic and probabilistic checks | Design review Q5 | Learner names which Week 1 checks survive an LLM agent |
| Correctness vs quality | Theory §2, Theory §6 Correctness, quality and safety | Design review Q1 | Learner explains case-0024 |
| Precision, recall, F1 | Theory §8 Precision, recall and F1; Theory §10.2 slice table | Exercise 5 | Hand calculation matches `test_confusion_matrix_and_metrics_match_hand_calculation` |
| Failure taxonomy | Theory §9 A failure taxonomy | Runner output "Failures by category" | Failures counted by category and severity |
| Keyword matching passes a wrong answer | Theory §7 The three Week 1 checks; Theory §10.1 case-0011 | Exercise 5 | `test_keyword_check_passes_a_wrong_answer` |
| 30 labeled cases | Hands-on §1 What is in a case | Exercises 1–4 | `dataset/cases.jsonl`, `test_fixture_has_30_unique_cases` |
| Exact outcome, required keyword, forbidden action checks | Hands-on §1 The checks | Drills 1 and 2 | `test_known_wrong_outcome_is_detected`, `test_forbidden_refund_on_another_customers_order_is_detected` |
| Runner with per-case results and reasons | Hands-on §1 Run it | `--case`, `--cases` | Runner output in Hands-on §1 |
| Staff checkpoint: quality does not guarantee safe behavior | Theory §2, Theory §11 Q1 | Design review Q1 | Model answer in Theory §11 |

## Week 2: Golden datasets and test design

Files: [theory](weeks/week-02-golden-datasets/theory/week-02-golden-datasets-theory.md) · [hands-on](weeks/week-02-golden-datasets/handson/week-02-golden-datasets-handson.md) · [dataset](weeks/week-02-golden-datasets/dataset/README.md)

| Roadmap concept | Taught in | Practised in | Completion evidence |
|---|---|---|---|
| Ground truth | Theory §3 Where labels come from | Exercise 3 | Learner's spot-check labels match Hands-on §4 |
| Representative slices | Theory §5 Slices and representative coverage | `lab.py slices`, exercise 5 | Learner names the critical slices behind 62% |
| Positive, negative, adversarial (and edge) cases | Theory §6 Four kinds of case | Exercise 1 | Four new cases validate |
| Dataset versioning | Theory §7 Dataset versions and the manifest | Drill 1 | `test_edited_file_breaks_the_manifest_hash` |
| Leakage | Theory §8 Training, development and holdout separation | Exercise 4, drill 2 | `test_leak_check_finds_reworded_holdout_example` |
| Train/dev/test separation | Theory §8 Training, development and holdout separation | Exercise 4 | 73/27 split, `test_week1_ids_are_stable_and_in_development` |
| 100 cases with IDs, outcomes, policy versions, risk labels, authorized user | Theory §4 What a case records | Exercise 1 | `datasets/`, `test_shipped_dataset_is_valid_and_split_73_27` |
| Schema validator | Hands-on §1 How the validator works | Exercise 2 | `lab.py validate` on the broken fixture prints 13 errors |
| Reject malformed, duplicate, overlapping records | Hands-on §1 Run it | Exercise 2 | `test_broken_fixture_reports_every_planted_error` |
| Keep holdout answers out of prompts | Theory §8, Hands-on §1 leak-check | Drill 2 | `lab.py leak-check` finds case-0074 |
| Staff checkpoint: prevent contamination and missing edge cases | Theory §11 Q1, Q2 | Design review | Model answers in Theory §11 |

## Week 3: Model judges and human calibration

Files: [theory](weeks/week-03-judges-and-human-calibration/theory/week-03-judges-and-human-calibration-theory.md) · [hands-on](weeks/week-03-judges-and-human-calibration/handson/week-03-judges-and-human-calibration-handson.md) · [dataset](weeks/week-03-judges-and-human-calibration/dataset/README.md)

| Roadmap concept | Taught in | Practised in | Completion evidence |
|---|---|---|---|
| Rubrics | Theory §4.1 Rubrics; Theory §10.2 rubric version 2 | Exercise 2 | Learner's rubric version 2 |
| Binary vs ordinal scoring | Theory §4.2 Binary and ordinal scores | Report score agreement | Parser rejects a verdict that contradicts its score |
| Pairwise comparison | Theory §5 Pairwise comparison and position bias | `lab.py pairwise`, exercise 4 | `test_pairwise_keeps_only_order_independent_winners` |
| Judge bias | Theory §6 Known judge biases | Exercises 4 and 5 | Learner explains pair-0028 |
| Reference-free vs reference-based grading | Theory §4.3 Reference-free and reference-based grading | Exercise 3 | Learner lists the verdicts that change |
| Agreement with human labels | Theory §8 Agreement with human labels; Theory §10.1 hand calculation | Exercise 1 | `test_agreement_and_kappa_match_hand_calculation`; learner's own kappa |
| Judge prompt with cited evidence | Theory §7 Structured output and failing closed | `lab.py prompt` | `judge_prompt.md`, `test_parser_fails_closed_on_bad_responses` |
| Human-review sheet, 30 samples | Hands-on §1 Label the samples yourself | Exercise 1 | Learner's completed sheet. **Requires real human labels**: the example sheet is marked not human |
| Disagreement report and confusion matrix | Theory §10, Hands-on §1 Run it | Exercise 1, drill 2 | Report output in Hands-on §1 |
| Fluent unsafe answer scored well, failing a deterministic check | Theory §2, Theory §10.3 | None | `test_fluent_unsafe_reply_passes_judge_but_fails_safety_check` |
| Staff checkpoint: a judge score cannot be the sole safety control | Theory §11 Q1 | Design review | Model answer in Theory §11 |

**Validation gaps.** The Week 3 judge responses are hand-written mocks, and the example labels are not human review. Both exercise the code only. The live judge (`handson/lab.py judge --live`) was checked against the installed `openai` 2.54.0 API but has not been run against a model. No calibration result exists until a learner labels the samples and runs a live judge.

## Week 4: Retrieval evaluation

Files: [theory](weeks/week-04-retrieval-evaluation/theory/week-04-retrieval-evaluation-theory.md) · [hands-on](weeks/week-04-retrieval-evaluation/handson/week-04-retrieval-evaluation-handson.md) · [dataset](weeks/week-04-retrieval-evaluation/dataset/README.md)

| Roadmap concept | Taught in | Practised in | Completion evidence |
|---|---|---|---|
| Precision@k, Recall@k, Hit Rate@k, MRR, nDCG | Theory §5; Theory §6 hand calculations | `lab.py hand`, exercise 1 | `test_hand_ranking_outdated_first`, `test_hand_ranking_answer_at_rank_four` |
| Ground-truth relevance labels | Theory §4 Relevance labels | Exercise 2 | `datasets/retrieval/policy-queries-v1.jsonl`, `test_query_set_has_50_labeled_queries_on_current_public_sections` |
| Chunk size | Theory §9 Chunk size | `lab.py compare` | `test_document_chunks_buy_recall_with_context_size` |
| Metadata filters | Theory §8 Metadata filters | Exercise 5 | `test_metadata_filter_removes_superseded_and_internal_chunks` |
| Dense versus hybrid retrieval, 50 queries, k = 3 and k = 5 | Theory §7, §10.1 | `lab.py compare`, `dense-live` | `test_concept_retriever_beats_bm25_on_paraphrases_and_hybrid_wins_overall_hit_rate`. **Dense is measured only with the concept-vector stand-in** until `dense-live` runs |
| Per-query and slice metrics | Theory §10.2 | `lab.py slices`, `lab.py query` | Slice output in Hands-on §1 |
| Staff checkpoint: when MRR is useful versus Recall@k | Theory §10.3, Theory §11 Q1 | Design review | Model answer in Theory §11 |

## Week 5: Answer quality and evidence

Files: [theory](weeks/week-05-answer-quality-and-evidence/theory/week-05-answer-quality-and-evidence-theory.md) · [hands-on](weeks/week-05-answer-quality-and-evidence/handson/week-05-answer-quality-and-evidence-handson.md) · [dataset](weeks/week-05-answer-quality-and-evidence/dataset/README.md)

| Roadmap concept | Taught in | Practised in | Completion evidence |
|---|---|---|---|
| Faithfulness and hallucination | Theory §4 | Exercise 4 | `test_outdated_answer_is_faithful_but_wrong`, `test_missing_evidence_produces_an_unsupported_claim_and_no_abstention` |
| Citation accuracy | Theory §5 | Drill 1 | `test_citation_check_catches_a_sentence_cited_to_the_wrong_chunk` |
| Answer correctness | Theory §6 | Drill 2 | `check_correctness` results in Hands-on §1 |
| Response relevance | Theory §7 | Exercise 5 | `test_filtered_retrieval_can_lose_the_gold_section` |
| Abstention | Theory §8 | Exercise 3 | Abstaining writer passes the missing slice |
| Access-aware retrieval | Theory §9 | `report --retrieval filtered` | `test_filtered_retrieval_removes_stale_and_internal_sources`, `test_internal_playbook_text_is_a_critical_failure` |
| Outdated, contradictory, missing and restricted evidence | Theory §2, §10.1 | Exercise 2 | `datasets/answers/answer-cases-v1.jsonl`, `test_answer_set_has_24_cases_in_five_slices` |
| Custom evaluators plus a Ragas experiment | Theory §10.3 | `ragas --live` | Seven local checks in `lab.py`. **The Ragas run is not yet validated**: pins and APIs checked in an isolated environment, not run against a model |
| Staff checkpoint: separate retrieval failure from generation failure | Theory §10.2, Theory §11 Q2 | Exercise 5 | `test_missing_evidence_fails_with_either_retrieval`, model answer in Theory §11 |

## Week 6: RAG regression comparisons

Files: [theory](weeks/week-06-rag-regression-comparisons/theory/week-06-rag-regression-comparisons-theory.md) · [hands-on](weeks/week-06-rag-regression-comparisons/handson/week-06-rag-regression-comparisons-handson.md) · [dataset](weeks/week-06-rag-regression-comparisons/dataset/README.md)

| Roadmap concept | Taught in | Practised in | Completion evidence |
|---|---|---|---|
| Version comparison on the same cases | Theory §3 | Drill 1 | `test_both_versions_run_on_the_same_cases` |
| Query rewriting, reranking, hybrid search | Theory §4, §8 | `lab.py ablate` | `test_ablation_shows_retrieval_metrics_and_answers_can_disagree` |
| Quality, cost and latency trade-offs | Theory §5, §10 | Exercise 5 | Scorecard in Hands-on §1. **Cost and latency are simulated** from illustrative constants |
| Slice regression hidden by the average | Theory §2, §6 | `lab.py slices`, `paired` | `test_average_hides_a_regression_on_the_normal_slice` |
| Retrieval versus generation cause | Theory §7 | `lab.py attribute`, drill 2 | `test_gold_context_swap_separates_retrieval_from_generation` |
| Retrieval drift | Theory §9 | Exercise 4 | Drift cell in the notebook |
| Scorecard and release recommendation | Theory §10 | Exercises 1 to 3 | `test_release_policy_blocks_v2_and_ships_v2_1` |
| Staff checkpoint: defend a choice where quality improves but latency worsens | Theory §10.2, Theory §11 Q1 | Exercise 3 | Model answer in Theory §11 |

## Week 7: Tools and persisted side effects

Files: [theory](weeks/week-07-tools-and-side-effects/theory/week-07-tools-and-side-effects-theory.md) · [hands-on](weeks/week-07-tools-and-side-effects/handson/week-07-tools-and-side-effects-handson.md) · [dataset](weeks/week-07-tools-and-side-effects/dataset/README.md)

| Roadmap concept | Taught in | Practised in | Completion evidence |
|---|---|---|---|
| Tool selection | Theory §5 | Exercise 1 | `check_tool_selection` results in Hands-on §1 |
| Argument and schema validity | Theory §5 | Exercise 3 | `test_missing_idempotency_key_is_a_schema_failure` |
| Tool output validation | Theory §6 | Exercise 1 | `test_success_message_without_a_stored_refund_is_caught` |
| Authentication and authorization | Theory §4 | Exercise 5 | `test_lax_backend_lets_v1_refund_another_customers_order`, `test_lax_backend_leaks_data_even_to_an_agent_that_refuses` |
| State mutation and database read-back | Theory §7 | Exercise 4, drills 1 and 2 | `test_strict_backend_cannot_stop_a_refund_on_the_wrong_order` |
| Checks around get_customer, get_order, search_policy, create_refund | Theory §3, §8 | `lab.py report` | `test_matrix_counts` |
| Reject wrong-order refunds, unauthorized actions, success without a stored refund | Theory §2, §9 | `lab.py case` | `test_strict_backend_cannot_stop_a_refund_on_the_wrong_order`, `test_success_message_without_a_stored_refund_is_caught` |
| Staff checkpoint: why matching the final answer is not enough | Theory §10 Q1 | Design review | Model answer in Theory §10 |

## Week 8: Trajectories and task completion

Files: [theory](weeks/week-08-trajectories-and-task-completion/theory/week-08-trajectories-and-task-completion-theory.md) · [hands-on](weeks/week-08-trajectories-and-task-completion/handson/week-08-trajectories-and-task-completion-handson.md) · [dataset](weeks/week-08-trajectories-and-task-completion/dataset/README.md)

| Roadmap concept | Taught in | Practised in | Completion evidence |
|---|---|---|---|
| Exact vs flexible trajectories | Theory §4 | `lab.py match`, exercise 1 | `test_match_modes`, `test_valid_alternative_order_passes_invariants_but_not_exact_match` |
| Required and forbidden steps | Theory §5 | `lab.py case`, exercise 5 | `test_mutation_before_ownership_is_a_hard_failure_the_outcome_misses` |
| Trace grading | Theory §3, §5.2 | Drills 1 and 2 | `test_ownership_needs_the_signed_in_customer_on_the_lookup` |
| Task success | Theory §6 | `lab.py check --agent drops_refund`, exercise 2 | `test_outcome_checker_reads_the_ledger_not_the_path`, `test_lax_backend_shows_what_the_strict_one_blocked` |
| Efficiency | Theory §7 | Exercise 4 | `test_redundancy_counts_identical_reads_but_not_post_mutation_reads` |
| Partial credit | Theory §8 | `lab.py scorecard`, exercise 3 | `test_partial_credit_cannot_override_a_hard_failure` |
| Separate trajectory and outcome checkers | Theory §2, §6 | `lab.py case` | `check_trajectory` and `check_outcome` output in Hands-on §1 |
| Accept valid alternative tool orders | Theory §4, §5.3 | Exercise 1 | `test_valid_alternative_order_passes_invariants_but_not_exact_match` |
| Authorization before mutation, final refund state | Theory §5.2, §5.3, §6.1 | `lab.py case --agent refund_first --case tr-031` | `test_mutation_before_ownership_is_a_hard_failure_the_outcome_misses` |
| Partial credit cannot override a hard safety failure | Theory §8.1 | `lab.py case`, exercise 3 | `test_partial_credit_cannot_override_a_hard_failure` |
| Staff checkpoint: avoid over-constraining a valid agent plan | Theory §4, §9 Q1 | Design review | Model answer in Theory §9 |

## Week 9: Multi-turn state

Files: [theory](weeks/week-09-multi-turn-state/theory/week-09-multi-turn-state-theory.md) · [hands-on](weeks/week-09-multi-turn-state/handson/week-09-multi-turn-state-handson.md) · [dataset](weeks/week-09-multi-turn-state/dataset/README.md)

| Roadmap concept | Taught in | Practised in | Completion evidence |
|---|---|---|---|
| Sessions and conversation state | Theory §3 | `lab.py show` | Learner names the four state fields and what breaks without each |
| Checkpoints and restarts | Theory §4 | Exercise 5, drill 1 | `test_restart_loses_v1_order_but_not_v2`, `test_checkpoint_survives_a_reopened_store` |
| Follow-up clarification | Theory §5, §9.1 | Exercise 6 | `test_clarification_answer_is_bound_to_the_question` |
| Context carryover and long conversations | Theory §6 | Exercise 2 | `test_v1_loses_the_order_after_three_digressions` |
| Cross-session leakage and tenant isolation | Theory §7, §9.2 | Exercise 3, drill 2 | `test_shared_session_id_leaks_an_order_and_a_lax_backend_refunds_it` |
| 25 multi-turn scenarios with restart points | Theory §9; Hands-on §1 | Exercise 1 | `datasets/conversations/conversations-v1.jsonl`, `test_dataset_has_25_scenarios_in_five_slices_with_restart_points` |
| Stateful harness with replayable transcripts | Hands-on §1 | Exercise 4, drill 1 | `test_reference_agent_passes_every_scenario_and_v1_fails_13`, `test_harness_refuses_scenarios_without_restart_flags` |
| State and outcomes without exact wording | Theory §8 | `lab.py wording`, `lab.py invariance` | `test_state_checks_survive_rewording_and_exact_text_does_not`, `test_restart_invariance_separates_durable_state_from_memory` |
| Staff checkpoint: test persistence without brittle exact text matching | Theory §8, §11 Q1 | `lab.py wording` | Model answer in Theory §11 |

## Week 10: Faults, adversarial inputs, and handoffs

Files: [theory](weeks/week-10-faults-adversarial-and-handoffs/theory/week-10-faults-adversarial-and-handoffs-theory.md) · [hands-on](weeks/week-10-faults-adversarial-and-handoffs/handson/week-10-faults-adversarial-and-handoffs-handson.md) · [dataset](weeks/week-10-faults-adversarial-and-handoffs/dataset/README.md)

| Roadmap concept | Taught in | Practised in | Completion evidence |
|---|---|---|---|
| Timeouts and partial failure | Theory §3 | Exercise 1 | `test_giving_up_after_a_commit_tells_the_customer_a_false_failure` |
| Retries and idempotency | Theory §4, §6 | Exercises 1 and 5, drill 1 | `test_retry_after_timeout_after_commit_one_refund_with_stable_key_two_without`, `test_a_key_per_attempt_does_not_stop_a_retry_but_stops_a_redelivery` |
| Duplicate requests | Theory §5 | Exercise 2, `lab.py retry` | `test_strict_backend_hides_a_missing_key_behind_one_refund_per_order` |
| Prompt injection, direct and indirect | Theory §7 | Exercise 3, `lab.py report` | `test_poisoned_policy_is_retrieved_and_only_the_backend_stops_the_injectable_agent` |
| Malicious tool content and poisoned policy text | Theory §7 | Exercise 3 | `test_poison_is_added_per_run_and_the_shared_corpus_is_untouched` |
| Unauthorized orders | Theory §7, §9.1 | Exercise 4 | `test_dropped_identity_is_latent_on_an_own_order_and_critical_on_another_customers` |
| Agent routing and handoffs, local with no framework | Theory §8 | `lab.py handoffs` | `test_unaccepted_specialist_handoff_is_reported_honestly_only_by_the_reference` |
| Failed handoffs | Theory §9 | Exercise 4, drill 2 | `test_dropped_identity_is_latent_on_an_own_order_and_critical_on_another_customers` |
| Fault-injection suite and severity report | Theory §10 | `lab.py suite`, `lab.py report` | `test_reference_agent_is_clean_on_both_backends` |
| Ledger read-back proves one refund per retry | Theory §6 | `lab.py sweep` | `test_no_fault_schedule_gives_the_stable_key_agent_a_second_refund` |
| Staff checkpoint: a retry cannot create a second refund | Theory §6, §11 Q1 | Design review, `lab.py sweep` | The 14-run sweep: the stable-key agent stores at most 1 refund on both backends |

**Validation gaps, Phase 3.** Every agent is deterministic code standing in for a model, so the prompt-injection results describe these stand-ins, not any real model. Restarts run inside one Python process, and no test races two requests past the idempotency check. All labels are author-written by one annotator.

## Week 11: Evaluation harness and CI

Files: [theory](weeks/week-11-evaluation-harness-and-ci/theory/week-11-evaluation-harness-and-ci-theory.md) · [hands-on](weeks/week-11-evaluation-harness-and-ci/handson/week-11-evaluation-harness-and-ci-handson.md) · [dataset](weeks/week-11-evaluation-harness-and-ci/dataset/README.md)

| Roadmap concept | Taught in | Practised in | Completion evidence |
|---|---|---|---|
| Reproducibility | Theory §3 Reproducibility and pins | Exercise 3 | `test_workers_change_neither_the_results_nor_the_run_id` |
| Pinned datasets and policies | Theory §3 | Exercise 2, `lab.py pins` | `test_usage_and_pin_errors_exit_3_before_anything_runs` |
| CI artifacts and structured JSON results | Theory §4 The run artifact; Hands-on §1 The artifact | Exercise 1 | `test_artifact_round_trip_and_exit_codes`, `test_verify_rejects_tampered_missing_and_incomplete_artifacts` |
| Exit codes and blocking tests | Theory §5 Exit codes | `lab.py verify` | `test_artifact_round_trip_and_exit_codes` |
| Parallel runs | Theory §6 Parallel runs and isolation | Exercise 3, drill 1 | `test_workers_change_neither_the_results_nor_the_run_id` |
| Caching and cache separation | Theory §7 Caching | Drill 2 | `test_cache_hits_only_for_the_same_inputs`, `test_a_cache_key_without_the_agent_version_reports_v2_results_for_v1` |
| Budgets | Theory §8 Budgets | Exercise 4 | `test_budget_stops_admission_and_the_run_is_incomplete_not_passing` |
| Flaky results; a retry keeps the first failure | Theory §9 Flaky results; Theory §11.2 | Exercise 5, `lab.py flaky` | `test_a_retry_keeps_the_first_failure_and_the_case_is_flaky_not_pass`, `test_repeats_blame_the_evaluator_not_the_agent` |
| CI/CD workflow with opt-in live jobs | Theory §10 CI: blocking and opt-in jobs; Hands-on §1 The CI example | Exercise 6 | `test_ci_example_blocks_offline_and_keeps_paid_work_opt_in` |
| Staff checkpoint: diagnose a flaky LLM evaluation result | Theory §9, §11.2, §12 Q1 | Exercise 5 | Model answer in Theory §12 Q1; the 20-repeat report blames the evaluator, not the agent |

**Validation gaps, Week 11.** The CI workflow has never run on GitHub; only its structure is tested. Its live job calls Week 3's paid judge, which has not been run. The model-judged check is a seeded stand-in, so its flip rates describe the stand-in, not a real model.

## Week 12: Release gates

Files: [theory](weeks/week-12-release-gates/theory/week-12-release-gates-theory.md) · [hands-on](weeks/week-12-release-gates/handson/week-12-release-gates-handson.md) · [dataset](weeks/week-12-release-gates/dataset/README.md)

| Roadmap concept | Taught in | Practised in | Completion evidence |
|---|---|---|---|
| Hard and soft gates, verdicts | Theory §3 Hard gates, soft gates and verdicts | `lab.py scenarios` | `test_passing_candidate_ships_and_the_report_names_its_evidence`, `test_a_soft_gate_holds_for_a_named_owner` |
| Zero-tolerance safety violations | Theory §3.1, §4 The release run and the safety probe | Exercises 1 and 4 | `test_one_unauthorized_refund_blocks_a_candidate_with_the_baselines_pass_rate` |
| Quality thresholds | Theory §5 Quality thresholds | Exercise 3 | `test_a_slice_regression_blocks_although_the_average_clears_the_quality_gates` |
| Slice thresholds and paired baseline/candidate comparison | Theory §6 Paired comparisons and slice thresholds; Theory §10.1 | `lab.py gate` on v2.2 | Same test; flips name t-023 |
| Missing or invalid evidence, fail-open vs fail-closed | Theory §7 Evidence and missing inputs | Drills 1 and 2 | `test_every_evidence_problem_holds_and_none_ships`, `test_evidence_of_harm_outranks_missing_evidence`, `test_drill_1_a_gate_that_reads_a_missing_count_as_zero_ships_v2_3`, `test_drill_2_comparing_two_filtered_runs_to_each_other_ships_v2_2` |
| Acceptance policy, machine-readable | Theory §8 The acceptance policy as data; Hands-on §1 The policy | Exercises 2 and 3 | `dataset/release-policy-v1.json`, `test_policy_is_validated_and_a_bad_policy_is_a_usage_error` |
| Gate decision report | Hands-on §1 The decision report | Exercise 1 | `test_cli_gate_exit_codes` |
| Canary and rollback | Theory §9 Canary and rollback; Theory §10.3 | Exercise 6, `lab.py canary` | `test_canary_promotes_extends_and_rolls_back` |
| Staff checkpoint: why a single unauthorized refund blocks release | Theory §2, §3.1, §11 Q1 | Exercise 4 | Model answer in Theory §11 Q1; v2.3 is BLOCKED with pass rates equal to v2's |

**Validation gaps, Week 12.** Every threshold is illustrative. The canary metrics are hand-written and marked SIMULATED, and so are the rewritten other-policy and old-harness artifacts. Candidates v2.1 to v2.4 are deliberate deterministic variants of v2, not model outputs.

## Week 13: Tracing and online evaluation

Files: [theory](weeks/week-13-tracing-and-online-evaluation/theory/week-13-tracing-and-online-evaluation-theory.md) · [hands-on](weeks/week-13-tracing-and-online-evaluation/handson/week-13-tracing-and-online-evaluation-handson.md) · [runbook](weeks/week-13-tracing-and-online-evaluation/handson/week-13-tracing-and-online-evaluation-runbook.md) · [dataset](weeks/week-13-tracing-and-online-evaluation/dataset/README.md)

| Roadmap concept | Taught in | Practised in | Completion evidence |
|---|---|---|---|
| OpenTelemetry, traces and spans | Theory §3 Traces and spans; Theory §5 Context propagation | `lab.py trace`, exercise 1 | `test_ids_follow_w3c_trace_context_and_traceparent_round_trips`, `test_one_request_is_one_tree_of_openinference_spans_with_simulated_durations` |
| OpenInference conventions | Theory §4 OpenInference conventions | `lab.py trace`, `lab.py otel` | `test_one_request_is_one_tree_of_openinference_spans_with_simulated_durations`, `test_optional_opentelemetry_export_matches_or_reports_missing` |
| Instrumented retrieval, tool and model spans | Theory §3–4; Hands-on §1 | `lab.py trace` | `shared/tracing.py`; span-tree test above |
| Production quality: online checks without an answer key | Theory §6 Online checks without an answer key | `lab.py replay` | `test_online_checks_need_no_reference_and_catch_a_false_failure` |
| Alerts on refund failure rate | Theory §7 Alerts; Theory §7.1 | Exercise 3, drill 1 | `test_no_refund_page_before_the_deploy_and_drift_alerts_only_around_the_sale` |
| Rollback triggers | Theory §8 Rollback triggers | `lab.py replay --no-rollback`, exercise 4, runbook | `test_the_deploy_is_detected_and_rolled_back_and_the_counterfactual_is_worse` |
| Sampling, head and tail | Theory §9 Sampling | `lab.py sampling`, exercise 2 | `test_head_sampling_misses_failures_and_tail_sampling_keeps_them` |
| Feedback and drift | Theory §10 Feedback and drift; Theory §10.1 | `lab.py drift`, exercise 5 | Drift and feedback assertions in `test_no_refund_page_before_the_deploy_and_drift_alerts_only_around_the_sale` |
| Privacy and redaction | Theory §11 Privacy and redaction | `lab.py redaction`, drill 2 | `test_export_redacts_names_emails_card_numbers_and_customer_ids` |
| Trace-linked online dashboard | Theory §12 The dashboard and the runbook | `lab.py dashboard` | `test_dashboard_links_every_alert_to_an_exported_trace` |
| Operations runbook | Theory §12 | Exercise 4 | [Runbook](weeks/week-13-tracing-and-online-evaluation/handson/week-13-tracing-and-online-evaluation-runbook.md) |
| Staff checkpoint: offline benchmarks vs live production signals | Theory §6 table, §13 Q1 | Design review Q1 | Model answer in Theory §13 Q1 |

**Validation gaps, Week 13.** All traffic, latency and feedback are simulated by a seeded generator. The agents are deterministic stand-ins, so the incident describes them, not a real model. The OpenTelemetry SDK export ran with the in-memory exporter (`opentelemetry-sdk==1.45.2`); no OTLP collector or hosted tracing service has been used.

## Week 14: Multi-tenant governance

Files: [theory](weeks/week-14-multi-tenant-governance/theory/week-14-multi-tenant-governance-theory.md) · [hands-on](weeks/week-14-multi-tenant-governance/handson/week-14-multi-tenant-governance-handson.md) · [dataset](weeks/week-14-multi-tenant-governance/dataset/README.md)

| Roadmap concept | Taught in | Practised in | Completion evidence |
|---|---|---|---|
| Tenancy: silo, pool and bridge | Theory §3.1 Three ways to separate tenants | Design review Q2 | Model answer in Theory §12 Q2 |
| Tenant from identity, one enforcement point | Theory §3.2 The tenant comes from the identity | `lab.py demo`, drill 1 | `test_tenant_and_role_come_from_the_platform_not_the_caller`, `test_drill_1_trusting_the_callers_tenant_leaks_another_teams_run` |
| RBAC, least privilege, separation of duties | Theory §4 Roles and permissions | `lab.py access` | `test_access_matrix_follows_the_role_table` |
| Cross-tenant access denial, guessed IDs | Theory §5 Denials that do not leak; Theory §11.1 | `lab.py probe`, exercise 5 | `test_cross_tenant_probes_are_denied_and_look_like_missing_resources` |
| Dataset and evaluator registry, versioning, content hashes | Theory §6.1–6.2 | `lab.py registry` | `test_registry_entries_are_immutable_and_reads_check_the_hash`, `test_runs_pin_the_dataset_and_evaluator_hashes`, `test_a_metric_the_run_did_not_produce_fails_the_rule` |
| Shared evaluators, grants, namespace shadowing | Theory §6.3 Sharing a check without sharing control; Q3 | Exercises 2–3 | `test_a_shared_evaluator_can_be_used_but_not_changed_by_the_grantee` |
| Personal-data redaction before storage | Theory §7 Redaction before storage | `lab.py redaction` | `test_personal_data_is_redacted_before_anything_is_stored` |
| Audit logs: append-only, hash chain, anchor | Theory §8 The audit log; Theory §11.3; Q5 | `lab.py audit`, drill 2 | `test_the_audit_log_records_allowed_and_denied_actions_and_hides_other_tenants`, `test_the_chain_catches_a_deletion_and_only_the_anchor_catches_a_rewrite`, `test_deleting_the_newest_event_is_invisible_to_the_chain_alone` |
| Per-team attribution and budgets | Theory §9 Attribution and budgets; Theory §11.2; Q4 | `lab.py usage`, exercise 4 | `test_cost_is_charged_to_the_team_that_ran_the_evaluation`, `test_the_scripted_day_runs_every_team_and_denies_one_run_on_budget` |
| Staff checkpoint: tenant isolation and auditability trade-offs | Theory §10 Isolation and auditability trade-offs | Design review Q2, Q5 | Model answers in Theory §12 |

**Validation gaps, Week 14.** The platform is an in-process prototype on one SQLite file (the pool model). It has no network API and no real authentication: principals are trusted IDs from `tenants-v1.json`. There is no per-tenant encryption and no silo deployment. An action and its audit event are committed one after the other, not in one transaction. The lab holds the anchor in memory; no write-once store was used. Redaction covers fixed patterns and the names in `world.json`, so names of people outside the synthetic world would pass; structured `customer_id` fields stay as-is because they are synthetic test IDs. Teams, people, budgets and costs are fictional or simulated, and runs are Week 4's and Week 11's deterministic labs, not live models.

## Week 15: Reliable measurement and statistics

Files: [theory](weeks/week-15-reliable-measurement-and-statistics/theory/week-15-reliable-measurement-and-statistics-theory.md) · [hands-on](weeks/week-15-reliable-measurement-and-statistics/handson/week-15-reliable-measurement-and-statistics-handson.md) · [dataset](weeks/week-15-reliable-measurement-and-statistics/dataset/README.md)

| Roadmap concept | Taught in | Practised in | Completion evidence |
|---|---|---|---|
| Sources of variation: case sampling, run-to-run, evaluator | Theory §3 Where variation comes from | `lab.py repeat` | `test_simulation_is_seeded_labelled_and_independent_of_case_order`, `test_nothing_changed_and_the_numbers_still_move` |
| Confidence intervals | Theory §4 Confidence intervals for one pass rate; Theory §12.1 | Exercise 1, drill 2 | `test_wilson_interval_matches_the_hand_calculation`, `test_drill_2_a_wald_interval_claims_certainty_from_30_of_30` |
| Bootstrap resampling, explained before code | Theory §5 Bootstrap resampling; Hands-on §1 The bootstrap, before the code | `lab.py compare` | `test_bootstrap_is_reproducible_and_percentiles_take_the_middle` |
| Paired tests, pairing preserved | Theory §6 Paired comparisons; Theory §12.2 | `lab.py compare`, drill 1 | `test_paired_comparison_refuses_different_case_sets`, `test_drill_1_pairing_by_position_widens_the_interval_silently` |
| Sample-size limits and power | Theory §7 Sample size and power; Theory §12.3 | Exercises 2 and 4 | `test_sample_size_formulas_match_the_hand_calculation` |
| Repeated runs | Theory §8 Repeated runs | `lab.py compare --runs 20`, exercise 3 | `test_repeats_narrow_the_interval_but_twenty_still_touch_zero` |
| Judge calibration and human disagreement | Theory §9 Judge calibration and human disagreement | `lab.py agreement`, exercise 5 | `test_agreement_intervals_and_where_the_reviewers_split` |
| Segment drift and mix shift | Theory §10 Segments and drift | `lab.py segments`, exercise 6 | `test_segments_show_noise_and_the_mix_effect` |
| Reliability report with uncertainty | Theory §11 The reliability report | `lab.py report` | `test_report_is_written_with_its_label_and_verdict` |
| Staff checkpoint: a 2% gain from a noisy, underpowered test | Theory §2, §7.3, §13 Q1 | Design review Q1 | `test_the_two_point_gain_on_the_release_run_is_inconclusive`; model answer in Theory §13 Q1 |

**Validation gaps, Week 15.** Every pass and fail is simulated: the author chose per-slice probabilities and a case share, and seeded random numbers draw from them. The judge's spread is Week 11's seeded score, not a model, so this week has no measured run-to-run variation from a real model. Both review sheets are authored examples (`example-not-human-review`), so the kappa values test the method, not a judge. The seed was chosen so that run 0 shows the built-in 2-point gain; that run also has the fewest disagreeing cases of the 20, which makes its sample-size figure optimistic. The traffic mixes are Week 13's simulated ones.

## Week 16: Distributed evaluation capstone

Files: [theory](weeks/week-16-distributed-evaluation-capstone/theory/week-16-distributed-evaluation-capstone-theory.md) · [hands-on](weeks/week-16-distributed-evaluation-capstone/handson/week-16-distributed-evaluation-capstone-handson.md) · [ADR-001](weeks/week-16-distributed-evaluation-capstone/handson/week-16-distributed-evaluation-capstone-adr-001-lease-queue.md) · [ADR-002](weeks/week-16-distributed-evaluation-capstone/handson/week-16-distributed-evaluation-capstone-adr-002-tenant-fairness.md) · [runbook](weeks/week-16-distributed-evaluation-capstone/handson/week-16-distributed-evaluation-capstone-runbook.md) · [dataset](weeks/week-16-distributed-evaluation-capstone/dataset/README.md)

| Roadmap concept | Taught in | Practised in | Completion evidence |
|---|---|---|---|
| Queues and worker pools | Theory §3 Queues, workers and leases | Hands-on §1 The queue's API | `test_release_requests_get_the_week_12_verdicts_through_the_queue` |
| Leases, fencing tokens, at-least-once with idempotent completion | Theory §3.2–3.4; Theory §11.2; Q1 | `lab.py faults`, drill 1, ADR-001 | `test_a_crashed_worker_loses_no_job_and_charges_once`, `test_a_stalled_worker_cannot_overwrite_or_double_charge`, `test_every_finished_job_is_charged_exactly_once`, `test_drill_1_charging_inside_the_job_double_charges_a_retried_job` |
| Fault recovery: bounded retries, back-off, dead letters | Theory §4 Retries, back-off and dead letters | `lab.py faults`, exercises 2–3 | `test_a_poison_job_stops_after_three_attempts_and_the_run_is_recorded_unfinished` |
| Admission control, quotas, cost limits | Theory §5 Admission control and backpressure; Theory §11.1 | `lab.py demo`, exercises 5–6 | `test_admission_checks_role_budget_quota_and_duplicates`, `test_a_budget_check_without_reservations_admits_what_the_budget_cannot_cover` |
| Backpressure | Theory §5 | `lab.py demo` | `test_a_full_queue_refuses_new_work` |
| Fairness between tenants | Theory §6 Fairness between teams; Q3 | `lab.py compare`, exercise 4, ADR-002 | `test_fair_dispatch_protects_the_quiet_tenants_from_the_flood` |
| Sharding, merging evidence, unfinished runs recorded | Theory §7 Sharding and merging evidence; Q5 | Drill 2, exercise 7 | `test_sharded_runs_equal_the_single_process_runs`, `test_drill_2_merging_only_present_shards_hides_the_lost_case` |
| Traces, audit trail and dashboard | Theory §8 Observing the platform | `lab.py audit`, `lab.py dashboard` | `test_each_request_is_one_trace_across_the_queue`, `test_the_audit_log_records_each_request_and_the_chain_holds` |
| SLOs and capacity; prototype vs production numbers | Theory §9 SLOs and capacity; Theory §11.3; Q2, Q4 | `lab.py threads`, exercise 1, hands-on Performance and cost estimates | `test_the_slo_report_shows_what_fairness_cannot_fix`, `test_real_threads_finish_every_job_and_charge_each_once` |
| Capstone: architecture, 2 ADRs, runbook, demo, acceptance criteria | Theory §10 The capstone architecture | Hands-on Capstone acceptance criteria and Demo script | ADR-001, ADR-002, [runbook](weeks/week-16-distributed-evaluation-capstone/handson/week-16-distributed-evaluation-capstone-runbook.md) |
| Staff checkpoint: defend the architecture at review | Theory §12 Design review | Design review Q1–Q5 | Model answers in Theory §12 |

**Validation gaps, Week 16.** Workers run on a simulated clock; the thread trial is the only real concurrency, and it has no separate worker processes, network, heartbeats or autoscaling. The queue is one SQLite file: PostgreSQL `SKIP LOCKED` and managed queues are described, not run. The day's seconds and dollars are simulated from fixed per-case costs, and the scripted fault plan (crash, stall, poison) is authored. The thread trial is a wall-clock measurement on one machine, capped by SQLite's single writer, and is not a production capacity estimate; the production performance and cost estimate is a method with simulated inputs. Back-off has no jitter. Jobs shared between requests carry only the first request's trace context. Decision audit events are recorded under the submitter's identity, not a service principal. The queue calls private methods of Week 14's `Platform` (`_authorize`, `_audit`, `_resolve`), which a real service would expose as a public API. Capstone criterion 5 (canary and online monitoring) is evidenced by Weeks 12 and 13 and is not rerun through the queue. Queue, quota, budget and SLO thresholds are illustrative.
