# Code Health Governance

Architecture modernization is not syntax conversion.

Detect and remediate, when justified:

- God Components/pages;
- very large source files;
- long mixed-responsibility functions;
- huge templates/render blocks;
- business logic embedded in UI;
- direct HTTP/data orchestration in views;
- duplicated business logic;
- deep nesting/magic constants;
- cross-module internal utilities;
- migration compatibility code lacking context.

Refactorings must retain functional/visual parity. Comments should explain WHY,
constraints, Legacy compatibility and architectural decisions rather than narrating
obvious statements.
