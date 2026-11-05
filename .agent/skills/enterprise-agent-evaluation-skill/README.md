# Enterprise Agent Evaluation Preparation Skill

Contains a reusable assistant skill for generating weekly theory and hands-on preparation guides from the included 16-week roadmap.

## Install

Copy the entire `enterprise-agent-evaluation-skill` directory into your assistant's configured skills location. For common file-based skill hosts this may be `.agents/skills/`, `.claude/skills/`, or another host-specific folder. Do not install to all locations unless your tools require it. Restart/reload or verify discovery according to your host.

## Invoke

Ask: `Use enterprise-agent-eval-prep to create the full Week 7 study guide.`

If your host exposes skill slash commands, you may be able to use `/enterprise-agent-eval-prep week 7`; the name is not automatically registered by placing the file on disk.

## What is inside
- `SKILL.md` — reusable instructions
- `references/roadmap.md` — full week-by-week scope
- `references/writing-standard.md` — topic structure, short paragraphs, and concise beginner-friendly explanations
- `references/no-ai-slop/SKILL.md` and `eval.md` — bundled editing rules and review checklist
- `references/guide-template.md` — theory/lab/interview format
- `assets/agent_eval_case.jsonl` — synthetic starter test cases

## Writing approach

The skill applies the bundled no-ai-slop rules to content creation and revision. Lessons use descriptive topic sections, short paragraphs, defined terms, and concrete examples. Concision removes filler while preserving the concepts, reasoning, and limits needed to apply the material.
