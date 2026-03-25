# Setting Guide / TaskOps 설정 가이드

## What Settings Are For

Settings record **required dependencies** for a workflow — specific tools, external services, APIs, or CLIs that must be configured before or during execution.

Use settings to declare and check:
- External API credentials needed (`openai_api_key_configured: true/false`)
- CLI tools required (`docker_available: true`)
- Skill-level preferences (`tdd_required: true`, `autonomy_level: high`)
- Platform-specific behavior (`commit_style: conventional`)

Settings are NOT for task output data. Use `resource add` for artifacts.

## Built-in Settings (created by `init`)

| Key | Default | Description |
|-----|---------|-------------|
| `autonomy_level` | `moderate` | Agent autonomy: `low` \| `moderate` \| `high` |
| `commit_style` | `conventional` | Commit message format |
| `use_subagent` | `true` | Allow sub-agent dispatch |
| `parallel_execution` | `true` | Allow parallel task execution |
| `progress_interval` | `major_steps` | `every_tool` \| `major_steps` \| `start_end_only` |

## Commands

> ⚠️ `--workflow <W-ID>` is **required** for `set`, `get`, and `delete`. Always provide a real workflow ID — never omit or pass an empty string.

```bash
# Register a dependency or configuration value
python -m cli --db $TASKOPS_DB setting set <key> <value> --workflow PRJ-MP --desc "<description>"

# Read a setting
python -m cli --db $TASKOPS_DB setting get <key> --workflow PRJ-MP

# List all settings (--workflow optional, omit to show all)
python -m cli --db $TASKOPS_DB setting list [--workflow PRJ-MP]

# Remove a setting
python -m cli --db $TASKOPS_DB setting delete <key> --workflow PRJ-MP
```

**Correct usage:**
```bash
# ✅ Always pass a real workflow ID
python -m cli --db $TASKOPS_DB setting set autonomy_level high --workflow PRJ-MP

# ❌ Never omit --workflow or pass empty string for set/get/delete
python -m cli --db $TASKOPS_DB setting set autonomy_level high   # missing --workflow → error
```

## Pattern: Pre-Execution Dependency Check

Before starting execution, verify required dependencies are ready:

```bash
python -m cli --db $TASKOPS_DB setting list --workflow PRJ-MP
```

If a required tool or service is not yet available, block execution:

```bash
# Record as unresolved — do not start dependent tasks
python -m cli --db $TASKOPS_DB setting set stripe_api_key_configured false \
    --workflow PRJ-MP --desc "Required for T005 (Payment processing). Get key from team Slack."
```

Update when resolved:
```bash
python -m cli --db $TASKOPS_DB setting set stripe_api_key_configured true \
    --workflow PRJ-MP --desc "Configured 2026-03-22. Stored in .env"
```
