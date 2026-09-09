# Execution Engine v1.3

Use the single entry point:

```bash
python scripts/modernize.py <command>
```

## Discovery-first setup

```bash
modernize doctor --repo <target>
modernize bootstrap --target <new-repo> --legacy <legacy-repo> --human-language zh-CN
modernize analyze --repo <target>
modernize assess --repo <target>
```

New bootstrap is cross-repository by design and does not select a target framework.

## Framework strategy

```bash
modernize framework recommend --repo <target>
modernize framework list --repo <target>
modernize framework select FW-VUE3 --confirmed-by human --decision ADR-TARGET-001 --repo <target>
```

## Scope

```bash
modernize scope add --id REQ-NEW-001 --type NEW_REQUIREMENT --title "..." --repo <target>
```

`NEW_REQUIREMENT` is deferred.

## Modules

```bash
modernize module create users --name "Users" --repo <target>
modernize affinity --repo <target>
```

## State

```bash
modernize transition users CURRENT_SYSTEM_MODELED --repo <target>
```

State transitions are prerequisite-checked.

## Evidence

Use `run-check`, `gate`, `visual`, and `validate`. PASS status fields without valid
runner evidence are rejected.

## Delta / cutover / handoff

```bash
modernize sync scan users --repo <target>
modernize cutover status users --repo <target>
modernize handoff build --repo <target>
modernize transition users HANDOFF_READY --repo <target>
```

`HANDOFF_READY` is the boundary for this Skill.
