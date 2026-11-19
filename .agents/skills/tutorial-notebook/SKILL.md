---
name: tutorial-notebook
description: Create or rewrite a Jupyter teaching notebook in the educational format of courses/04-end-to-end-eval-tutorial - a title cell with objectives and prerequisites, a "The idea" cell, numbered Parts that each teach one concept, banner-commented code cells that always print a result plus a "Reading:" line, paid steps cached to data/, file handoffs between notebooks, and a summary that names the next notebook. Use when asked to write, add or restyle a course notebook "like course 04", or to turn a script or topic into a tutorial notebook.
---

# Tutorial notebook

Write notebooks that teach one idea at a time to someone who has not seen it before, using the
house format of `courses/04-end-to-end-eval-tutorial/`. The format is fixed. The topic, the
number of Parts and the emoji adapt.

This skill extends the `format-notebook` skill (sourav-skills plugin) and agrees with it on the
title cell, banners, import order, output emoji and summary. Where they differ, follow this file:
it records how course 04 actually does it.

## Before writing

1. Read two notebooks from `courses/04-end-to-end-eval-tutorial/`: the one before the new
   notebook in the sequence, and `06_tool_call_evaluation.ipynb` as the format reference.
2. Read the target folder's `README.md` and the repo `CLAUDE.md`: they set the environment, the
   kernel, which libraries are allowed and whether outputs are committed.
3. Write down, before any cell, the 3 to 5 things the learner will be able to do. Each becomes
   one learning objective and one Part. If an idea doesn't fit an objective, leave it out.
4. List what the notebook reads from `data/` and what it writes there, and which notebook
   produces each input.

Never execute a notebook that calls a paid API unless the user asks. Write it, check it
statically, and say it has not been run.

## The skeleton

See `references/skeleton.md` for a complete annotated example. In order:

| Cell | Type | Content |
|---|---|---|
| Title | markdown | `# <emoji> NN — <Title>`, a 2 to 5 sentence opening, `## Learning Objectives`, optional `## Where this fits`, `## Prerequisites` |
| The idea | markdown | `---`, `## 🗺️ The idea`: the whole notebook in one picture, a text diagram or a table, before any code |
| Setup | markdown + code | `## ⚙️ Part 0: Setup`, one sentence, then the setup cell |
| Helpers | code (optional) | Small reporting helpers this notebook repeats, defined once near the top |
| Parts 1..N | markdown + code | One `## <emoji> Part N: <Title>` per objective, sub-steps as `### N.M <emoji> <Title>` |
| Save | markdown + code | `## 💾 Part N: Save ...` when the notebook hands results on |
| Summary | markdown | `## 📝 Summary`, one `### N. <Title>` per Part, then `### Next Steps` |

### Title cell

```markdown
# 🔧 06 — Tool-Call Evaluation

<2 to 5 sentences: the problem in concrete terms, what this notebook does about it.>

## Learning Objectives
In this notebook, you will learn:
1. **Tool selection** - did the agent call the tools the case expects, and no others?
2. ...

## Where this fits
<2 or 3 sentences: what the previous notebook produced, what this one adds, what comes next.>

## Prerequisites
- Notebooks 01 and 04 run once: they build `data/chroma_db/` and record `data/golden_runs.json`
- `OPENROUTER_API_KEY` ... in the `.env` file at the repository root
```

- One emoji in the H1. The number is the file's two-digit prefix, joined with an em dash.
- Objectives: bold term, ` - `, one line saying what the learner can do or answer.
- Prerequisites name earlier notebooks by number and the exact files they write.

### The idea cell

Show the whole mechanism before any code. Use a fenced text diagram or a table that maps each
check or step to the question it answers and the tool that does it. Say what is out of scope
and which notebook covers it ("`adversarial` cases ... are not scored here; notebook 09 checks them").

### Markdown before every code section

Every `##` heading starts with `---` on its own line. After the heading, 2 to 5 sentences: what
the code below does, why it matters, and what to look for in the output. Then optionally:

- `### Key Concepts:` with `- **Term**: definition` bullets, when a Part introduces several terms.
- `> **Key Insight:** ...` for the one sentence to remember.
- `> **Note:** ...` for a caveat, a version quirk or a known gap.
- `> **Why this matters for evaluation:** ...` to link a build step to the notebook that scores it.

Split failures and outcomes into named kinds with a bullet each ("**Missing**: ...", "**Extra**: ...")
and say how they differ in meaning, not only in count.

### Code cells

Every code cell starts with a banner:

```python
# ============================================================================
# TOOL SELECTION: called tool names = expected tool names
# ============================================================================
```

