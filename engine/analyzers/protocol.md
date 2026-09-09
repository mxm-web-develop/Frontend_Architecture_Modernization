# Analyzer Adapter Protocol

Every framework analyzer adapter must output a normalized raw-analysis directory.

Required files:

- `analysis-manifest.json`
- `project.json`
- `routes.json`
- `imports.json`
- `apis.json`
- `state.json`
- `inventory.json`

Every extracted fact should include:

```json
{
  "source": {"file": "src/...", "start_line": 1, "end_line": 3},
  "extraction": {
    "method": "ast",
    "confidence": 1.0,
    "level": "STATIC_CONFIRMED"
  }
}
```

Allowed evidence levels:

- `STATIC_CONFIRMED`
- `STATIC_INFERRED`
- `HEURISTIC`
- `RUNTIME_CONFIRMED`
- `UNKNOWN`

Adapters must not convert dynamic or unparseable behavior into false certainty. Such
facts must be emitted as `UNKNOWN` / `NEEDS_RUNTIME_EVIDENCE` or omitted with a
recorded analyzer warning.
