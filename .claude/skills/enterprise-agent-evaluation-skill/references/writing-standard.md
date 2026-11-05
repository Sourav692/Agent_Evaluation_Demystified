# Writing standard

Read `no-ai-slop/SKILL.md` before drafting or revising content. Apply its editing rules alongside the teaching guidance below. Preserve technical accuracy and the learner's requested scope.

## Audience and voice

Write as an engineer teaching someone new to agent evaluation. Use familiar words, direct verbs, and complete sentences. Define technical terms and expand abbreviations on first use. Use the same name for the same concept throughout.

Keep one continuous example: a customer-support agent that retrieves refund policy and calls tools. Label assumptions and distinguish observed results from illustrative outputs. Preserve uncertainty where the evidence requires it.

## Topics, sections, and paragraphs

Give the lesson a title that names its topic. Use descriptive second-level headings for major sections and third-level headings for distinct concepts within them. Keep heading levels in order. Combine closely related points when separate headings would fragment the explanation.

Keep one idea per paragraph, usually in 1–3 sentences. Start a new paragraph when the idea changes. Explain mechanisms and reasoning in connected prose. Use numbered lists for ordered steps, bullets for parallel items, and tables for comparisons. Avoid turning the whole lesson into a list of fragments.

Order concepts by dependency. Establish the problem and essential terms before introducing metrics, code, formulas, or design trade-offs. Add a brief transition when the connection between topics would otherwise be unclear.

## Beginner-friendly explanations

Explain what each concept means and which problem it solves. Show how it works with a small concrete example, then cover when to use it, its limits, and how to inspect a failure. Weave these details into natural prose instead of repeating identical labels under every heading.

For example, explain idempotency as preventing the same refund from being issued twice when a request is retried. Then show how a request ID lets the backend recognize a retry and return the stored result.

For each metric, explain what it measures, its inputs, how to read the result, and where it can mislead. If a formula is needed, define its symbols and work through small numbers. Explain code inputs, the main steps, and expected outputs before discussing implementation details.

Begin with small deterministic examples. Introduce model or judge variability when relevant. Prefer straightforward Python and comments that explain non-obvious choices. For labs, include exact commands, expected results, and deliberate failures with fixes. For theory, use a conceptual failure example without requiring runnable code.

Introduce advanced trade-offs after the basic mechanism is clear. State the decision criteria and practical consequences. Keep prerequisites visible so beginners can identify what they need to learn first.

## Concision and coverage

Cover all concepts needed for the requested topic and mode. Remove repetition, generic introductions, slogans, and recap paragraphs. Keep definitions, reasoning, examples, caveats, and failure modes that the learner needs to apply the idea. Do not meet a length target by leaving concepts unexplained.

Use one worked example across related concepts when it helps continuity. Avoid repeating an analogy or adding a new analogy for every term. End with measurable checks or the next concrete action.

## Editorial review

1. Check coverage against the selected roadmap scope and deliverable mode.
2. Check that a beginner can follow the prerequisites, definitions, examples, and reasoning in order.
3. Remove filler and repeated explanations without dropping technical substance.
4. Check headings, paragraph boundaries, terminology, and internal references.
5. Confirm that code, outputs, diagrams, and acceptance criteria agree.
6. Review against `no-ai-slop/eval.md`, fix failed checks, and reread the result.
