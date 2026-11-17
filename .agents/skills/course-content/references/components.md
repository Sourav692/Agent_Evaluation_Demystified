# Reusable teaching components

The approved Markdown shows the full examples. Copy the component structure, then replace all content and IDs for the new subject. The renderer always includes `reader.js`; it contains no refund policy, LangGraph node name or fixed stage count. Do not paste inline scripts into lesson Markdown.

## Walkthrough

Use an outer `<div class="walkthrough learning-widget" data-stepper id="unique-id">`. Inside it provide:

- A `.widget-intro` paragraph naming what the learner can inspect.
- A `.step-controls` group with `hidden`, `role="group"` and a meaningful `aria-label`.
- One native button per stage: `type="button"`, `data-step="any-unique-value"`, `aria-pressed="false"`, and `aria-controls="panel-id"`.
- One `.step-panel` section per button with that ID, a visible descriptive heading and its actual input/decision/state/output explanation. All panels are initially visible. Order the buttons and panels in the process sequence.
- A `.step-footer` with `hidden`, Previous and Next buttons marked `data-walk="previous"` and `data-walk="next"`, and `.step-status` with `aria-live="polite"`.

Desktop columns adapt to the stage count: four stages use two balanced rows, and the six-stage reference keeps three columns. An optional `data-columns="1"` to `"4"` on `.step-controls` selects a deliberate desktop arrangement. Mobile keeps two columns.

The reader matches buttons to panels through `aria-controls`, computes the stage count, maintains selected/disabled states and exposes one stage at a time. It supports multiple independent walkthroughs. A malformed component remains static for readability, but the validator rejects it for delivery.

A stage should reveal a meaningful transition. Do not break one sentence into six panels to imitate the reference. Three, five or another appropriate count is valid.

## Architectural comparison

Explain each approach and place its own labelled diagram before the interactive comparison. Use a common input. State what each component reads, computes, stores and passes onward. A selection control does not replace either architecture diagram.

Use `<div class="learning-widget evidence-switcher" data-comparison id="unique-id">`. Inside it provide:

- A `.widget-intro` naming the question or state difference being compared.
- A `.mode-controls` group with `hidden`, `role="group"` and a descriptive `aria-label`.
- Two or more buttons with `type="button"`, a unique `data-mode`, `aria-pressed="false"` and `aria-controls="panel-id"`.
- A `.mode-panel` section for each button. Match its ID to `aria-controls`; show a visible heading and concrete state/result changes. Add a short `data-announcement` on the panel when a topic-specific live announcement helps.
- A `.switch-status` paragraph with `aria-live="polite"`.

All panels begin visible. After script enhancement the first mode is selected. The script derives mode membership from the authored controls and panels. It supports several comparisons on one page and any appropriate number of modes. The selected button label is a fallback announcement.

## Figures and tables

Use Mermaid for new mechanism diagrams or embed supplied SVG images in an offline-safe figure. Existing source assets remain unchanged; a necessary SVG/XML packaging normalisation must be recorded separately from a semantic redraw. For a wide source image, use `.diagram.source-diagram` and its light/dark `.dg` variants. The two restored comparison diagrams use `.diagram.comparison-diagram` with a `.comparison-sheet` wrapper to retain their original paper palette in both themes.

Give required figures stable IDs, for example `<figure id="approach-a-architecture" class="diagram" markdown="0">...`. Use a numbered italic caption immediately afterwards. New Mermaid figures receive a numbered caption and their figure ID is derived from the caption number (`figure-4`), unless an explicit authored figure provides one. The manifest records the required IDs and any protected payload hashes.

Tables use ordinary Markdown syntax. The renderer supplies column scopes, mobile cell labels and value wrappers. Native `<details>` and `<summary>` hold self-checks. Source notebook links remain in their generated course slot, or their retained section for a standalone adaptation.

## Accessibility and progressive enhancement

Use buttons rather than clickable text, unique IDs and immediate focus rings. Show selected state through contrast and `aria-pressed`. Let native Enter/Space activate buttons. Previous/Next indicate limits through the native disabled property. Do not add decorative motion, fake loading, fabricated success or network calls to a scripted illustration.

Without JavaScript, all panels remain visible and inactive controls remain hidden. In print, all explanations are shown. Test every authored stage/mode, not only the default. On phones, diagrams scroll inside their frames rather than shrinking labels to fit.
