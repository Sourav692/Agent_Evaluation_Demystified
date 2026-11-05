# Setup and prerequisites

This page gets your machine ready and covers the background the weekly guides assume: Python, JSON Lines files, the command line, retrieval-augmented generation, model calls and agent tool calls. If a term in a weekly guide is unfamiliar, check the [glossary](glossary.md).

## Install and check

You need Python 3.12 or later and a terminal. From the repository root:

```bash
cd new_course
python3 --version                              # must print 3.12 or later
python3 -m venv .venv
source .venv/bin/activate                      # Windows: .venv\Scripts\activate
pip install -r requirements-core.txt
python3 -m pytest                              # runs the tests for every written week
```

The last command should end with `222 passed`. Activate the environment in every new terminal before running course commands. The labs use only the standard library. `requirements-core.txt` adds pytest for the tests, `ipykernel` so the hands-on notebooks can use this environment as their kernel, and `markdown` for rebuilding the theory HTML.

Run every course command from `new_course/`. The `pytest.ini` file in this folder limits pytest to `weeks/`. Never run a bare `pytest` from the repository root: other folders there contain test files that call paid models.

If you use `uv`, the repository root sets `VIRTUAL_ENV` to its own environment, so a bare `uv pip install` installs into the wrong place. Name this course's environment explicitly:

```bash
uv venv .venv --python 3.12
uv pip install --python .venv/bin/python -r requirements-core.txt
source .venv/bin/activate
```

To open a hands-on notebook, select `new_course/.venv` as its kernel in VS Code, or register it once for Jupyter and pick "new_course" from the kernel list:

```bash
python3 -m ipykernel install --user --name new-course --display-name "new_course"
```

Each week's theory comes as Markdown and as a rendered HTML file you can open in a browser. The Markdown is the source. After editing a theory file, rebuild the HTML with `python3 tools/build_html.py`. The tests fail if any HTML file is out of date.

Optional integrations, such as the Week 3 live judge, Week 4's live embeddings and Week 5's Ragas metrics, are listed in `requirements-integrations.txt`. Its pins are a set: Ragas 0.4.3 caps `openai` below 3.0, so the file pins `openai` 2.54.0. Install them only when an exercise asks for them. They call paid services, and each weekly guide states the credentials, the number of calls and the validation status before you run anything.

## Python you will read

The labs use plain Python: functions, lists, dictionaries, `dataclasses`, `pathlib` for file paths, `json` and `argparse` for command-line options. No class hierarchies or frameworks. If you can read this function, you can read the labs:

```python
def passed(case: dict, outcome: str) -> bool:
    return outcome == case["expected_outcome"]
```

The type hints (`dict`, `-> bool`) are documentation. Python does not enforce them at run time.

## JSON and JSON Lines

JSON is a text format for structured data: objects in braces, lists in brackets, strings in double quotes, plus numbers, `true`, `false` and `null`. **JSON Lines** (`.jsonl`) puts one complete JSON object on each line. The course stores cases in JSON Lines because each line is one case: you can count them with `wc -l`, compare two versions line by line with `diff`, and append new cases without rewriting the file.

```json
{"case_id": "case-0001", "message": "My order #123 arrived damaged. Can I get a refund?", "expected_outcome": "refund_created"}
```

## Command-line basics

You will run Python files with arguments, such as `python3 weeks/week-01-evaluation-basics/handson/lab.py --case case-0001`. The words after the file name are **arguments**. Each lab prints its options with `--help`.

Every program returns an **exit code** when it finishes. Zero means success, and any other number means failure. Run `echo $?` straight after a command to see it. Evaluation scripts use exit codes so that an automated job can stop when a check fails. Week 2's validator is the first example.

## Retrieval-augmented generation

A language model answers from patterns in its training data. It does not know your company's refund policy, and it cannot know about a policy change made last week. **Retrieval-augmented generation (RAG)** fixes that by retrieving relevant passages from your own documents first, then giving them to the model with the question. The model is asked to answer from those passages.

That creates two places to fail. Retrieval can return the wrong passage, such as an old version of the policy. Generation can ignore or misread the right passage. Weeks 4 to 6 measure the two separately, on a help-centre corpus of 7 documents. Weeks 1 to 3 treat the policy as fixed text the agent already has.

## Model calls

A **model call** sends text (the prompt) to a language model through an API and receives generated text back. You pay per **token**, a chunk of text of roughly three-quarters of an English word, counted separately for input and output.

The same prompt can return different text on different calls, because the model samples each next token from a probability distribution. A **temperature** setting controls how much: lower temperatures make output more repeatable, but even at zero, many providers do not guarantee identical results. Every evaluation that involves a model must allow for this. The course does so by checking structured fields rather than exact wording, and by running comparisons more than once in later weeks.

## Agents and tool calls

An **agent** is a program that uses a model to decide what to do next, including which tools to call. A **tool** is a function the agent can ask the program to run, such as `get_order(order_id)`. The model proposes a call with arguments, the program runs it, and the result goes back to the model, which decides the next step. The ordered record of those calls and their arguments is the **trace**.

Two facts about agents shape this whole course. First, a tool call changes the world: `create_refund` moves money, whatever the agent says in its reply. Second, the model's proposal is not a permission. The backend must check identity, ownership and eligibility in code, because a model can be talked into proposing anything.

## The refund agent used throughout

Every week evaluates the same system: a customer-support agent that handles refund requests. It has four tools: `get_order`, `get_customer`, `search_policy` and `create_refund`. The [refund policy](datasets/policies/refund-policy-2026-01.md) has six numbered rules, R1 to R6, covering ownership, the 30-day window, final-sale items, refunds over $500, missing order numbers and one refund per order.

Weeks 1 to 3 use **agent v1** (`shared/support_agent.py`), a rule-based mock rather than a model. Every run gives the same result and costs nothing, which makes the evaluation mechanics easy to see. V1 has five deliberate bugs, listed at the top of its file. The labs exist to find them, so read that list after you finish Week 1, not before. Later weeks add new agent versions alongside v1 instead of editing it. Every earlier lab keeps producing the results its guide describes.

All customers, orders and policies are synthetic. `datasets/world.json` holds 40 customers and 89 orders as of 2026-03-15, the fixed "today" for every date calculation. `datasets/build_datasets.py` shows how every record was made.
