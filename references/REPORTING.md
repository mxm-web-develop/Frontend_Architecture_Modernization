# Reporting Standard

Reports should explain the system in natural language while using tables heavily for
enumerated facts.

## Writing rule

Use prose for:

- interpretation;
- reasons;
- trade-offs;
- risk;
- recommendation;
- decisions.

Use tables for:

- modules/domains;
- capabilities/functions;
- routes;
- APIs;
- dependencies;
- responsibility findings;
- architecture issues;
- mappings;
- migration/parity status;
- visual scenarios;
- before/after metrics.

Do not repeat table rows in prose.

## Master report

```text
1. Executive Summary
2. Legacy System Overview
3. Module & Domain Analysis
4. Functional Capability Inventory
5. Route Analysis
6. API & Data Flow Analysis
7. Frontend / BFF / Backend Responsibility Analysis
8. Dependency & Coupling Analysis
9. Target Architecture
10. Legacy -> Target Mapping
11. Architecture Remediation Backlog
12. Migration Strategy & Sequence
13. Risks & Known Unknowns
14. Migration Progress
15. Functional Parity
16. Visual Parity
17. Architecture / Governance Status
18. Before / After Comparison
```

## Required useful tables

### Legacy modules

| Legacy module | Route | Files | Pages | Capabilities | APIs | Cross deps | Complexity | Proposed target |
|---|---|---:|---:|---:|---:|---:|---|---|

### Capabilities

| Capability ID | Function | Legacy entry | Behavior | Permission | Disposition | Target |
|---|---|---|---|---|---|---|

### Routes

| Route ID | Legacy route | Page | Target domain | Target route | Runtime flag | Status |
|---|---|---|---|---|---|---|

### APIs

| API | Method | Modules | Capabilities | Frontend computation | Cross-domain aggregation | Recommendation |
|---|---|---|---|---|---|---|

### Responsibility

| Logic ID | Current behavior | Current owner | Problem | Recommended owner | Strategy |
|---|---|---|---|---|---|

### Dependencies

| Source | Target | Type | Count | Risk | Target treatment |
|---|---|---|---:|---|---|

### Issues

| Issue ID | Type | Scope | Severity | Evidence | Recommendation |
|---|---|---|---|---|---|

### Visual parity

| Scenario | Capability | Policy | Legacy baseline | Target | Diff | Status |
|---|---|---|---|---|---:|---|

### Source-target

| Legacy | Type | Target | Target type | Treatment | Reason |
|---|---|---|---|---|---|

### Before/after

| Metric | Legacy | Target/current | Change |
|---|---:|---:|---:|

Only report measurable metrics or mark estimates clearly.

## Required distinctions

Visibly distinguish:

- Migration
- Architecture remediation
- Functional change

Functional change requires explicit decision evidence.

## Unknowns

Every report with unresolved unknowns includes:

| Unknown ID | Finding | Why uncertain | Risk | Required action/evidence |
|---|---|---|---|---|

## Evidence standard

Avoid vague statements like "the module is messy."

Prefer:

> User Detail coordinates six requests with three sequential dependencies and repeats
> the same role/organization join in two pages.

Then explain the architecture implication.

## v1.5 report evidence requirements

The system report must distinguish:

- confirmable Domain Candidates from Structural Hints;
- resolved APIs from unresolved request signals;
- total import count from cross-area/package dependency summaries;
- remediation type from the actual source file when available.

Do not collapse unresolved discovery debt into an empty table.
