# Frontend Responsibility Governance

The purpose is not to force logic out of the browser. It is to prevent legacy
frontend architectural mistakes from being faithfully recreated.

## Review signals

Analyze:

- API request fan-out;
- sequential dependency depth;
- client-side joins;
- repeated aggregation/transformation;
- cross-domain aggregation;
- authoritative business rules;
- pricing/billing calculations;
- security/permission decisions;
- transaction-like multi-call behavior;
- duplicated orchestration across screens;
- presentation-only data shaping.

## Ownership guidance

| Target | Appropriate work |
|---|---|
| FRONTEND | UI state, formatting, interaction, local view-model transforms |
| BFF_RECOMMENDATION | UI-specific orchestration/aggregation/response shaping |
| BACKEND_RECOMMENDATION | authoritative business rules, consistency, security decisions |
| PLATFORM_GATEWAY_RECOMMENDATION | routing/rate limits/shared infrastructure |

Multiple API calls alone are not evidence for a BFF.

## Frontend-only project scope

When backend source is out of scope:

- do not pretend to validate backend implementation;
- do not edit backend contracts unless explicitly provided;
- record external recommendation and expected frontend-facing contract;
- choose a frontend migration strategy.

## Migration strategies

### FIX_BEFORE_MIGRATE
Use for correctness/security/authoritative logic where preserving frontend ownership
would reproduce a critical flaw.

### MIGRATE_WITH_ADAPTER
Preferred when frontend migration should proceed before external API remediation.

```text
Feature
  -> Repository interface
     -> Legacy adapter (now)
     -> BFF/new API adapter (later)
```

### MIGRATE_AS_IS
Use when current ownership is acceptable or remediation is not justified.

## Finding format

Always write:

`Observation -> Evidence -> Impact -> Recommendation -> Migration Strategy`

Avoid vague "should use BFF" statements.
