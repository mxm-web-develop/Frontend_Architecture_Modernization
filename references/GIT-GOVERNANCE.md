# Git Governance

Git is historical evidence, not only source storage.

## Branch policy

Prefer short-lived branches and incremental integration.

Examples:

```text
migration/users/analyze
migration/users/list
migration/users/roles
migration/users/parity
```

Do not keep a months-long branch as the only record of migration truth.

## Commit categories

Recommended:

- `analyze`
- `arch`
- `migrate`
- `verify`
- `sync`
- `governance`
- `docs`
- `refactor`
- `fix`

Example:

```text
migrate(users): preserve role assignment flow
```

## Migration trailers

For migration/verification commits, prefer Git trailers:

```text
Migration-Domain: users
Capability: CAP-USER-017
Legacy-Base: 83d29a1
Legacy-Checked: 93af129
Decision: ADR-021
Evidence: EVID-USER-017
Visual-Evidence: EVID-VIS-USER-017
Visual-Policy: STRICT_PRESERVE
```

Not every trailer is required for every commit. Project policy may define required
sets by commit type.

## Atomic traceability

The same logical change should normally include:

- target code;
- tests;
- migration state;
- source-target mapping;
- evidence reference;
- necessary documentation.

Do not intentionally create weeks of ledger drift.

## State transitions

Important migration state transitions should be committed.

A state file may record the commit at which the state became true.

## Baseline/delta

Each domain records legacy baseline and last checked commit.

Never claim "synced" if unresolved delta records remain.

## Validation

Use `scripts/validate_git_trace.py` as a lightweight trailer guardrail, plus project
CI policies where available.
