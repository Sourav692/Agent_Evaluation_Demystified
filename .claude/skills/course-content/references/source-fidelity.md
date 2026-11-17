# Source fidelity and editorial freedom

Use this reference for every source-derived create, rewrite or standalone lesson. Preserve what the source teaches. Its editorial headings are not immutable. Repository contracts and protected content still apply.

## Inventory the original

Read the original article, README, transcript or notebook, including diagrams and linked assets needed to understand it. Record its URL or path and retrieval date. If unavailable, use an authenticated local copy or supplied source and state its provenance. If no original is available, report the gap rather than substituting an earlier adaptation.

Include all user-supplied source and adaptation files in the inventory. A diagram added by another supplied version can still be required by the requested combined format. Never treat an interactive substitute as authorisation to remove it.

Inventory each teaching unit: concept, mechanism, example, named failure, numerical observation, negative result, qualification, comparison, table, diagram, notebook link and check. Source headings are useful inventory labels. They are not a requirement to copy the source structure.

Before drafting, create a coverage matrix: source heading/item; specific teaching content; output heading/anchor; preserved/expanded/omitted; reason. A source section may map to several output sections. Several source items may share one output section only when each still has a substantive explanation. Omission needs explicit user authorisation, identified in the matrix.

## Rename and reorganise for clarity

Rename non-contract headings to say what the section teaches. Split a crowded section or combine repetitive explanations when it improves the learning sequence. Record the new anchors and the reason. A brief mention, keyword or table label does not preserve a mechanism the source explains.

Keep exact concept headings required by curriculum metadata, required footer and notebook slots, and site import hooks. Preserve dependencies: define a concept before relying on it. Keep protected diagrams in their original relative order, moving each with its explanation when needed.

## Preserve diagrams and evidence

Keep existing Mermaid blocks, SVG/image references, animations and labs unchanged in repository rewrites. Additional figures supplement them. If the source provides only rendered diagrams, retain the original light/dark assets in a standalone export, embedded or packaged for offline use. Record asset URLs and hashes. A semantic redraw is allowed only when the original format cannot be retained or the user requests it; map every node, edge, branch label and caveat, and disclose the redraw. Never replace a sequence diagram with prose alone.

Check the diagram contents, not only its filename. Preserve its participants, direction, decisions, loop-back target, termination and figure caption meaning. If the source figure contradicts the prose, retain and flag the discrepancy. Give a corrected supplementary figure where useful, without silently changing the source.

Preserve exact values, corpus provenance, named examples, uncertainty and negative findings. Label inherited measurements as source-reported unless rerun. Correct an overbroad source statement with a scoped explanation and a note in the coverage matrix. Do not turn one lab's result into a universal API guarantee.

## Add useful teaching material

Add definitions, worked state traces, process or transaction diagrams, alternative designs, decision rules and planted failures when they resolve a learning gap. Label hypothetical cases as illustrative and new engineering guidance as an addition. Cite current primary documentation for moving API claims. An illustrative value is not a benchmark.

Explain alternatives individually before comparing them. For graph workflows, separate the work that computes a verdict, the state update that records it, and the router that chooses a destination. Explain when a separate node earns its checkpoint/retry boundary and when a small edge router is enough. Neither a node nor a schema automatically guarantees correct judgments.

Compress repetition before source concepts. Respect a deployment word limit when applicable; report any unresolved conflict instead of deleting source material. A standalone delivery does not imply publication or permission to edit the source repository.

## Verify the delivery

- Every inventory item maps to an existing output anchor with meaningful content. No unauthorised omissions.
- Every original diagram and protected block is present. Compare bytes or hashes where preservation is exact, and inspect every rendered figure.
- Examples, values, distinctions, caveats and checks remain correct. Additions and corrections are distinguishable.
- Check notebook links and navigation. Keep generated notebook slots instead of duplicating them. Standalone adaptations may retain the source's existing notebook section when no importer creates it.
- Build the HTML, inspect desktop/mobile and light/dark, exercise controls and check offline assets. Report any unavailable checks.
- Deliver the coverage matrix and verification results with the Markdown/HTML pair. Heading equality alone cannot establish fidelity.

## LangGraph regression case

The retriever-as-tool lesson must still explain both routing decisions and their return-value/path-map contracts; the greeting bypass; rewrite back to agent; edge-local versus persisted verdicts; whole-block versus per-chunk grading and call counts; exact label matching, normalisation and enum validation; relatedness versus answerability; every TF-IDF result and its limits; loop termination; notebook provenance; and the three original self-checks. Preserve both original diagrams. Add a transaction/process trace and a separate-node alternative when requested. Renamed headings pass when all these items remain taught and mapped.
