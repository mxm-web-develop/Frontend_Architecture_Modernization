# Repository Agent Entry Point

This repository is a brownfield frontend modernization target governed by
`frontend-architecture-modernization` until it reaches `HANDOFF_READY`.

## First steps

1. Read `governance/project.yaml`.
2. Read `governance/modernization-constitution.yaml`.
3. Read `governance/framework-strategy.yaml`.
4. Read `governance/modules.yaml` and the relevant module manifest/README.
5. Read `governance/commands.yaml`.
6. Run the logical `modernize status --repo .` command through the active Skill runtime. Do not hard-code a Cursor/Codex installation path.

## Scope boundary

During modernization:

- reproduce Legacy product behavior;
- improve architecture/code/governance internally;
- preserve approved UI unless an explicit redesign decision exists;
- classify Target-only net-new product requests as `NEW_REQUIREMENT` and defer them.

Do not implement net-new product requirements under the modernization Skill.

## Architecture rules

- Capability-first reproduction.
- Explicit module ownership and public integration contracts.
- No cross-module internal imports by default.
- Machine-readable governance is canonical for deterministic facts.
- Human-readable docs follow project language governance.
- Gate PASS requires verifiable evidence.

## After HANDOFF_READY

The modernization lifecycle is complete. Normal feature-development Agents/Skills may
continue using this repository's governance, module manifests, commands, ADRs and handoff
package without relying on modernization chat history.
