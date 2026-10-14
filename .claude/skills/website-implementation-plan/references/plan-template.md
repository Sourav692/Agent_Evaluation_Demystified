# Implementation Plan Template

Copy this structure. Keep the numbering and headings. Replace the guidance in each section with real content; delete the guidance text.

Every numbered section from 3 to 13 uses the same four sub-parts:

```markdown
**Goal.** One or two sentences: the user or business outcome this section secures.

**Decisions.**
| Decision | Why | Rejected alternative |
|---|---|---|

**Tasks.**
| ID | Outcome | Size | Depends on |
|---|---|---|---|

**Acceptance criteria.**
- Testable statement, e.g. "All interactive elements reachable by keyboard with visible focus ring."
```

Task ID prefixes: `PM` product, `UX` experience and flows, `DS` design system, `FE` frontend, `BE` backend, `DATA` data and content, `A11Y` accessibility, `PERF` performance, `SEC` security, `QA` testing, `OPS` deploy and operations.

---

## Contents

0. Summary
1. Inputs, mode and assumptions
2. Current state (walkthrough and hybrid only)
3. Product goals, users and success metrics
4. Information architecture and sitemap
5. UX flows and key screens
6. Visual design system
7. Component inventory
8. Frontend architecture
9. Backend, data and APIs
10. Content and CMS pipeline
11. Accessibility, performance and SEO
12. Security, privacy and compliance
13. Testing, deployment and operations
14. Phased roadmap
15. Risks and open questions
16. Appendix: requirement traceability

---

## 0. Summary

Five to eight lines. What is being built, for whom, on what stack, in how many phases, and what Phase 1 delivers. A busy reader should be able to stop here.

## 1. Inputs, mode and assumptions

- Mode: files, walkthrough or hybrid.
- Sources read: list each file or folder with a one-line note of what it contributed.
- Requirement list (files mode): `R1 ... Rn`, each with its source file.
- Assumptions: numbered `A1 ... An`. Each one also appears in section 15.

## 2. Current state

Walkthrough and hybrid only; otherwise write "Greenfield: no existing code."

| Area | What exists | Evidence | Gap or problem |
|---|---|---|---|
| Stack | | `package.json` | |
| Routes | | | |
| Components and tokens | | | |
| Data and backend | | | |
| Content | | | |
| Quality (tests, a11y, analytics) | | | |
| Deploy | | | |

Close with three to five bullets on what to keep, what to fix and what to replace.

## 3. Product goals, users and success metrics

- Primary audiences and personas: who, what they know, what device and context.
- Top jobs to be done, ranked.
- Success metrics with a target and how each is measured (for example, "70% of first-time visitors reach a lesson within 2 clicks, measured by analytics funnel").
- Non-goals.

## 4. Information architecture and sitemap

- Sitemap as a nested list or a mermaid diagram, with real route paths (`/`, `/learn/[track]/[lesson]`).
- Navigation model: global nav, local nav, breadcrumbs, search, footer.
- URL and slug rules, including which IDs must never change.
- Page templates: list the distinct templates and which routes use each.

## 5. UX flows and key screens

- The three to six critical flows, step by step (entry point, steps, success state, failure and empty states).
- For each key screen: purpose, primary action, content hierarchy, and mobile versus desktop layout differences.
- States to design for every data-driven view: loading, empty, error, partial, success.
- Microcopy principles: voice, button verbs, error message pattern.

## 6. Visual design system

Decisions must carry values.

- Color roles: background, surface, text primary and muted, border, accent, success, warning, danger; light and dark values; contrast ratios checked.
- Typography: font families, type scale (sizes and line heights), weights, measure (line length).
- Spacing scale, grid, breakpoints, container widths.
- Radius, elevation and shadow, borders.
- Motion: durations, easing, and reduced-motion behavior.
- Iconography and imagery rules.
- Where tokens live in code (CSS variables, Tailwind theme) and how themes switch.

## 7. Component inventory

| Component | Variants and states | Used on | Exists today? | Task |
|---|---|---|---|---|

Group as primitives (button, input, card), patterns (nav, tabs, table, modal, toast) and page sections (hero, lesson body, progress panel). Note keyboard and screen-reader behavior for every interactive component.

## 8. Frontend architecture

- Framework and versions; why.
- Rendering per route type: static, server-rendered, client, streamed; caching and revalidation rules.
- Folder structure and module boundaries.
- State strategy: what lives in the URL, server, client store, local storage.
- Data fetching pattern and error boundaries.
- Forms and validation (shared schemas with the backend if possible).
- Client bundle budget and how it is enforced.

## 9. Backend, data and APIs

- Data model: entities, key fields, relationships (a mermaid ER diagram helps).
- API surface: endpoint or server action, method, input, output, auth, errors.
- Authentication and authorization model, session handling.
- Validation, rate limiting, idempotency for writes.
- Background jobs, webhooks, third-party services.
- Storage, backups, migrations strategy.

Static sites: state "No backend" and cover only build-time data here.

## 10. Content and CMS pipeline

- Content types and their fields.
- Source of truth (markdown repo, headless CMS, database) and why.
- Authoring workflow, preview, review and publish.
- Build-time generation, validation checks and broken-link checks.
- Media handling: formats, sizes, alt text ownership.

## 11. Accessibility, performance and SEO

- Accessibility target (WCAG 2.2 AA by default), audit method, tooling, and manual checks (keyboard, screen reader, zoom to 200%, reduced motion).
- Performance budgets: LCP, INP, CLS targets, JS and image weight per page type, and how they are measured.
- SEO: metadata per template, Open Graph, sitemap.xml, robots, canonical URLs, structured data.
- Analytics events tied to the success metrics in section 3.

## 12. Security, privacy and compliance

- Threats that matter for this site (auth abuse, injection, XSS through content, secret leakage).
- Headers (CSP, HSTS), secret handling, dependency scanning.
- Personal data collected, where stored, retention, consent and cookie handling.
- Any compliance or licensing constraint, including third-party content rights.

## 13. Testing, deployment and operations

- Test layers: unit, component, integration, end-to-end, visual regression, accessibility automation; what each covers.
- CI pipeline steps and required checks.
- Environments: local, preview, production; how previews are reviewed.
- Release, rollback and feature flags.
- Monitoring: error tracking, uptime, logs, alerts, and who is paged.

## 14. Phased roadmap

Phase 1 is the smallest release that delivers the top jobs from section 3. Each phase:

```markdown
### Phase N: name (estimate)

Outcome: what a user can do at the end of this phase.

Tasks: FE-01, FE-02, BE-01, ... (IDs from the sections above, in build order)

Exit criteria:
- ...
```

End with a critical-path note: the dependency chain that sets the minimum duration, and what can run in parallel.

## 15. Risks and open questions

| ID | Risk or question | Impact | Likelihood | Mitigation or decision needed | Owner |
|---|---|---|---|---|---|

Include every assumption from section 1 that still needs confirmation.

## 16. Appendix: requirement traceability

Files mode and hybrid only.

| Requirement | Source | Plan section(s) | Task IDs |
|---|---|---|---|

Every requirement must appear. If one is deliberately not covered, say why in the last column.
