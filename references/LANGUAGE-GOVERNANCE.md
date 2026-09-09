# Language Governance

## Purpose

Human-readable project documentation must use one configured language so long-running
AI work does not drift between Chinese and English across sessions.

## Project configuration

`governance/project.yaml` is authoritative:

```yaml
language:
  interaction: zh-CN
  human_documentation: zh-CN
  enforce_human_documentation: true
  machine_protocol: en
  code_identifiers: en
  code_comments: zh-CN
  governed_markdown:
    - docs
    - migration
```

Rules:

- Conversational responses follow `interaction` unless the user explicitly requests another language.
- Human-readable Markdown under configured governed roots MUST declare the same `language` in frontmatter.
- Machine-readable keys, schema properties, enums, stable IDs and Git trailers remain English.
- Code identifiers remain English.
- Human-readable descriptions, recommendations, table headers and comments use the project language.
- `modernize validate` fails when governed Markdown is missing language frontmatter or disagrees with the configured language.

## Example governed document

```markdown
---
id: MIG-USERS-001
type: migration-plan
status: active
language: zh-CN
---

# Users Domain 迁移计划
```

Changing `human_documentation` is a governance change. Update active governed documents
through an explicit documentation-language migration rather than silently mixing languages.
