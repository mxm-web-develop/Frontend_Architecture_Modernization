# v1.3 Workflow

## Scope

This workflow reconstructs an existing frontend into a separate new repository. It does
not implement Target-only net-new product requirements.

## Lifecycle

```text
DISCOVERED
-> CURRENT_SYSTEM_MODELED
-> CAPABILITY_MODELED
-> ARCHITECTURE_ASSESSED
-> FRAMEWORK_STRATEGY_CONFIRMED
-> RESPONSIBILITY_REVIEWED
-> TARGET_CONTRACT_DEFINED
-> REMEDIATION_PLANNED
-> IMPLEMENTING
-> FUNCTIONAL_PARITY_CHECK
-> VISUAL_PARITY_CHECK
-> ARCHITECTURE_CHECK
-> TRACEABILITY_CHECK
-> MODERNIZED
-> HANDOFF_READY
```

### Discovery

Run bootstrap and analyze. Bootstrap leaves framework strategy `UNDECIDED`.

### Capability modeling

Recover product capabilities from Legacy behavior/evidence. Do not treat files/routes as
final module boundaries.

### Architecture assessment

Compare Legacy architecture against the unified modernization constitution. Produce
remediation findings and code-health evidence.

### Framework strategy

Generate recommendations, then require explicit human confirmation + ADR.

### Target definition and remediation planning

Define module manifests, integration contracts, target data/state/runtime boundaries and
source-to-target mappings. The selected framework adapter controls implementation details,
not the architecture principles.

### Implementation and parity

Reproduce Legacy capabilities while improving implementation architecture. New product
requirements remain deferred.

### Modernized

All required evidence gates pass and Legacy capability coverage is complete.

### Handoff ready

Generate the handoff package, verify module/docs/commands/governance, and transfer
Target-only new requirements to the post-modernization backlog.

## Legacy delta loop

While Legacy remains active:

```text
MODERNIZED -> SYNCING -> MODERNIZED
```

A newly shipped Legacy capability is `LEGACY_DELTA` and remains in scope.
