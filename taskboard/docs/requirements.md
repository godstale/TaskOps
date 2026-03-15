# TASK BOARD

---

## About TaskBoard

TaskBoard는 TaskOps에서 관리하는 프로젝트의 작업을 시각적으로 표현하는 도구입니다.
TaskBoard는 TaskOps의 DB를 참조하여 프로젝트의 작업을 분석하고, 사용자가 확인하기 편한 대시보드 방식으로 구현합니다.
이를 위해 npx 로 실행할 수 있는 typescript 프로젝트를 구현합니다.

---

## TaskBoard 실행 과정

1. TaskBoard 가 실행되면 TaskOps가 생성한 TaskOps 폴더를 선택하는 화면이 표시됩니다.
2. TaskOps 폴더를 선택하면, 다시 내부의 프로젝트를 선택합니다.
3. TaskBoard 는 선택한 프로젝트의 SQLite DB를 참조하여 프로젝트의 작업을 분석합니다.
4. TaskBoard 는 main - Dashboard 화면을 표시합니다.

---

## TaskBoard GUI 구성

Task 보드는 아래와 같은 메뉴를 제공하며, 각 메뉴는 하나의 화면을 구성합니다.
- Main - Dashboard (대시보드)
  - 현재 프로젝트의 ETS(Epic-Task-SubTask) 구조와 Workflow를 확인할 수 있습니다.
  - 또한 현재 프로젝트 구현(실행) 상황을 간략하게 표시합니다.
  - 에러 또는 작업이 중단된 경우 에러 메시지를 표시합니다.
  - Workflow 구현 예시는 `docs/img/example_project_workflow.png`를 참고한다.
- Task Operations (작업 현황)
  - 전체 task 리스트 및 상태를 볼 수 있습니다.
  - 특정 task 를 선택했을 때 task 의 operation flow 를 볼 수 있습니다.
  - operation flow 구현 예시는 `docs/img/example_task_operations.png`를 참고한다.
- Resources (리소스)
  - Task 작업 수행 후 생성된 resource 파일들의 목록을 보여줍니다.
- Settings (설정)
  - TaskOps 설정 파일입니다.


## 구현 요구사항

- react best practice 스킬과 같이 TaskBoard 를 구현할 때 참고할 수 있는 아키텍처를 확인하고 적용합니다.
- TDD 를 적용하는 것을 원칙으로 합니다. 이를 위해 관련된 스킬을 사용합니다.
- Design guide 스킬을 사용해서 모던한 GUI 디자인을 구현합니다.
- TaskOps 스킬이 배포될 때 TaskBoard도 함께 배포될 수 있도록 TaskOps root 폴더 아래에 TaskBoard 폴더를 생성하고, 여기에 코드를 구현합니다.
- 
