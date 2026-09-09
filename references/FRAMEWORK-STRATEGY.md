# Framework Strategy

Framework choice is an implementation strategy under a fixed modernization architecture.

## Rules

1. Bootstrap leaves framework strategy `UNDECIDED`.
2. Discovery detects the current framework.
3. `framework recommend` may generate multiple options and mark one `RECOMMENDED`.
4. Recommendation does not equal selection.
5. Only explicit human confirmation may set `status: CONFIRMED`.
6. The user may preserve the current framework or choose another adapter.
7. Framework adapters may adjust router/state/rendering/build details but may not weaken
   the unified modernization constitution without an explicit ADR.
