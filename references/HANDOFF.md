# Handoff

`HANDOFF_READY` is the Skill boundary.

The final new repository must allow another Agent or development Skill to implement new
requirements without modernization chat history.

Required handoff package:

```text
handoff/
  README.md
  agent-start-here.md
  system-context.yaml
  module-index.yaml
  architecture-summary.md
  development-guide.md
  known-issues.yaml
  deferred-work.yaml
  new-requirements.yaml
```

Handoff validation checks architecture/governance files, commands, framework strategy,
module manifests/docs, unresolved work and the post-modernization requirement backlog.
