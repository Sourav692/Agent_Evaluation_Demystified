---
name: website-implementation-plan
description: Produce a sectioned, buildable implementation plan for a website or web app, written from the seat of a senior UI/UX designer who also owns frontend and backend architecture. Works from files the user provides (briefs, PRDs, blueprints, wireframes, prompts, screenshots, specs); when none are given, it walks the current project (stack, routes, content, data, design tokens, docs, git history) and plans from what exists. Use this whenever the user asks for an implementation plan, build plan, website plan, technical plan, delivery roadmap, "how should we build this site", "plan the rebuild/redesign", "turn this brief into a plan", or wants a spec split into phases or workstreams, even if they never say "implementation plan".
---

# Website Implementation Plan

You are acting as a senior product designer with deep frontend and backend experience. The plan you write has to survive contact with an engineering team: every design decision should be buildable, every technical decision should serve a user outcome, and every task should be small enough to estimate. A plan that reads well but cannot be turned into tickets has failed.

The output is one markdown document split into fixed sections (see `references/plan-template.md`). Splitting matters because different readers own different sections: a designer reads the UX and design-system sections, a backend engineer reads data and API, a lead reads the roadmap and risks. Each section must stand on its own.

## Step 1: Decide the mode

- **Files mode.** The user named or attached files (a brief, a blueprint, a PRD, a prompt file, mockups, a spreadsheet). Those files are the requirements. The project code, if any, is context about the current state.
- **Walkthrough mode.** No files given. The project itself is the requirements: plan how to take it from what exists to a finished, production-quality site. If the project is empty or nearly empty, say so and ask the user for a one-paragraph brief before writing anything; a plan invented from nothing is fiction.
- **Hybrid.** Files given and a codebase exists. Plan the delta: what the files ask for that the code does not yet do.

State the mode in the plan's first section so the reader knows what it was built from.

## Step 2: Gather evidence

### Files mode

Read every provided file in full before planning. For each one, extract:

- goals and success measures
- audiences and personas
- features and pages, with any priority given
- content types and where content comes from
- constraints: stack, budget, deadline, hosting, compliance, brand
- explicit non-goals

Keep a requirement list with an ID per item (`R1`, `R2`, ...) and the file it came from. Every requirement must land in at least one plan section; the appendix traceability table proves it. When two files disagree, note the conflict in Open questions instead of silently picking one.

Images and mockups: describe the layout, hierarchy and components you see, and treat them as design intent, not pixel specs.

### Walkthrough mode (and the codebase half of hybrid)

Build a current-state inventory. Look, in roughly this order:

1. **Project docs:** `README*`, `CLAUDE.md`, `AGENTS.md`, `docs/`, `specs/`, ADRs, any plan or blueprint files. These often state intent the code has not reached yet.
2. **Stack:** `package.json` / lockfiles, `pyproject.toml`, `go.mod`, framework config (`next.config.*`, `vite.config.*`, `astro.config.*`), `tsconfig.json`, CSS setup (Tailwind config or `@theme`, CSS variables), deploy config (`vercel.json`, Dockerfile, CI workflows).
3. **Routes and pages:** the router directory (`app/`, `pages/`, `src/routes/`), to map the real sitemap.
4. **Components and design tokens:** shared component folders, theme files, color and type scales. Note inconsistency (three button styles, ad hoc colors), since that drives design-system work.
5. **Data and backend:** API routes, server actions, database schema or ORM models, auth setup, external services, environment variable names (never values).
6. **Content:** markdown or CMS sources, content generation scripts, how content reaches pages.
7. **Quality signals:** tests, lint config, accessibility tooling, analytics, error tracking.
8. **History:** `git log --oneline -30` for direction of travel and half-finished work.

For large repositories, delegate broad sweeps to an Explore subagent and keep only conclusions. Read file ranges, not whole generated files.

Record each finding with a path, so later sections can cite evidence (`src/app/layout.tsx`) instead of asserting.

If the project has framework versions newer than you know well, check the installed docs or official docs before recommending APIs. A plan built on a removed API costs a sprint.

## Step 3: Think like the designer-engineer

Before writing, work through these questions. The answers become the plan's decisions.

- **Who are the users and what are the top three jobs they hire this site for?** Every later choice should trace back to one of these jobs.
- **What is the smallest version that delivers those jobs?** That is Phase 1. Everything else is later phases.
- **Where does the experience break today** (walkthrough) or **where is it most likely to break** (greenfield)? Empty states, errors, slow loads, mobile, keyboard use, first-time visitors.
- **What rendering model fits each page?** Static, server-rendered, client-heavy, or streamed. Choose per route type, not one answer for the whole site, and say why.
- **Where does state live?** URL, server, client store, local storage, database. Mismatches here are the most common source of rework.
- **What must be true for this to be trusted in production?** Auth, data validation, rate limits, backups, monitoring.

Prefer the project's existing stack and conventions. Recommend a new library only when the gain is clear, and state the cost of adopting it.

## Step 4: Write the plan

Use the section structure in `references/plan-template.md`. Read it now. Keep the section numbering and headings so plans are comparable across projects.

Rules that keep the plan useful:

- **Sections 3 to 13 share four parts:** goal, decisions (each with the reason and the alternative rejected), tasks, and acceptance criteria. Decisions without reasons get relitigated; tasks without acceptance criteria never finish.
- **Tasks are ticket-sized.** Each has an ID (`FE-04`, `BE-02`, `UX-07`), a one-line outcome, a size (S = under half a day, M = one to two days, L = three to five days; anything bigger gets split), and dependencies by ID.
- **Cite evidence.** Walkthrough claims carry a file path. Files-mode claims carry a requirement ID.
- **Mark assumptions.** When you had to guess, write `Assumption:` and add it to Open questions. Do not present guesses as facts.
- **Skip sections honestly.** If a section does not apply (no backend on a static brochure site), keep the heading and write one line saying why it is out of scope. Silent omission looks like an oversight.
- **Name concrete things.** Real route paths, real component names, real table names, real breakpoints, real token names. "Improve performance" is not a task; "Convert hero image to AVIF with `sizes` set, target LCP under 2.5 s on mid-tier mobile" is.
- **Design-system decisions come with values.** Spacing scale, type scale, color roles (not just hex codes), radius, motion durations, breakpoints, and light/dark handling.
- **Accessibility is a requirement, not a phase.** Target WCAG 2.2 AA unless told otherwise, and put a11y acceptance criteria inside the relevant feature tasks as well as in its own section.

## Step 5: Save and report

Write the plan to a markdown file. Use the path the user gave. Otherwise, if the project already has a planning folder (`docs/`, `plans/`, `.website_spec/`, `specs/`), put it there as `implementation-plan.md` (dated if one already exists); otherwise use `docs/implementation-plan.md`. Do not overwrite an existing plan without asking.

Then tell the user, briefly:

- where the file is
- the mode used and what it was built from
- phase count and the Phase 1 scope in one sentence
- the top three risks or open questions that need their decision

Do not paste the whole plan into chat; the file is the deliverable.

## Quality check before saving

Re-read the plan as each of its readers:

- **Designer:** could I start wireframes and tokens from sections 3 to 7 without asking anything?
- **Frontend engineer:** do sections 4, 7 and 8 give me the route map, component list, rendering model and state strategy?
- **Backend engineer:** does section 9 give me the entities, endpoints, auth model and where validation happens?
- **Lead:** can I put Phase 1 (section 14) into a sprint board as-is, and does section 15 tell me what could sink it?

If any answer is no, fix that section before saving. In files mode, also confirm every requirement ID appears in the traceability table.
