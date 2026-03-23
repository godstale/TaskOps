# Execution Guide / TaskOps 실행 가이드

> TaskOps replaces `executing-plans`. Task state and progress are stored in the TaskOps DB — no TodoWrite is used.

**Announce at start:** "I'm using TaskOps to execute this workflow."

## Step 1: Load and Review Workflow

```bash
python -m cli query show --workflow {PREFIX}-W001
python -m cli setting list --workflow {PREFIX}-W001
```

Review critically:
- Are all required settings configured? (check `setting list --workflow {PREFIX}-W001`)
- Are there tasks with unclear done-conditions?
- Are there external dependencies that must be resolved first?

If concerns exist → raise them with the user before starting execution.

## Step 2: Execute Tasks (Repeat per Task)

Find the next task:
```bash
python -m cli workflow next --workflow {PREFIX}-W001
```

For each task, follow this exact sequence:

**2a. Start the task**
```bash
python -m cli task update {T-ID} --status in_progress
python -m cli op start {T-ID} --platform claude_code
```

**2b. Work on the task** — implement, test, review

**2c. Record progress at meaningful milestones**
```bash
python -m cli op progress {T-ID} --summary "Implemented login endpoint, tests passing"
```
Call `op progress` after: finishing a component, creating a key file, passing tests, resolving a bug.

**2d. Register all artifacts (HARD GATE — required before marking done)**

Register every file created, modified, or referenced during the task:
```bash
python -m cli resource add {T-ID} --path ./output/report.html --type output --desc "Final report"
python -m cli resource add {T-ID} --path ./tmp/analysis.csv --type intermediate --desc "Raw data"
```

Verify registration:
```bash
python -m cli resource list --task {T-ID}
```

> ⛔ If list is empty or incomplete → return to resource add. Do NOT proceed.

**2e. Mark task done**
```bash
python -m cli task update {T-ID} --status done
python -m cli op complete {T-ID} --summary "Login API complete. All tests pass."
```

## Step 3: When to Stop and Ask for Help

Stop immediately when:
- A required dependency is missing (API key, tool, external service)
- A test fails repeatedly with no clear fix
- A task instruction is ambiguous
- `workflow next` returns nothing but tasks are not all done

**Ask for clarification — do not guess or skip steps.**

## Step 4: Handling Interruptions

```bash
python -m cli task update {T-ID} --status interrupted --interrupt "Waiting for API key"
python -m cli op interrupt {T-ID} --summary "Blocked: external dependency unresolved"
```

## Step 5: After All Tasks Complete

```bash
python -m cli query status --workflow {PREFIX}-W001
```

Then offer the user:
1. **Export summary** — `workflow export {PREFIX}-W001` (creates TODO.md snapshot)
2. **Start next workflow** — if more work phases planned
3. **Archive** — workflow remains in DB; no action needed unless cleanup requested