- The banner title is UPPER CASE; after the colon, plain words or the rule being checked.
- Use `# --- SUB-STEP` lines to separate blocks inside a long cell.
- Comment only the why, on the same line where possible: `return value.lower()      # emails are not case-sensitive`.
- One concept per cell. Split computing from reporting when both are long (`... : the two versions side by side`).
- Descriptive names in full words (`expected_names`, `runs_by_case`), never `df`, `res`, `tmp`.
- Prefer plain Python first, then the library that does the same thing, then compare them
  ("our check vs DeepEval's"). Teaching the mechanism before the library is the house pattern.

### Every cell prints something

End each cell with a result, a count or a confirmation. Output prefixes:

| Prefix | Use |
|---|---|
| `✅` | step done: `print("✅ Setup complete")`, `print("✅ Helper ready")` |
| `📄` | counts of loaded files or records |
| `🔍` | search results, a case looked at closely |
| `🧮` | computed scores and rates |
| `⚠️` | a warning or a borderline case |
| `❌` | a failure being listed |
| `🔑` / `📈` | keys present (True/False only, never the value); where traces go |
| `💾` | file written, with its path |

Indent listed items with three spaces. Align columns with f-string widths (`{slice_name:<14}`).

After a result that needs interpreting, add one line that starts with `Reading:` and says what
the number means:

```python
print("Reading: a missed decline is the worse error; it means the agent invents policy.")
```

### The setup cell

One code cell that, in this order:

1. Imports: standard library, then third-party, then LangChain/LangGraph, grouped with blank lines.
2. `load_dotenv(os.path.join("..", "..", ".env"))` (the root `.env`, two folders up).
3. Telemetry and tracing switches, each with a comment (`os.environ["LANGSMITH_TRACING"] = "false"   # nothing to trace here`).
4. Models from `models.toml` through a `model_config(role)` helper, repeated in each notebook.
   Never name a model, base URL or key inline.
5. Input files from `data/`. If one is missing, raise with the notebook that writes it:
   `raise RuntimeError("No data/golden_runs.json. Run notebook 04 first: it records data/golden_runs.json.")`
6. A `✅` line and a `📄` line with the counts loaded.

### Notebooks stand alone

- No shared modules. Helpers are copied into each notebook that needs them, on purpose. When a
  notebook needs the app under test, paste the whole app into one cell under the banner
  `THE APP UNDER TEST: notebook NN's <app>, in one cell`, with a comment naming its source Part.
- State passes between notebooks only through files in `data/`. Say in markdown which notebook
  reads each file this one writes.
- When results are merged into a shared file, load it if it exists, update this notebook's
  fields per record and write it back, so other notebooks' fields survive.

### Paid calls

- Put a cost and size comment at the top of any cell that calls a model:
  `# ⏱️ About 35 judge calls with the Qwen3 judge: well under a cent a call.`
- Cache expensive results: if the output file exists, load it; otherwise run and save. Say so in
  the markdown ("if that file already exists, it is loaded instead, so the run is never paid for
  twice"). Note that deleting the file re-runs it.
- Judges run at `temperature=0` and come from a different model family than the app.

### Summary cell

```markdown
---
## 📝 Summary

In this notebook, we learned:

### 1. Deterministic tool checks
- **Selection**: the set of called tools against the set expected; missing and extra mean different things
- ...

### Next Steps
- Notebook 07 looks at the whole path: the order of the calls, the route the supervisor chose, ...
```

One `###` per Part with 1 to 3 takeaway bullets, not a replay of the steps. `### Next Steps`
names the next notebook and the one thing it adds.

## Voice

- Plain English for a newcomer. Short sentences. Define every term in bold the first time it
  appears, then use the same word every time.
- Concrete examples from the course's own data (a real case ID, a real order, a real number),
  not "foo" or "example.com" placeholders unless the data uses them.
- State numbers exactly and say where they came from. Say what a check cannot see.
- No filler, no hype words, no em dashes in prose except in the H1 title. Apply the `no-ai-slop`
  skill when it is available.

## Notebook mechanics

- Cell IDs are unique. New notebooks use `cell-00`, `cell-01`, ... in order.
- Kernel metadata matches the other notebooks in the target folder.
- Outputs: follow the folder's rule. Course 04 commits outputs because its runs are paid; the
  repo default is to clear outputs and set `execution_count` to null before committing. Keep
  machine paths out of outputs: write `data/...`, never `/Users/...`.
- Edit `.ipynb` JSON with a short Python script or the NotebookEdit tool, never by hand-editing
  escaped strings.

## Check before handing over

Run this check on the finished file and fix every failure:

```bash
python3 SKILL_DIR/scripts/check_notebook.py path/to/NN_name.ipynb
```

It checks the title cell sections, the idea cell, Part 0 Setup, `---` before every `##`, a
banner on every code cell, a summary with Next Steps, unique cell IDs and no `/Users/`
paths. It does not judge the teaching: reread the markdown cells in order and confirm each Part
answers its learning objective.

Report what was written, what was checked, and that the notebook was not executed (unless the
user asked for a run).
