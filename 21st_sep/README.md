# 21st Sep — working through the roadmap

Ten scaffold folders, one per level of
[`docs/study-guide/evaluation-roadmap.md`](../docs/study-guide/evaluation-roadmap.md).
Each holds that level's topics, its goal, a link to the notebook mapping and its exit checks,
copied from the roadmap, plus room for your own notebooks and notes.

**The roadmap is canonical.** These folders are a workspace, not a second source — they are not
rendered into [the site](https://eval-demystified.vercel.app) and nothing in `courses/`,
`docs/` or `labs/` links to them.

| # | Folder | Band | The question it answers |
|---|---|---|---|
| 0 | [`00-orientation/`](00-orientation/) | Beginner | Draw the taxonomy from memory and choose between a deterministic scorer and a judge without hesitating. Every follow-up later is a disguised version of *"which layer are you measuring?"* |
| 1 | [`01-rag-retrieval-and-generation/`](01-rag-retrieval-and-generation/) | Beginner | Separate a retrieval failure from a generation failure with numbers, and know the one failure no referenceless metric can see. |
| 2 | [`02-agents-tools-conversations-trajectories-outcomes/`](02-agents-tools-conversations-trajectories-outcomes/) | Intermediate | Hold three things apart — mechanics, process, outcome — and reach for the system of record before any judge. |
| 3 | [`03-ground-truth/`](03-ground-truth/) | Intermediate | Know where cases and labels come from on day one and by month three, and the two ways a dataset lies to you. |
| 4 | [`04-judges-and-the-humans-who-validate-them/`](04-judges-and-the-humans-who-validate-them/) | Intermediate | Build a judge three ways, catch it lying three ways, and know the only thing that licenses trusting it. |
| 5 | [`05-statistics-and-stratified-reporting/`](05-statistics-and-stratified-reporting/) | Advanced | Refuse to act on a number you cannot resolve, and never report an average that buries a segment. |
| 6 | [`06-the-release-gate-and-ci/`](06-the-release-gate-and-ci/) | Advanced | Turn metrics into a decision that can refuse a deploy, and put the cost of loosening it on a named line. |
| 7 | [`07-online-evaluation-and-the-loop/`](07-online-evaluation-and-the-loop/) | Advanced | Measure without an answer key, alert only on what you can resolve, and carry every finding back into a gated test. |
| 8 | [`08-safety-adversarial-and-multi-agent-attribution/`](08-safety-adversarial-and-multi-agent-attribution/) | Expert | Separate what must never happen from what should usually happen, test by attack surface rather than by example, and say which agent broke a multi-agent run. |
| 9 | [`09-the-harness-as-a-product/`](09-the-harness-as-a-product/) | Expert | Keep the evaluation system itself trustworthy and affordable — the layer above the metrics. |

Folder names are the roadmap's own anchor slugs with the `level-N` prefix replaced by a
zero-padded number, so `#level-4-judges-and-the-humans-who-validate-them` is
`04-judges-and-the-humans-who-validate-them/`.

## Order

Sequential — each level assumes the one before it. If you are short on time, the roadmap's
[fast paths](../docs/study-guide/evaluation-roadmap.md#fast-paths) name what to keep.

## Regenerating

These READMEs are copied from the roadmap. If the roadmap changes, they go stale silently —
re-run the generator rather than hand-editing them, and keep your own notes in separate files
so a regenerate cannot overwrite them.
