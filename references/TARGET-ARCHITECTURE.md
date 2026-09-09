# Target Architecture

v1.3 uses a **unified modernization architecture**, not a framework-specific target
architecture.

Canonical rules live in:

```text
governance/modernization-constitution.yaml
governance/architecture.yaml
governance/modules.yaml
governance/framework-strategy.yaml
```

## Stable requirements

- AI-native/self-describing repository.
- Capability-first ownership.
- Business modules with machine manifests and human docs.
- Public module integration contracts.
- Controlled cross-module dependencies.
- Independent test boundaries and preferred build boundaries.
- Governed data-access/state/UI responsibilities.
- Code-health remediation.
- Evidence-backed verification.

## Framework adapters

Vue/React/Next.js/custom adapters express Router, State, Build and rendering mechanics.
They do not redefine module ownership, documentation/evidence requirements or the
new-requirement scope boundary.

A Dashboard may still use Domain Applications if the project chooses that concrete
module runtime model, but it is no longer assumed by the generic Skill.
