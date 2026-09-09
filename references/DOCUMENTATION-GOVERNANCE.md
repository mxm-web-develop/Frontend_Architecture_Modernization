# Documentation Governance

## Document classes

### Authoritative
Current rules and decisions.

Examples:
- `governance/*`
- active `docs/architecture/*`
- accepted ADRs

### Generated
Derived inventories/reports.

Examples:
- migration assessment tables
- dependency/API inventories
- generated docs index

Generated files should identify their source and should not be hand-edited unless
the generation workflow explicitly allows it.

### Evidence
Tests, screenshots, runtime captures, hashes and proof artifacts.

### Historical
Superseded docs retained for traceability. They are not current architecture truth.

## Metadata

Important Markdown documents should carry stable metadata where practical:

```yaml
---
id: ARCH-ROUTING-001
type: architecture
status: active
schema_version: 1
related_decisions:
  - ADR-008
last_verified_commit: 912afb3
---
```

## Naming

Avoid ambiguous names:

```text
routing-final.md
routing-final-v2.md
new-routing-final.md
```

Use stable IDs and explicit status/supersession.

## Docs index

Maintain a machine-readable index.

Use:

```bash
python scripts/generate_docs_index.py docs --output governance/docs-index.json
```

## Drift

If code/architecture state invalidates a document:

- update it in the same change when authoritative;
- regenerate it when generated;
- archive/supersede it when historical.

Do not leave known-stale active docs.

## Session continuity

Durable facts belong in predictable repository files, not scratch chat notes.

Development logs may be useful, but they cannot replace structured migration state,
ADRs or Git evidence.
