# Scope Boundary

This Skill exists only for brownfield reconstruction into a new governed repository.

## Product truth

Legacy production behavior defines what must be reproduced. Architecture is not copied
from legacy; it is redesigned against the modernization constitution.

## In-scope work classes

- `LEGACY_PARITY`
- `LEGACY_DELTA`
- `ARCHITECTURE_REMEDIATION`
- `GOVERNANCE_ENABLEMENT`

## Out-of-scope work class

- `NEW_REQUIREMENT`

A `NEW_REQUIREMENT` is recorded with `status: DEFERRED` and transferred into the final
handoff backlog. It must not contribute to legacy capability coverage or be presented as
required to reach functional parity.

If a new feature is shipped in the Legacy product while modernization is in progress,
it becomes `LEGACY_DELTA`, not `NEW_REQUIREMENT`.
