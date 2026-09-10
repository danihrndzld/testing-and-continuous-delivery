# testing-and-continuous-delivery

A [Claude Code skill](https://docs.claude.com/en/docs/claude-code/skills) covering ISTQB testing theory and continuous delivery practice — from why a test exists to how a pipeline ships it.

Claude loads it when you're designing test cases or a test strategy, picking a test level or type, applying ISTQB terms (error/defect/failure, equivalence partitioning, boundary values, decision tables, state transitions, statement/branch coverage), planning smoke/sanity/regression runs, judging flaky tests or suite speed, or working on CI/CD pipelines, quality gates, DORA metrics, deployment strategies, trunk-based development, or linting policy.

Reference content in `references/` is in Spanish.

## Install

Personal (all projects):

```bash
git clone https://github.com/danihrndzld/testing-and-continuous-delivery ~/.claude/skills/testing-and-continuous-delivery
```

Project-only:

```bash
git clone https://github.com/danihrndzld/testing-and-continuous-delivery .claude/skills/testing-and-continuous-delivery
```

Restart Claude Code and it picks up the skill automatically.

## Contents

| File | Covers |
|---|---|
| `references/fundamentos-y-niveles.md` | QA vs QC vs Testing, error→defect→failure, the 7 ISTQB principles, verification vs validation, Pyramid/Trophy/Quadrants, shift-left/right, the 4 test levels |
| `references/tipos-y-cambios.md` | Functional vs non-functional, black/white/gray box, performance/usability/security/visual/resilience, smoke vs sanity, regression strategies |
| `references/tecnicas-de-diseno.md` | Equivalence partitioning, boundary values, decision tables, state transition, statement/branch coverage, error guessing/exploratory/checklists, TDD, Clean as You Code |
| `references/testing-estatico.md` | Reviews, static analysis and its ceiling, linter buckets, legacy linting adoption, reproducible dependencies |
| `references/ci-cd-fundamentos.md` | Pipeline/gate/transformation, GitHub Actions anatomy, webhooks, CI vs CD vocabulary, signal vs noise, flakes and retries, suite speed, parallel/sharding |
| `references/entrega-continua.md` | Single source of truth, config as code, secrets, trunk-based development, SLSA, SemVer and pinning, DORA metrics, code freeze, rollback, blue-green and canary |
| `references/diseno-de-pipelines.md` | Universal task list, greenfield vs legacy starter packs, task boundaries, errors/speed/signal triage, sharding, parameterized pipelines |
| `references/bibliografia.md` | Sources for every claim above |

`SKILL.md` holds the routing table Claude uses to pick which file to load.
