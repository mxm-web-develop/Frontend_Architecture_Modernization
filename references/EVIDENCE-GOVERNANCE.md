# Evidence Governance

A gate is not true because YAML says `PASS`.

## Command evidence

Functional, architecture and traceability gates use runner-produced command evidence
with command, command-key, exit code, timestamps, Git commit, stdout/stderr and hashes.
`modernize validate` re-checks evidence artifacts.

## Visual evidence

Visual PASS references Visual Harness `result.json`. Validation checks required
scenarios, result status, Legacy/Target/Diff PNG existence, PNG signatures and hashes.

## MODERNIZED

A Domain can reach `MODERNIZED` only when required gates and capability parity have
verifiable evidence.

## HANDOFF_READY

Handoff additionally requires repository governance, discoverable commands, target
module manifests/docs and the generated handoff package. New product requirements must
remain deferred.
