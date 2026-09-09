# Architecture Assessment

Assess the Legacy system against the unified modernization constitution.

Core dimensions:

- capability/module cohesion;
- dependency direction and cross-module coupling;
- state isolation;
- API/data-flow ownership;
- build/runtime boundaries;
- module integration surfaces;
- testability;
- code health and large mixed-responsibility files;
- documentation and AI-development readiness;
- framework lifecycle/maintenance risk.

Scores are diagnostic signals, not automatic architecture decisions. Findings must point
to evidence and produce remediation work, not ungrounded redesign.

## v1.5 API assessment invariant

`apis == 0` is not a positive architecture signal.

If static discovery sees HTTP/API calls but cannot resolve any endpoint:

```text
api_data_flow.score = null
finding = API_DISCOVERY_INCOMPLETE
```

If some endpoints are resolved but dynamic calls remain, record
`API_DISCOVERY_PARTIAL` and preserve the unresolved evidence.

## v1.5.1 partial-discovery scoring

If any API request signals remain unresolved, `api_data_flow.score` must be null.
The finding remains `API_DISCOVERY_PARTIAL`. Discovery coverage and architecture
quality must not be conflated.
