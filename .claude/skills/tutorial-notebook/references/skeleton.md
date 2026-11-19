# Annotated skeleton

A short notebook in the course 04 format, cell by cell. Comments in `<angle brackets>` are
instructions, not content. The topic here (scoring declines) is only an example.

---

**cell-00 · markdown**

```markdown
# 🚫 05 — Did It Decline Exactly When It Should?

<2 to 5 sentences. Name the failure in concrete terms first, then what this notebook does.>
An agent that answers a question its articles don't cover is inventing policy. An agent that
declines a question it could answer is useless. This notebook counts both mistakes on the saved
run, first with a plain string check, then with a judge, and compares the two.

## Learning Objectives
In this notebook, you will learn:
1. **Missed declines** - out-of-scope questions the agent answered anyway
2. **False declines** - answerable questions the agent refused
3. **A judge for declines** - when a string check is not enough, and what the judge costs

## Where this fits
Notebook 04 recorded one run of the agent over the golden set. This notebook reads that run
and scores one behaviour. Notebook 06 scores the tool calls from the same run.

## Prerequisites
- Notebook 04 run once: it records `data/golden_runs.json`
- `OPENROUTER_API_KEY` in the `.env` file at the repository root (only Part 3 calls a model)
```

**cell-01 · markdown**

````markdown
---
## 🗺️ The idea

Every out-of-scope case should end in the fixed decline sentence; every answerable case should not.

```
 golden case ──► saved answer ──► is it the decline sentence?
                                       │
                 out_of_scope ── yes ✅ / no ❌ missed decline
                 answerable  ── no ✅ / yes ⚠️ false decline
```

`adversarial` cases are not scored here: notebook 09 checks them against the safety rules.
````

**cell-02 · markdown**

```markdown
---
## ⚙️ Part 0: Setup
```

**cell-03 · code**

```python
# ============================================================================
# ENVIRONMENT SETUP: keys, models, the golden set and the recorded runs
# ============================================================================
import os
import tomllib
import json
from collections import Counter

from dotenv import load_dotenv

load_dotenv(os.path.join("..", "..", ".env"))
os.environ["LANGSMITH_TRACING"] = "false"   # nothing to trace: the agent doesn't run here

# Every model and provider comes from models.toml: change them there, not in the notebooks.
with open("models.toml", "rb") as f:
    MODELS_CONFIG = tomllib.load(f)

def model_config(role):
    """One role from models.toml, with its provider's base URL, key variable and key filled in."""
    ...   # <copied unchanged from the other notebooks; never imported>

RUNS_PATH = os.path.join("data", "golden_runs.json")
if not os.path.exists(RUNS_PATH):
    raise RuntimeError("No data/golden_runs.json. Run notebook 04 first: it records data/golden_runs.json.")

with open(os.path.join("data", "golden_set.json"), encoding="utf-8") as f:
    golden_set = json.load(f)
with open(RUNS_PATH, encoding="utf-8") as f:
    golden_runs = json.load(f)
runs_by_case = {run["case_id"]: run for run in golden_runs}   # join each case to its run

print("✅ Setup complete")
print(f"📄 {len(golden_set)} cases, {len(golden_runs)} runs")
```

**cell-04 · markdown**

```markdown
---
## ❌ Part 1: Missed declines

<2 to 5 sentences: what the check does, why it matters, what to look for in the output.>
The RAG prompt fixes one decline sentence, so a decline can be found by text alone. A missed
decline is the worse error: the agent has made up a policy the store does not have.

### Key Concepts:
- **Decline**: the fixed sentence the prompt asks for when the articles don't hold the answer
- **Missed decline**: an out-of-scope question that got an answer instead
```

**cell-05 · code**

```python
# ============================================================================
# MISSED DECLINES: out-of-scope answers that are not the decline sentence
# ============================================================================
DECLINE_TEXT = "I don't have information about that"

def is_decline(answer):
    return DECLINE_TEXT in answer   # the prompt fixes the wording, so a substring is enough

out_of_scope_runs = [run for run in golden_runs if run["slice"] == "out_of_scope"]
missed = [run for run in out_of_scope_runs if not is_decline(run["answer"])]

print(f"🧮 out of scope declined: {len(out_of_scope_runs) - len(missed)} of {len(out_of_scope_runs)}")
for run in missed:
    print(f"   ❌ missed decline {run['case_id']}: {run['answer'][:120]}")
print("Reading: every missed decline is an invented policy; one is enough to block a release.")
```

**cell-06 · markdown**: `## ⚠️ Part 2: False declines`, then the same pattern.

**cell-07 · code**: the same pattern.

**cell-08 · markdown**

```markdown
---
## ⚖️ Part 3: A judge for declines

<Why the string check stops being enough, which judge, what it costs.>

> **Key Insight:** a free check that is exact beats a paid judge; use the judge only where the
> wording varies.
```

**cell-09 · code**

```python
# ============================================================================
# JUDGED DECLINES: cached in data/decline_judgements.json
# ============================================================================
# ⏱️ About 40 judge calls with the Qwen3 judge: well under a cent a call.
CACHE_PATH = os.path.join("data", "decline_judgements.json")
if os.path.exists(CACHE_PATH):
    with open(CACHE_PATH, encoding="utf-8") as f:
        judgements = json.load(f)                  # delete the file to judge again
else:
    judgements = {}
    ...   # <call the judge at temperature=0, one case at a time>
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(judgements, f, indent=2)
print(f"🧮 {len(judgements)} answers judged")
```

**cell-10 · markdown**

```markdown
---
## 💾 Part 4: Save the scores

Each case's decline result goes into `data/agent_scores.json`, keyed by case ID with its
`run_id`, so notebook 12 can report it by slice. Other notebooks' fields in that file are kept.
```

**cell-11 · code**: load the file if it exists, update this notebook's fields, write it back,
then `print(f"💾 {len(records)} records → data/agent_scores.json")`.

**cell-12 · markdown**

```markdown
---
## 📝 Summary

In this notebook, we learned:

### 1. Missed declines
- A fixed decline sentence makes declines checkable for free
- A missed decline invents policy, so it is the error to gate on

### 2. False declines
- ...

### 3. A judge for declines
- ...

### Next Steps
- Notebook 06 scores the tool calls from the same run: right tool, right arguments, and no call when none is needed
```
