# Visual Parity Governance

## Principle

If the UI has already passed product/design approval and no redesign is requested,
migration must preserve the rendered result.

Architecture modernization may change internals without changing approved output.

## Policies

| Policy | Meaning |
|---|---|
| STRICT_PRESERVE | visual output must match legacy baseline |
| STRUCTURE_PRESERVE | approved low-level styling differences allowed |
| APPROVED_REDESIGN | intentional redesign linked to approval |
| NOT_VISUAL | no meaningful visual surface |

Default to `STRICT_PRESERVE`.

## Scenario inventory

Do not capture only the initial page.

Possible states:

- default;
- loading;
- empty;
- filtered/searched;
- selected;
- expanded/collapsed;
- dialog/drawer/popover;
- error;
- disabled;
- permission-limited;
- route/deep-link state.

Use actual product behavior to choose required scenarios.

## Deterministic comparison

Legacy and target should use the same deterministic data fixture or network mock.

Stabilize:

- browser/version;
- OS/container;
- fonts;
- locale;
- timezone;
- viewport;
- device scale;
- color scheme;
- animation/caret behavior.

Do not use live changing data for strict screenshot equivalence.

## Baseline evidence

Every legacy baseline must record:

- legacy repository/commit;
- route;
- scenario/capability ID;
- fixture;
- browser environment;
- viewport/theme/locale;
- image path/hash where available.

Commit approved baselines/evidence according to project repository policy.

## Playwright pattern

Prefer `expect(page).toHaveScreenshot()` or an equivalent deterministic comparison.

Example template is in:

`assets/templates/playwright.visual.example.ts`

## Masking

Mask only unavoidable non-business nondeterminism such as a clock tick or random
diagnostic ID.

Do not mask:

- business data;
- buttons;
- labels;
- monetary values;
- meaningful chart content;
- icons;
- layout differences.

"Mask the diff" is not a valid migration fix.

## Baseline update rule

The agent must never run snapshot update merely because a migration diff fails.

A baseline change requires one of:

- explicit `APPROVED_REDESIGN`;
- approved visual bug fix;
- explicit visual-test-environment migration.

Record the decision.

## Diff triage

When visual diff fails, classify likely source:

- layout/box model;
- typography/font;
- spacing;
- token/color;
- component variant;
- icon/asset;
- rendering/environment;
- fixture/data mismatch;
- animation/async state.

Fix the cause and rerun.

## Gate

A `STRICT_PRESERVE` capability cannot pass Visual Parity with an unresolved meaningful
diff unless there is a documented waiver/approved redesign.
