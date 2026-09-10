# Current-System Discovery

Discovery answers **what exists now**, not what the target should be.

Required outputs include current framework/build/state/router indicators, raw route/API/
import/state facts, source evidence, runtime unknowns, capability inputs and code-health
signals.

`governance/current-system.yaml` must never imply a selected target framework.

Analyzer facts have evidence confidence. Dynamic behavior that cannot be statically
proved remains explicit `NEEDS_RUNTIME_EVIDENCE`/`UNKNOWN` rather than guessed.

## v1.5 discovery accuracy rules

- Relative route object paths such as `hall` are valid evidence when the containing
  object is route-shaped.
- Navigation calls such as `router.push({ path: '/' })` are not route definitions.
- Resolved and unresolved HTTP/API evidence are separate outputs.
- `api-signals.json` records request calls that cannot yet be resolved to concrete
  endpoints.
- If request signals exist but zero endpoints are resolved, Discovery completeness
  must fail.
- Workspace `packages/*` boundaries and route segments can become confirmable Domain
  Candidates.
- `src/config`, `src/data`, `src/lib`, `src/types`, `src/requests` and similar
  infrastructure folders are Structural Hints only.

## v1.5.1 closure rules

- Request wrapper discovery accepts optional TypeScript generic arguments and
  wrapper identifiers containing `Request`.
- Route-object markers are evaluated only at object-literal top level.
- Route-builder helper matches are HEURISTIC evidence, not confirmed route truth.
- Documentation files (`.md`, `.mdx`) are not business API endpoints.
