# ETS Planning Guide / ETS 기획 가이드

## ETS Hierarchy / ETS 계층 구조

```
Project (프로젝트)
  └── Epic (에픽) — 대규모 기능 단위
        └── Task (태스크) — 구현 단위 (parent = Epic)
              └── Task (서브태스크) — 세부 작업 (parent = Task, 구조는 동일)
  └── Objective (목표) — 마일스톤/일정 기반 목표
```

Task와 SubTask는 동일한 타입입니다. "SubTask"는 단순히 `parent_id`가 Epic이 아닌 다른 Task를 가리키는 Task입니다. 별도 명령어나 타입 구분이 없습니다.

## ID Naming Convention / ID 규칙

- Epic: `{PREFIX}-E001`, `{PREFIX}-E002`, ...
- Task/SubTask: `{PREFIX}-T001`, `{PREFIX}-T002`, ... (동일 시퀀스)
- Objective: `{PREFIX}-O001`, `{PREFIX}-O002`, ...

## Decomposition Rules / 분해 규칙

1. **Epic**: 하나의 주요 기능 영역. 3~10개의 Task를 포함하는 것이 적절합니다.
2. **Task**: 한 세션에서 완료 가능한 구체적 구현 단위. 완료 조건이 명확해야 합니다.
3. **SubTask(=Task)**: Task에 독립적으로 검증 가능한 세부 단계가 있을 때만 사용하세요.
4. **Objective**: 시간 기반 마일스톤 또는 성공 기준. Task 계층에 포함되지 않습니다.

## Plan Registration / 계획 등록

**항상 `workflow import`로 일괄 등록하세요.** 개별 `epic create` / `task create` 반복 호출은 사용하지 마세요.

### Step 1 — Workflow 생성

```bash
python -m cli --db $DB workflow create --title "계획 제목" [--source-file ./TODO.md]
```

### Step 2 — 계획을 JSON으로 변환 후 일괄 import

계획의 `[epic]`/`[task]` 구조를 아래 형식의 JSON으로 변환하여 한 번에 등록합니다:

```bash
python -m cli --db $DB workflow import {PREFIX}-W001 --structure '<json>'
```

JSON 구조:
```json
{
  "epics": [
    {
      "title": "Epic 제목",
      "description": "optional",
      "tasks": [
        {
          "title": "Task 제목",
          "description": "optional",
          "resources": [
            {"path": "./output/result.html", "type": "output", "desc": "설명"}
          ],
          "tasks": [
            {"title": "Sub-step 제목 (하위 Task)"}
          ]
        }
      ]
    }
  ]
}
```

- `tasks` 안의 `tasks` = 서브태스크 (동일 구조, 상위 Task의 하위)
- `resources`, `description`, 중첩 `tasks`는 모두 선택 사항
- `resources.type`: `input` | `output` | `reference` | `intermediate`

### 변환 예시 / Conversion Example

계획 텍스트:
```
[epic] 인증 시스템 구축
  [task] 로그인 API 구현
  [task] JWT 토큰 관리
[epic] 데이터베이스 설계
  [task] 스키마 설계
  [task] 마이그레이션 스크립트 작성
```

변환된 JSON:
```json
{
  "epics": [
    {
      "title": "인증 시스템 구축",
      "tasks": [
        {"title": "로그인 API 구현"},
        {"title": "JWT 토큰 관리"}
      ]
    },
    {
      "title": "데이터베이스 설계",
      "tasks": [
        {"title": "스키마 설계"},
        {"title": "마이그레이션 스크립트 작성"}
      ]
    }
  ]
}
```

### Step 3 — 확인

```bash
python -m cli --db $DB query show --workflow {PREFIX}-W001
```

## Plan Changes / 계획 변경

기존 계획에 일부 변경이 필요할 때 (추가/수정/삭제):

```bash
python -m cli --db $DB plan update --changes '<json>' [--workflow {PREFIX}-W001]
```

```json
{
  "create": [
    {"type": "epic", "title": "새 Epic"},
    {"type": "task", "title": "새 Task", "parent_id": "{PREFIX}-E001"}
  ],
  "update": [{"id": "{PREFIX}-T001", "title": "수정된 제목"}],
  "delete": [{"id": "{PREFIX}-T002"}]
}
```

`parent_id`는 `type: "task"` 에서 **필수**이며, 기존 Epic 또는 Task ID를 참조해야 합니다.
