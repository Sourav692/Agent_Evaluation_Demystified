# Glossary

Each term is defined as this course uses it, with the week that introduces it. "Setup" means the [setup primer](setup.md).

| Term | Meaning | Introduced |
|---|---|---|
| A/A test | Running one version twice and comparing it with itself; any difference is noise. | Week 15 |
| Ablation | Removing one component of a version and rerunning the same evaluation, to measure what that component contributes. | Week 6 |
| Abstention | An answer that says it cannot answer and hands off, instead of guessing. | Week 5 |
| Acceptance policy | The release policy together with who may change it and who may approve a soft-gate failure. | Week 12 |
| Access-aware retrieval | Retrieval that applies the reader's permissions before the answer writer sees any text. | Week 5 |
| Adjudication | Resolving a reviewer disagreement through a third reviewer, the rubric owner, or evidence such as the ledger. | Week 15 |
| Admission control | Reserving budget for a case before it runs, and refusing the case when the budget cannot cover it. Week 14 refuses a whole run that would break the tenant's budget. Week 16 checks role, budget with reservations, quota, then capacity, before any work starts. | Week 11, Week 14, Week 16 |
| Adversarial case | A case written to make the agent break a rule, such as a message claiming a policy override. Its label is still what the policy says. | Week 2 |
| Agent | A program that uses a model to choose its next action, including which tools to call. | Setup |
| Agent version | A named, unchanging build of the agent. Weeks 1 to 3 use v1. | Week 1 |
| Alert window | The time span over which an alert's rate is computed. | Week 13 |
| Anchor | The audit head's sequence number and hash, kept outside the system holding the log. | Week 14 |
| Append-only | Events are added and never changed or removed. | Week 14 |
| Architecture decision record (ADR) | A short document recording one design decision, its options and its consequences. | Week 16 |
| Argument correctness | A call's argument values are right for the case: the order the customer meant, at its real amount. | Week 7 |
| Argument schema | The arguments a tool accepts, with their types and which are required. | Week 7 |
| At-least-once execution | Every job runs one or more times; leases give this guarantee. | Week 16 |
| Attribution | Recording which tenant caused each cost; the tenant that ran an evaluation pays for it. | Week 14 |
| Audit event | One record of an access decision: when, who, which tenant, what action, allowed or denied, why. | Week 14 |
| Authentication | Establishing who the caller is. The runtime holds the signed-in customer's verified ID. | Week 7 |
| Authorization | Deciding what an authenticated identity may do, checked by the backend on every call. | Week 7 |
| Back-off | Waiting longer before each retry after a failure. | Week 16 |
| Backpressure | Refusing new work when the system is full, with a signal to retry later. | Week 16 |
| Baseline | The version in production, which a candidate is compared against. | Week 6 |
| Binary score | A grade with two values, pass or fail. | Week 3 |
| Blocking job | A CI job whose failure stops the merge or release. | Week 11 |
| BM25 | A keyword scoring formula that rewards shared words, more for rare words, with diminishing returns and a length penalty. | Week 4 |
| Bootstrap | Estimating a statistic's variability by resampling the cases with replacement many times. | Week 15 |
| Bounded retry | A retry with a fixed maximum number of attempts. | Week 10 |
| Budget | The most a run may spend. Course budgets are in simulated dollars. | Week 11 |
| Cache key | A hash of every input that can change a case's result. A cached result is reused only when the key matches. | Week 11 |
| Calibration (judge) | Comparing a judge's grades with human labels, fixing the rubric or prompt, and comparing again. | Week 3 |
| Canary | A release to a small share of traffic, compared against the version still serving the rest. | Week 12 |
| Candidate | The version proposed to replace the baseline. | Week 6 |
| Capacity | The most active jobs the whole queue holds. | Week 16 |
| Capacity floor | Queued job-seconds divided by workers: the shortest possible wait in any order. | Week 16 |
| Case | One input plus its label: the message, the signed-in customer and the expected handling. | Week 1 |
| Case sampling | Variation in a result from which cases happen to be in the set. | Week 15 |
| Case type | Positive, negative, edge or adversarial. | Week 2 |
| Chance agreement (p_e) | How often two graders would agree if each kept its own pass rate but chose independently. | Week 3 |
| Check | A function that compares a run with a case's label and returns pass or fail with a reason. | Week 1 |
| Checkpoint | Saved conversation state from which a new process can continue. | Week 9 |
| Chunk | A passage cut from a document so it can be searched. By default, one policy section. | Week 4 |
| CI artifact | Files a CI job uploads for people and later jobs to read, such as `results.json`. | Week 11 |
| Citation support | The chunk cited for a claim actually contains that claim. | Week 5 |
| Claim mismatch | A reply whose claimed outcome disagrees with what the ledger holds. | Week 13 |
| Clarification question | A question asked because the agent cannot continue safely, such as 'Which order?'. | Week 9 |
| Code hash | One digest over the runner and every module a suite runs. It changes whenever the evaluated code changes. | Week 11 |
| Cohen's kappa | Agreement above chance: (p_o − p_e) / (1 − p_e). 1 is perfect, 0 is chance level. Week 15 adds a bootstrap interval and a second reviewer. | Week 3, Week 15 |
| Commit | The moment the backend makes a change permanent, here the ledger insert. | Week 10 |
| Comparable runs | Runs with the same case set, data hashes, policy version and full case list. Only these may be paired. | Week 12 |
| Complete run | A run whose completed cases equal its expected cases. An incomplete run cannot pass. | Week 11 |
| Concept vector | This course's stand-in for an embedding: counts of hand-listed concepts in a text. Tuned on the course's queries, so it flatters itself. | Week 4 |
| Confidence interval | A range from a method that contains the true value in the stated share (for example 95%) of repeated experiments. | Week 15 |
| Confused deputy | A component with authority that is tricked into using it for the wrong identity. | Week 10 |
| Confusion matrix | Counts of true positives, false positives, false negatives and true negatives for one yes-or-no question. | Week 1 |
| Contamination | See leakage. | Week 2 |
| Context carryover | Using an earlier turn's facts in a later turn. | Week 9 |
| Context propagation | Carrying the trace ID and parent span ID to the next operation. Across processes it travels in the W3C `traceparent` header. | Week 13 |
| Context size | The words sent to the answer writer, here the total words in the top k chunks. | Week 4 |
| Continuous integration and delivery (CI/CD) | Running builds and tests automatically on every change (CI), and releasing changes through an automated pipeline (CD). | Week 11 |
| Conversation state | What the agent must remember between turns: order in focus, pending question, candidates. | Week 9 |
| Corpus | The documents an agent can search. Here, 7 help-centre documents. | Week 4 |
| Correctness | Whether the agent did the right thing: decision, tool calls, order of steps. | Week 1 |
| Cross-field rule | A validation rule that spans several fields, such as "a requester who does not own the order must be labeled `access_denied`". | Week 2 |
| Cross-session leakage | State from one customer's session reaching another session. | Week 9 |
| Dataset version | A name for one exact set of records, such as `refund-cases-v1`, pinned by a manifest. | Week 2 |
| Dead letter | The terminal state of a job that used up its attempts, kept for a person to inspect. | Week 16 |
| Decision report | The verdict plus every rule's result and evidence pointers. | Week 12 |
| Defense in depth | Several independent controls, each able to stop the failure alone. | Week 10 |
| Deterministic check | A check that always gives the same verdict for the same case and run. | Week 1 |
| Development split | Cases you study while improving the agent. | Week 2 |
| Digression | An off-task turn after which the conversation returns to the task. | Week 9 |
| Discordant case | A case where one version passed and the other failed; only these carry evidence about the change. | Week 15 |
| Duplicate delivery | The same tool call reaching the backend twice. | Week 10 |
| Durable state | State in storage that outlives the process. | Week 9 |
| Edge case | A case on a rule boundary, such as day 30 or exactly $500.00. Written in pairs, one each side. | Week 2 |
| Efficiency | 1 minus the share of a trace's calls that are redundant. | Week 8 |
| Embedding | A list of numbers standing for a text's meaning. Similar meanings get nearby vectors, compared by cosine similarity. | Week 4 |
| Enumeration | Discovering what exists by trying many IDs and watching which answers differ. | Week 14 |
| Evaluator variation | Change in a verdict when the same output is graded again; zero for deterministic checks. | Week 15 |
| Evidence | The chunks the answer writer received for a question. | Week 5 |
| Evidence pointer | A run ID, path or case ID that lets a person check a rule's result. | Week 12 |
| Exact / in-order / any-order match | Same sequence / the reference in order with extras allowed / every reference tool present in any order. | Week 8 |
| Exact-text check | Comparing replies word for word with a recorded transcript. | Week 9 |
| Exit code | The number a program returns when it finishes. Zero means success. | Setup |
| F1 | The harmonic mean of precision and recall: 2PR / (P + R). | Week 1 |
| Fail closed | Treating bad or unreadable input to a check as a failure, never as a silent pass. | Week 1 |
| Fail open | Treating a rule that cannot be evaluated as passed. The opposite of fail closed. | Week 12 |
| Failure taxonomy | A fixed list of failure categories and severities used to count failures consistently. | Week 1 |
| Faithfulness | Every claim in an answer is supported by its evidence. Says nothing about whether the evidence was right. | Week 5 |
| False negative (FN) | A positive the system missed. For refund decisions: an owed refund not issued. | Week 1 |
| False positive (FP) | A negative the system flagged as positive. For refund decisions: a refund issued that was not owed. | Week 1 |
| Fan-out and fan-in | Splitting a request into jobs, then combining their results. | Week 16 |
| Fault injection | Making a dependency fail on purpose to see how the system behaves. | Week 10 |
| Fencing token | A token that storage checks so a writer whose claim was superseded cannot write. | Week 16 |
| Filter violation | A superseded or internal chunk in the top k. | Week 4 |
| Fingerprint | A short hash of a case's tool calls, outcome and stored refunds. Equal fingerprints mean the agent behaved the same way. | Week 11 |
| Flaky result | A verdict that changes between runs with the same inputs. | Week 11 |
| Flip | A case whose verdict changed between baseline and candidate. | Week 12 |
| Forbidden fact | A phrase a correct answer must never contain, checked on every case. | Week 5 |
| Forbidden step | A mutation the case does not allow, or a lookup of another customer. | Week 8 |
| Gold section | A policy section that answers a question. | Week 5 |
| Gold-context swap | Rerunning a failing case with only its gold sections as evidence. Passing means retrieval caused the failure. | Week 6 |
| Graded relevance | A usefulness score per passage: 3 answers, 2 needed context, 1 related, 0 unlabeled. | Week 4 |
| Grant | An owner's permission for another tenant to read and run one evaluator, not to change it. | Week 14 |
| Ground truth | The correct handling of a case, as defined by an authority you trust. Here, the refund policy. | Week 2 |
| Guardrail | A live metric with a limit the canary must stay inside. | Week 12 |
| Hallucination | A claim the evidence does not support, true or false. | Week 5 |
| Handoff | Passing a request and its context from one agent to another. | Week 10 |
| Handoff contract | The required handoff fields: verified customer ID, order ID and reason. | Week 10 |
| Hard failure | A broken safety invariant. One fails the case, whatever else went right. | Week 8 |
| Hard gate | Any hard failure sets the gated score to 0 and the verdict to HARD FAIL. In a release policy (Week 12), a rule whose failure blocks the release with no override. | Week 8, Week 12 |
| Hard negative | A passage that looks right and isn't, such as the superseded refund policy. | Week 4 |
| Hash (SHA-256) | A fixed-length fingerprint of a file's bytes. Any edit changes it. | Week 2 |
| Hash chain | Each audit event's hash covers the previous event's hash, so an edit or gap breaks later links. | Week 14 |
| Head sampling | Deciding whether to keep a trace when it starts, from its trace ID alone. | Week 13 |
| Hit Rate@k | 1 if any top-k chunk is relevant, else 0, averaged over queries. | Week 4 |
| Holdout split | Cases used only to decide whether a version ships. Also called the test set. | Week 2 |
| Hybrid retrieval | Combining keyword and vector rankings, here by reciprocal rank fusion. | Week 4 |
| Idempotency key | An ID a caller sends with a mutation so the backend can recognize a retry and return the stored result. | Week 7 |
| Idempotent completion | Reporting a job twice has the effect of reporting it once: one result, one charge. | Week 16 |
| Idempotent operation | Same effect whether it runs once or many times. | Week 10 |
| Indirect injection | An instruction inside content the agent reads, such as a retrieved policy chunk. | Week 10 |
| Indistinguishable denial | The same answer for "missing" and "exists but forbidden". | Week 14 |
| Input drift | A change in what customers send, such as the mix of request topics. | Week 13 |
| Inter-rater agreement | Kappa between two human reviewers; the ceiling for a judge's agreement. | Week 15 |
| Invalid response | A judge response that cannot be read or whose evidence fails checks. Never counted as a pass. | Week 3 |
| Invariant | A condition every acceptable trajectory satisfies, such as ownership established before any mutation. | Week 8 |
| Isolation (case) | Each case starts from its own fresh state, so no case can see another's side effects. | Week 11 |
| Job | One unit of scheduled work; here one shard of up to 10 cases, with an ID that hashes the work. | Week 16 |
| JSON Lines | A file format with one JSON object per line. | Setup |
| Label | The expected part of a case, written down before the agent runs. | Week 1 |
| Latent failure | A bug that gives the right outcome on today's cases and the wrong one on an untested case. | Week 10 |
| Lax backend | A tool backend that trusts the agent. Shows what the agent would do if nothing stopped it. | Week 7 |
| Leakage | Any path by which holdout information reaches the agent or the people tuning it. | Week 2 |
| Lease | A worker's time-limited claim on a job; it expires if the worker does not report. | Week 16 |
| Lease token | A number raised on every lease; a completion must carry the current one. | Week 16 |
| Least privilege | Each role gets only the permissions its work needs. | Week 14 |
| Ledger | The SQLite refund store, the system of record for refunds. | Week 7 |
| Manifest | A file recording a dataset's version, policy version, and each split's path, case count and hash. | Week 2 |
| McNemar's test | A paired test that treats the discordant split as fair coin flips. | Week 15 |
| Metadata filter | A rule sent with a search, such as current policy and public audience only, that limits which chunks can come back. | Week 4 |
| Metamorphic test | Testing a property by comparing two runs of the system with each other instead of with labels. | Week 9 |
| Minimum detectable effect | The smallest difference a comparison of a given size detects with the chosen power. | Week 15 |
| Minimum volume | The least traffic a window needs before its alert may fire. It stops a few requests from paging someone. | Week 13 |
| Mix shift | A change in the segment shares of traffic, with each segment's rate unchanged. | Week 15 |
| Model call | Sending a prompt to a language model through an API and receiving generated text. | Setup |
| Model judge | A model that grades a reply against a rubric. Also called LLM-as-a-judge. | Week 3 |
| MRR | Mean reciprocal rank: the average of 1 / rank of the first relevant chunk. | Week 4 |
| Mutation | A state-changing call: create_refund or escalate_to_specialist. | Week 8 |
| Namespace | The tenant prefix that makes a registry name unique, as in trust-safety/refund-safety. | Week 14 |
| nDCG@k | Normalized discounted cumulative gain: graded, rank-discounted gain divided by the best possible gain. Each labeled section is credited once. | Week 4 |
| Negative case | A case where the agent should refuse, escalate or ask for more information. | Week 2 |
| Noisy neighbour | A tenant whose load degrades service for others on shared infrastructure. | Week 16 |
| Normalization | Lower-casing text and removing punctuation and extra spaces before comparing, so trivial edits still match. | Week 2 |
| Offline evaluation | Running fixed labeled cases before a release. | Week 1 |
| Online evaluation | Watching live traffic after a release, usually without labels. | Week 1 |
| OpenInference | Semantic conventions for AI spans built on OpenTelemetry. They name span kinds such as AGENT, TOOL, RETRIEVER and LLM and the attributes each carries. | Week 13 |
| OpenTelemetry | An open standard and set of SDKs for traces, metrics and logs. Its trace data model is spans linked into traces. | Week 13 |
| Order dependence | A result that changes when the same cases run in a different order. A sign of shared state. | Week 11 |
| Ordinal score | A grade with ordered but unevenly spaced levels, such as 1 to 5. | Week 3 |
| Over-constraining | Rejecting a valid plan because it differs from the reference in a step that does not matter. | Week 8 |
| p50 / p95 latency | The response time half of requests beat / that 95% beat. | Week 6 |
| Paired bootstrap | Resampling case IDs and carrying both versions' results with each one. | Week 15 |
| Paired comparison | Two versions run on the same cases, compared case by case. | Week 6 |
| Pairwise comparison | A judge picks the better of two replies to the same message. | Week 3 |
| Partial credit | Weighted credit for required steps, task success and efficiency. | Week 8 |
| Partial failure | Some steps of a task took effect and others did not. | Week 10 |
| Pass rate | The share of repeated runs in which a case passed. | Week 11 |
| Percent agreement (p_o) | The share of items where two graders gave the same verdict. | Week 3 |
| Percentile interval | The middle 95% of the sorted bootstrap values. | Week 15 |
| Permission | One action on one kind of resource, such as dataset.read or evaluator.write. | Week 14 |
| Personal data | Anything that identifies a person: names, emails, card numbers, customer IDs. | Week 14 |
| Poison job | A job that fails on every worker every time. | Week 16 |
| Position bias | A judge's preference for the reply shown first or second, regardless of content. | Week 3 |
| Positive case | A case where the agent should complete the task, such as an owed refund. | Week 2 |
| Positive class | The answer a metric counts as "positive", such as "a refund is issued". | Week 1 |
| Power | The chance of detecting a real effect of a given size, for example 80%. | Week 15 |
| Precision | Of everything flagged positive, the share that was right: TP / (TP + FP). | Week 1 |
| Precision@k | The share of the top k chunks that are relevant at all. | Week 4 |
| Principal | An identity that makes a request; the platform's policy maps it to one tenant and one role. | Week 14 |
| Probabilistic check | A check whose verdict can vary on the same input, such as a model judge. | Week 1 |
| Prompt injection | Text in user input, or in content the agent reads, that tries to override the agent's instructions. | Week 1 |
| Pseudo-replication | Treating repeated runs of the same case as new cases; it makes intervals too narrow. | Week 15 |
| Pseudonym | A salted hash standing in for an identifier, so traces can be joined without exposing it. | Week 13, Week 14 |
| Quality | How well a reply is written: clear, polite, complete, on topic. Separate from correctness. | Week 1 |
| Quality drift | A change in how well the agent handles requests, seen in checks and outcomes. | Week 13 |
| Quality gate | A minimum rate the candidate must reach, such as task completion of at least 0.95. | Week 12 |
| Query rewriting | Changing the customer's wording before search, such as mapping 'money back' onto 'refund'. | Week 6 |
| Queue | The table of jobs waiting for workers, with each job's state. | Week 16 |
| Quota | The most active jobs one team may have at once. | Week 16 |
| Read-back | Querying the system of record directly after a run, instead of trusting the agent's account. | Week 7 |
| Recall | Of all actual positives, the share that was flagged: TP / (TP + FN). | Week 1 |
| Recall@k | The share of labeled sections that some top-k chunk covers. | Week 4 |
| Reciprocal rank fusion (RRF) | A hybrid method scoring each chunk by the sum of 1 / (60 + rank) across the fused rankings. | Week 4 |
| Redaction | Masking personal data before a trace or log leaves the process. Week 14 adds identity-aware redaction at the registry write. | Week 13, Week 14 |
| Redaction before storage | Masking personal data inside the write path, then checking the stored bytes. | Week 14 |
| Redundant call | A read identical to an earlier one with no mutation in between. | Week 8 |
| Reference (ref) | The full name of one registry entry, tenant/name@vN. | Week 14 |
| Reference answer | A correct answer written before the run, with the facts it must and must not contain. | Week 5 |
| Reference trajectory | One known-good path for a case, kept as a diff aid, not as the only acceptable path. | Week 8 |
| Reference-based grading | Judging with the correct answer or expected outcome in the prompt. | Week 3 |
| Reference-free check | An online check that compares the system's own records, such as reply against ledger, and needs no expected answer. | Week 13 |
| Reference-free grading | Judging without the correct answer, from the input, the reply and context such as the policy. | Week 3 |
| Refund failure rate | Failed refund attempts divided by refund attempts, within one alert window. | Week 13 |
| Registry | Catalogue of datasets and evaluators with owner, version and content hash for each entry. | Week 14 |
| Regression gate | A limit on how much worse the candidate may be than the baseline on the same cases. | Week 12 |
| Release gate | The automated decision whether a candidate may go to production. | Week 12 |
| Release policy | The versioned rules a gate applies, kept as data rather than code. | Week 12 |
| Release run | The suite run on the strict backend, the configuration production uses. | Week 12 |
| Relevance label | A person's judgment of how useful a passage is for a query, written before any retriever runs. | Week 4 |
| Representative dataset | A dataset whose mix covers common traffic well and oversamples rare, harmful situations. | Week 2 |
| Required fact | A phrase a correct answer must contain, checked on cases that expect an answer. | Week 5 |
| Required step | A call that must appear and succeed on the target order, in any position. | Week 8 |
| Reranking | Re-sorting the first search results with a second, slower scorer. | Week 6 |
| Reservation | An upper estimate of a run's cost, checked against the budget before the run starts. Week 16 holds it from admission until the job finishes. | Week 11, Week 14, Week 16 |
| Restart | The agent process stops and a new one starts. Memory-only state is lost. | Week 9 |
| Restart invariance | Restarting between turns changes nothing the agent does. | Week 9 |
| Restricted source | An internal document cited in a customer answer. Critical. | Week 5 |
| Retrieval drift | Retrieval results changing over time because the corpus, the query mix or a model changed. | Week 6 |
| Retrieval-augmented generation (RAG) | Retrieving relevant passages from your documents and giving them to the model with the question. | Setup |
| Retriever | The search step that ranks chunks for a query. | Week 4 |
| Retry policy | What the harness does after a failed attempt: how many more attempts, and how it reports them. | Week 11 |
| Reweighting | Recomputing an overall rate from segment rates under a different mix. | Week 15 |
| Role-based access control (RBAC) | Permissions attached to roles, and one role per principal. | Week 14 |
| Rollback | Routing all traffic back to the previous version. | Week 12 |
| Rollback trigger | A rule on live signals that restores the previous version. | Week 13 |
| Root span | A request's first span, the one with no parent. | Week 13 |
| Round robin | Giving the next free worker to the team served least recently. | Week 16 |
| Routing | Deciding which agent handles a request. | Week 10 |
| Rubric | The written grading standard: what earns each verdict and each score level. | Week 3 |
| Run | Everything the agent produced for one case: decision, reply and trace. | Week 1 |
| Run artifact | The files a run leaves behind, here `results.json` and `checksums.json`. | Week 11 |
| Run ID | An identifier hashed from a run's settings and versions. The same ID must give the same case records. | Week 11 |
| Run-to-run variation | Change in a result when the same version reruns the same cases. | Week 15 |
| Safety | The part of correctness that must never fail, such as refunding another customer's order. Reported separately from averages. | Week 1 |
| Safety probe | The suite run on the lax backend, to show what the agent alone would store. | Week 12 |
| Schema | The required fields of a record, with their types and allowed values. | Week 2 |
| Scorecard | One table comparing versions on quality, safety, cost and latency. | Week 6 |
| Segment drift | A change in one segment's own pass rate. | Week 15 |
| Self-enhancement bias | A judge's preference for replies written by its own model. | Week 3 |
| Separation of duties | Splitting powers so no role can both define a check and pass it, or both act and hide it. | Week 14 |
| Service-level indicator (SLI) | A measured quantity, such as the time from submission to release decision. | Week 16 |
| Service-level objective (SLO) | A target for an SLI, such as every release decision within 300 s. | Week 16 |
| Session | One conversation between one signed-in customer and the agent, named by a session ID. | Week 9 |
| Session key | What locates a conversation's state, here (authenticated customer ID, session ID). | Week 9 |
| Severity | The size of the harm if a failure reaches a customer: minor, major or critical. | Week 1 |
| Severity report | All findings, critical first, with counts per agent and backend. | Week 10 |
| Shadow evaluator | A same-named evaluator in the caller's own namespace that a short reference resolves to. | Week 14 |
| Shard | A slice of a run's cases that one job evaluates. | Week 16 |
| Side effect | A lasting change a tool call makes, such as a stored refund. | Week 7 |
| Silo, pool and bridge | Tenancy models: separate stacks per tenant, shared tables with a tenant column, or shared logic with separate storage. | Week 14 |
| Simulated | Computed from illustrative constants, not measured. Shows the shape of a trade-off, not its size. | Week 6 |
| Slice | A group of cases sharing one condition, such as "damaged but outside the window". | Week 1 |
| Slice risk | The highest risk label among a slice's cases. It sets the slice's tolerance. | Week 12 |
| Soft gate | A rule whose failure holds the release until a named owner approves it. | Week 12 |
| Span | The record of one operation inside a request: name, start and end times, status, parent and attributes. | Week 13 |
| Stable ID | A case ID that never changes and is never reused. | Week 2 |
| Stable key | An idempotency key derived from the request, the same on every attempt. | Week 10 |
| Stale source | A superseded policy cited in an answer. | Week 5 |
| Standard error | The typical distance between an estimate and the true value across repeated samples. | Week 15 |
| Starvation | A team's work waits indefinitely because other work is always chosen first. | Week 16 |
| State check | A check on outcomes, the order in focus, tool calls and the ledger, never on wording. | Week 9 |
| Strict backend | A tool backend that enforces identity, ownership, eligibility and amounts on every call. | Week 7 |
| System of record | The store that holds the truth about side effects, here the refund ledger. | Week 7 |
| Tail sampling | Deciding whether to keep a trace after it ends, from what happened, so every error can be kept. | Week 13 |
| Task success | The ledger and events match the case, and the claimed outcome is acceptable. | Week 8 |
| Temperature | A model setting that controls how much its output varies between calls. | Setup |
| Tenant | A team whose data, checks, runs and spending a shared platform keeps apart from other teams'. | Week 14 |
| Tenant isolation | No customer sees or acts on another customer's data. On the evaluation platform, no team reads, changes or spends another team's resources without that team's grant. | Week 9, Week 14 |
| Time to detect | From a deploy to its first alert. | Week 13 |
| Time to mitigate | From a deploy to the rollback or fix that stops the harm. | Week 13 |
| Timeout before / after commit | The call gave up before / after the refund was stored. The caller sees the same error either way. | Week 10 |
| Token | The unit models read, write and bill by, roughly three-quarters of an English word. | Setup |
| Tolerance | The largest slice decline the policy accepts. | Week 12 |
| Tool | A function an agent can ask its program to run, such as `create_refund`. | Setup |
| Tool response | What a tool call returned: data, or an error such as not_eligible. | Week 7 |
| Top k | The k highest-ranked chunks a retriever returns. | Week 4 |
| Total variation distance | Half the summed absolute difference between two distributions. Week 13's drift score. | Week 13 |
| Trace | The ordered list of tool calls, with arguments, that an agent made during a run. From Week 13, also the OpenTelemetry sense: every span of one request, linked by parent span IDs. | Setup, Week 1, Week 13 |
| Trace grading | Checking a trajectory from its trace, including arguments, responses and errors, not the reply. | Week 8 |
| Traffic share | The share of requests the canary serves. | Week 12 |
| Trajectory | The ordered steps (tool calls) an agent took for one request. | Week 8 |
| True negative (TN) | A negative correctly left unflagged. | Week 1 |
| True positive (TP) | A positive correctly flagged. | Week 1 |
| Trust boundary | The line between input the system controls and input it does not. | Week 10 |
| Turn | One customer message and the agent's response. | Week 9 |
| Utilisation | The share of worker time spent running jobs. | Week 16 |
| Verbosity bias | A judge's preference for longer replies even when the extra length adds nothing. | Week 3 |
| Verdict | The gate's decision: SHIP, BLOCK or HOLD. | Week 12 |
| Version pin | The recorded identity of everything that affects a result: dataset, corpus, configuration and writer. | Week 6 |
| Wald interval | Estimate ± 1.96 standard errors; it collapses to zero width at 0% or 100%. | Week 15 |
| Wilson interval | An interval for a proportion that stays within 0–100% and is never zero-width. | Week 15 |
| Worker | One of several threads or processes running cases at the same time. | Week 11 |
| Worker pool | The processes that lease and run jobs. | Week 16 |
