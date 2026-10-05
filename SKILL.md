---
name: testing-and-continuous-delivery
description: Use when designing test cases or a test strategy, picking a test level or type, applying ISTQB terms (error/defect/failure, equivalence partitioning, boundary values, decision tables, state transitions, statement/branch coverage), planning smoke/sanity/regression runs, judging flaky tests or suite speed, or working on CI/CD pipelines, quality gates, DORA metrics, deployment strategies, trunk-based development, or linting policy. Whenever it is applied to concrete code, a feature or a spec, it always delivers two things, the implemented and executed tests, and a PDF test report (HTML + Chrome, no LaTeX) that justifies each technique with ISTQB citations. Reference content is in Spanish.
---

# Testing and Continuous Delivery

Reference base covering ISTQB testing theory and continuous delivery practice, from *why* a test exists to *how* a pipeline ships it. Reference files are in Spanish.

## Mandatory output

When the skill is applied to a concrete scenario (code, function, endpoint, user story, spec), the deliverable is **always both**:

1. **Implemented tests, executed**, in the project's own framework. Every test carries a technique ID (`EP-01`, `BVA-03`, `DT-R2`, `ST-T4`…) in its name.
2. **A PDF report** at `reportes-pruebas/YYYY-MM-DD-<object>/`: why each technique was chosen for *this* scenario, derivation tables, traceability ID → `file:line`, results, coverage, defects and residual risk, citing ISTQB CTFL v4.0.1 by section and the et al. sources. Full report (one 5-part subsection per technique) when any condition is high risk; short 3-6 page report otherwise.

Steps (details in `references/reporte-contenido.md`):

1. Decide the **oracle** first: expected results come from a spec, from the user, or from declared assumptions — never from the code under test. No spec → ask the user for the expected results of high-risk conditions.
2. Rate product risk, pick techniques with the selection matrix, write the tests with IDs.
3. Run them emitting **JUnit XML + JSON coverage** into the report folder (`--junitxml`, `--cov-report=json`, or the Jest/Vitest equivalents).
4. Write `reporte.json` (your judgment only: risks, why each technique, derivations, defects; schema in §5).
5. `uv run <skill-dir>/scripts/armar_reporte.py <dir>/reporte.json --junit <dir>/junit.xml --cobertura <dir>/coverage.json --raiz .` — validates traceability (every test has an ID, every ID exists in JUnit and at its `file:line`, every failure is a documented defect), takes counts and coverage from the artifacts, numbers citations, and renders the PDF with a page-numbered index. Fix whatever it lists and rerun. `<skill-dir>` is the absolute path of the folder holding this SKILL.md; run from the tested project's root.
6. Look at pages 1-2 as PNG (`pdftoppm`).

Failing tests that expose a defect stay failing and go in `defectos`.

Pure concept questions (no scenario) get a direct answer from the references below.

**Core principle:** testing shows the presence of defects, never their absence — so every technique here is about *choosing* which few tests to write, and about making the signal they produce trustworthy and fast.

## Routing

Load only the file you need.

| Need | File |
|---|---|
| QA vs QC vs Testing, error→defect→failure, the 7 ISTQB principles, verification vs validation, Pyramid/Trophy/Quadrants, shift-left/right, the 4 test levels | `references/fundamentos-y-niveles.md` |
| Functional vs non-functional, black/white/gray box, performance/usability/security/visual/resilience, smoke vs sanity, regression strategies | `references/tipos-y-cambios.md` |
| Equivalence partitioning, boundary values, decision tables, state transition, statement/branch coverage, error guessing/exploratory/checklists, TDD, Clean as You Code | `references/tecnicas-de-diseno.md` |
| Reviews, static analysis and its ceiling, linter buckets, legacy linting adoption, reproducible dependencies | `references/testing-estatico.md` |
| Pipeline/gate/transformation, GitHub Actions anatomy, webhooks, CI vs CD vocabulary, signal vs noise, flakes and retries, suite speed, parallel/sharding, the gap between merges | `references/ci-cd-fundamentos.md` |
| Single source of truth, config as code, secrets, trunk-based development, SLSA, SemVer and pinning, DORA metrics, code freeze, rollback, blue-green and canary | `references/entrega-continua.md` |
| Universal task list, greenfield vs legacy starter packs, task boundaries, when bash falls short, errors/speed/signal triage, `finally`, sharding, parameterized pipelines | `references/diseno-de-pipelines.md` |
| Sources for any claim above | `references/bibliografia.md` |
| Report workflow, oracle rule, technique-selection matrix with verified CTFL v4.0.1 sections, report sections, `reporte.json` schema, citation keys | `references/reporte-contenido.md` |
| Report visual design (palette, cover, header/footer, boxes, tables) and the HTML/CSS skeleton the build script reads | `references/reporte-diseno.md` |

## Quick reference

**Which design technique:**

| If... | Use |
|---|---|
| Valid and invalid ranges | Equivalence partitioning + boundary values |
| Rules combine to decide the outcome | Decision table testing |
| Behavior depends on what happened before | State transition testing |
| Code exists; need to know what actually ran | Statement & branch coverage |
| Thin spec, or the app's failure history is known | Error guessing, exploratory, checklists |

**Levels stack up** (Unit → Integration → System → Acceptance). **Types cut across** them (functional / non-functional). Smoke, sanity and regression are *selections*, not levels.

**DORA elite thresholds:** deploy multiple times/day · lead time under an hour · restore under an hour · change failure rate 0-15%.

## Common mistakes

- **Reading 100% statement coverage as "tested."** Coverage says what *ran*, never what was *verified*. Branch coverage subsumes statement coverage, never the reverse.
- **Equating passing with signal.** A passing test can cover a real bug; a failure that teaches nothing is noise. Investigate every failure, flakes included.
- **Wrapping a whole test body in a retry.** It hides every other bug, not just the flaky call. Retry only the isolated non-deterministic step.
- **Confusing smoke with sanity.** Smoke is broad and shallow, every build. Sanity is narrow and deep, on a build claiming specific fixes.
- **Deploying less often to reduce risk.** Smaller, more frequent deploys lower change failure rate; the math is in `entrega-continua.md`.
- **Trusting a version pin.** Registries let a maintainer republish the same tag. Only a content hash guarantees the same bytes.
- **Writing only the all-true and all-false rules** of a decision table. Those are exactly the columns a wrong `or`/`and` survives.
- **Expecting static analysis to catch a wrong business rule.** It never executes the program — only a test with the right expected result, or a human review, catches that.
