# Delivery validation

## Structural and source checks

Run `scripts/validate_lesson.py lesson.md lesson.html lesson.manifest.json`. The manifest schema is in `examples/manifest.schema.json`; a filled reference manifest is `examples/approved-lesson.manifest.json`.

The validator counts all static interaction panels against the default 2,500-word budget, then checks the theory-only rule, unique IDs, fragment destinations, caption sequence, image embedding, required figures/components, preserved image hashes, and component button/panel contracts. It requires a non-empty coverage inventory with substantive reviewer notes and passing review statuses. It verifies source strings where supplied as evidence, but it cannot decide whether prose teaches a concept adequately. Perform that editorial comparison before marking a row reviewed.

The source inventory must include every diagram across the input versions relevant to the request. Removing an alternative's diagram because a switcher exists is a coverage failure. For a new architectural comparison, its manifest lists at least one required figure per approach.

## Browser checks

The rendering cache contains `puppeteer-core`. Run:

```bash
node SKILL_DIR/scripts/check_browser.cjs lesson.html --out checks/browser.json
```

Set `PUPPETEER_MODULE` to another installed module path or `CHROME_PATH` when needed. The script checks 320, 390, 1254 and 1920 pixels in light and dark. It blocks HTTP/HTTPS asset loads, verifies images, page overflow, every stage/mode, Previous/Next, keyboard, theme controls, self-check disclosure and no-script content. Screenshots of the top and each figure/component are saved beside the JSON. Inspect every figure and each comparison, including the non-default mode. A successful automated check does not prove all labels are visually legible.

If Hallmark is available, run its render sweep on a scratch copy. Hallmark uses its own `HALLMARK_PUPPETEER` setting; point it to `node_modules/puppeteer-core` inside the renderer cache (or another installed module). Verify that the sweep actually rendered before reporting a render pass. Keep the course frame and long-document density. Fix actual failures and assess advisory findings without turning the lesson into a marketing page.

## Compare a reference rebuild

Build the reference with the packaged renderer, without copying its target HTML or adding post-build patches:

```bash
python3 SKILL_DIR/standalone/scripts/build_site.py SKILL_DIR/standalone/references/example-lesson.md rebuilt.html
node SKILL_DIR/scripts/compare_pages.cjs SKILL_DIR/standalone/references/example-lesson.html rebuilt.html --out checks/comparison.json
```

This compares article text, original image payloads where protected, component contracts, layout and screenshots at desktop/mobile in both themes. Mermaid can emit fresh internal SVG IDs; compare rendered appearance as well as meaningful content rather than requiring a byte-identical generated file. Record the actual pixel difference and any explained variation. The default allows at most 0.025% differing pixels with a maximum channel delta of 64, after exact text/component/layout checks. This threshold was calibrated against the approved file compared with itself in two browser pages, which showed up to 0.0187% text-edge raster differences. `--strict-pixels` requires zero differences when using a fully deterministic capture environment. Never use the tolerance to excuse changed content, layout or protected assets. Use the reference manifest for exact required asset and semantic checks.

The rebuild demonstrates template/component reproducibility. It does not prove that another writer will select or explain every source concept correctly. For a substantial skill revision, independently adapt a different source lesson through the package and review its coverage, diagrams, examples and interaction choices. Record any failure and its correction.

## Live site limits

A standalone export does not run the website's complete curriculum/import checks. In a repository, also run its required build, links and tests. Do not report those checks as passed unless they ran. Mark external notebook scores as inherited when not rerun, and distinguish source-reported results from new illustrative values.
