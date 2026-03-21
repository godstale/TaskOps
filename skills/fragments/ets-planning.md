# ETS Planning Guide / ETS 기획 가이드

## ETS Hierarchy / ETS 계층 구조

```
Project (프로젝트)
  └── Epic (에픽) — 대규모 기능 단위
        └── Task (태스크) — 구현 단위
              └── SubTask (서브태스크) — 세부 작업
  └── Objective (목표) — 마일스톤/일정 기반 목표
```

## ID Naming Convention / ID 규칙

- Epic: `{PREFIX}-E001`, `{PREFIX}-E002`, ...
- Task/SubTask: `{PREFIX}-T001`, `{PREFIX}-T002`, ... (동일 시퀀스)
- Objective: `{PREFIX}-O001`, `{PREFIX}-O002`, ...

Task and SubTask share the same ID sequence. A SubTask is simply a Task whose parent is another Task.

## Decomposition Rules / 분해 규칙

1. **Epic**: One major feature or initiative. Should contain 3-10 Tasks.
2. **Task**: A concrete implementation unit completable in one session. Should have a clear done condition.
3. **SubTask**: Use only when a Task has distinct, independently verifiable sub-steps.
4. **Objective**: Time-based milestones or success criteria. Not part of the task hierarchy.

## Planning Steps / 기획 단계

1. Analyze the project requirements
2. Create Epics for each major feature area
3. Break each Epic into Tasks (implementation units)
4. Add SubTasks only if a Task has clearly separable steps
5. Create Objectives for milestones and deadlines
6. Define workflow order and dependencies

## CLI Commands for Planning / 기획용 CLI 명령어

> **Always pass `--workflow` when creating epics, tasks, and objectives individually.**
> Items without a workflow_id are invisible in TaskBoard's Workflow view and cannot be filtered per workflow.
> When using `workflow import`, workflow_id is set automatically — no need to pass it separately.

```bash
# Create Epic (always specify workflow)
python -m cli epic create --title "Feature Name" --description "Details" --workflow {PREFIX}-W001

# Create Task under Epic (always specify workflow)
python -m cli task create --parent {PREFIX}-E001 --title "Implementation unit" --workflow {PREFIX}-W001

# Create SubTask under Task (always specify workflow)
python -m cli task create --parent {PREFIX}-T001 --title "Sub-step" --workflow {PREFIX}-W001

# Create Objective (associate with workflow if relevant)
python -m cli objective create --title "MVP Complete" --milestone "Core features done" --workflow {PREFIX}-W001
python -m cli objective create --title "Demo Day" --due-date 2026-04-01

# List by workflow
python -m cli epic list --workflow {PREFIX}-W001
python -m cli task list --workflow {PREFIX}-W001
```
