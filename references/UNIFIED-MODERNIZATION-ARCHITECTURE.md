# Unified Modernization Architecture

The architecture goal is stable across frameworks.

## AI-native

- repository self-describes purpose and architecture;
- commands are machine-discoverable;
- architectural rules are machine-readable;
- durable state does not depend on chat history.

## Capability-first

Capabilities are recovered before target code is organized. Every reproduced capability
has ownership, source evidence, target ownership and parity evidence.

## Module-oriented and integration-first

Each business module should define:

- ownership;
- capabilities;
- public integration surface;
- dependencies;
- routes/runtime configuration where applicable;
- test/build boundaries;
- machine manifest;
- human guide.

Direct deep imports into another business module's internals are prohibited by default.
Independent deployment is optional; explicit integration boundaries are not.

## Code health

Modernization may split large files, God Components, mixed responsibilities, duplicated
logic and direct HTTP-in-view patterns. Refactoring must preserve product behavior unless
an approved product decision says otherwise.

## Documentation

Machine-readable governance is canonical for deterministic facts. Human-readable docs
explain purpose, reasoning, architecture, modules and operating procedures.

## Framework adapters

Framework adapters translate this constitution into framework-specific patterns. Vue,
React and Next.js may use different routers/state/rendering/build mechanics without
changing the architecture principles above.
