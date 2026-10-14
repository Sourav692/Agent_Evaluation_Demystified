# Explorer content contract

Use a JSON object with `title`, optional `subtitle`, `sources`, and `systems`. All prose is plain text. Systems have independent topologies and variable stage counts.

## Top level

```json
{"title":"FDE Architecture Explorer","subtitle":"Explore the flow. Understand the decisions. Revise.","sources":[{"id":"notes","title":"Real source title","file":"actual-source.md","note":"Available sections used and any adaptations."}],"systems":[]}
```

Source entries accept a verified HTTPS `url`. Use `sources: []` if no source exists, and explicitly label the representative design in `provenance`.

## System

Required: `id`, `name`, `nav`, `family`, `tag`, `description`, `question`, `scope`, `provenance`, `sourceIds`, `diagram`, `scenarios`, `revision`.

- `id`: unique lowercase identifier. `nav`: short sidebar label.
- `description`: purpose in 1–2 sentences. `question`: the request/event being followed.
- `scope`: what the walkthrough does and where it ends.
- `provenance`: source/adaptation boundaries and key assumptions.
- `sourceIds`: source IDs actually used.

Optional: `icon` (`search`, `layers`, `shield`), `color` (`purple`, `teal`, `orange`), `time` (reading-time estimate such as `4 min`).

## Diagram

```json
{"width":960,"height":470,"nodes":[
 {"id":"gateway","label":"API gateway","sub":"Trusted identity","x":30,"y":40},
 {"id":"search","label":"Retriever","sub":"Permitted evidence","x":270,"y":40},
 {"id":"store","label":"Knowledge base","sub":"Versioned docs","x":510,"y":200,"role":"data"}
],"edges":[
 {"from":"gateway","to":"search","kind":"flow"},
 {"from":"search","to":"store","kind":"data","label":"read","points":[[448,75],[599,75],[599,200]]}
]}
```

Nodes default to 178×70 units; optional `w`/`h` override this. Use `role: component | data | branch | observation`. Keep labels short. Place nodes inside the viewBox without overlap.

Edges use `kind: flow | data | branch | observation`. Optional `points` is an orthogonal route as `[x,y]` pairs. Otherwise the renderer connects the nearest node sides with a bend. Optional `labelX`/`labelY` place a label away from crossings.

Include all nodes needed by any scenario. Map every node to a stage through `nodeIds`, or mark it skipped for that scenario.

## Scenario and stage

```json
{"id":"normal","label":"Evidence found","outcome":"Grounded answer","stages":[
 {"title":"Establish identity","component":"API gateway","short":"Who is asking?",
 "what":"Describe this request's execution now.","why":"Explain the need or failure it addresses.","next":"Name the actual next step or terminal outcome.",
 "input":{"question":"Illustrative request"},"output":{"scope":"trusted tenant"},
 "checks":[{"kind":"Exact","text":"An exact control."}],"nodeIds":["gateway"]}
]}
```

`input`/`output` may be strings, objects, or arrays. Checks use `Exact`, `Judge`, `Offline`, or `Observe`, only where relevant. First scenario is the default.

Optional scenario fields:

- `edges`: replace diagram edges, avoiding automatic execution of a stopped path.
- `skipNodes`: show these components as skipped, without stage selection.
- `nodeOverrides`: map node IDs to `label`, `sub`, `x`, `y`, `w`, or `h` overrides.

Every node must map to a stage or be skipped. Do not map skipped nodes to an active stage. Shorten early-ending scenarios instead of inventing later work.

## Revision

```json
{"pitch":"A concise spoken whole-system answer.","flow":"Identify → Retrieve → Draft → Check → Return",
"requirements":[["Functional","Concrete behaviors."],["Non-functional","Constraints and controls."]],
"discovery":["A question that changes the design?","Another important question?"],
"tradeoff":"One tradeoff and consequence.","failure":"One failure and handling.",
"ops":[["Scale","Brief talking point."],["Latency","Brief talking point."],["Cost","Brief talking point."],["Evaluation","Brief talking point."]],
"remember":"A short anchor line."}
```

Keep revision specific and compact. Do not introduce unsupported features or hard performance promises.
