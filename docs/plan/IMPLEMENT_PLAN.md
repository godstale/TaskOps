# TaskOps 

TaskOps 는 Claude Code, Gemini CLI 와 같은 AI Agent 에서 사용할 수 있는 skill 형태로 작성된 Task 관리 도구입니다.
TaskOps 스킬은 사용자가 실행하고 싶은 작업의 개요를 설명하면 AI Agent 를 이용해서 작업을 ETS(Epic-Task-SubTask) 구조로 변환합니다.
작업을 ETS 구조로 나눔으로써 복잡한 문제를 Divide & Conquer 방식으로 해결할 수 있도록 돕습니다.

---

## TaskOps 동작 방식

사용자가 프로젝트를 시작하거나 작업을 계획을 작성하는 경우, TaskOps 스킬은 사용자의 요청을 아래와 같이 처리한다.

1. 사용자의 요청을 분석해서 큰 틀의 프로젝트 실행 계획을 세운다. (Epic) Epic은 실행 가능한 컴포넌트가 아니다.
2. Epic을 구현하기 위해 필요한 세부 작업들을 Task 단위로 등록한다. (Task) Task는 실행 가능한 컴포넌트이다.
3. Task 작업이 큰 경우 필요에 따라 SubTask 단위로 나눈다. (SubTask) SubTask는 Task 와 본질적으로 동일한 컴포넌트이다.

이 과정은 사용자의 요청을 분석해서 해야할 작업을 TODO.md 파일에 체크박스 형태로 기록하는 과정과 유사하다.
TaskOps 는 이 과정을 체계적으로 관리하기 위해 ETS 구조를 사용하며, 이를 순차적으로 처리하기 위한 workflow 를 정의한다.
따라서 TaskOps 는 Task 단위로 프로젝트를 관리하고 수정, rollback 등의 작업을 효율적으로 수행한다.

TaskOps 가 프로젝트를 생성하고 관리하는 과정은 크게 4가지로 나뉜다.

- 프로젝트 초기화:
  - TaskOps 를 이용해서 프로젝트 또는 작업을 생성하는 경우 초기화 과정을 수행한다.
  - TaskOps 폴더를 생성하고 초기화 작업을 수행한다.
  - SQLite DB, Claude Hooks 와 같은 모니터링 도구를 생성한다. 

- 프로젝트 기획: 
  - 세부 실행 계획을 ETS(Epic-Task-SubTask) 구조로 만든다.
  - 세부 실행 계획을 만들 수 있을 만큼 충분한 정보가 없다면 웹 검색을 통해 얻거나, 사용자에게 질문을 하여 구체화한다.
  - ETS 컴포넌트는 모두 고유의 ID 값을 할당한다. 이 ID 값은 컴포넌트의 상태를 조회하거나 수정할 때 index 로 사용된다. (예 - TOS-001)
  - ETS 컴포넌트의 처리 순서를 workflow 로 정의한다.

- 프로젝트 관리:
  - TaskOps 를 이용해서 사용자, AI Agent 는 workflow 와 프로젝트 기획 상태(ETS)를 조회할 수 있다. (TODO.md, SQLite DB)
  - TaskOps 는 작업의 처리 상태를 파악해서 업데이트하고 이를 모니터링할 수 있는 방법을 제공한다. (SQLite DB)
  - 사용자, AI Agent 는 필요에 따라 workflow 와 ETS 컴포넌트를 수정할 수 있다. (TODO.md, SQLite DB)
  - 그리고 수정된 workflow 와 ETS 컴포넌트를 기반으로 작업 처리를 다시 시작할 수 있다.
  - SETTINGS.md 파일을 이용해서 프로젝트 설정을 저장한다. 이 파일은 프로젝트 작업 수행 중 AI Agent 가 참조할 수 있도록 사용자의 지침을 저장한다.

- 프로젝트 실행:
  - 사용자가 프로젝트의 작업 처리를 진행하면 workflow 와 TODO(ETS) 리스트를 AI Agent 가 참조할 수 있도록 전달한다.
  - AI Agent 가 작업을 처리하는 동안 처리 진행상황을 모니터링 할 수 있도록 AI agent에 요청한다. 
    - 시작시간, 완료시간, 진행상황 요약, 결과 요약, sub agent 사용 여부, sub agent 사용 결과 등

---

## TaskOps 리소스 관리

TaskOps 는 AI Agent 가 프로젝트 작업 처리를 위해 참조해야 하는 파일들을 관리한다. (md 파일)
TaskOps 는 사용자(또는 플러그인)가 프로젝트를 모니터링하기 위해 필요한 파일들을 관리한다. (SQLite DB)

---

## TaskOps 초기화 및 파일 구조

- TaskOps 스킬이 사용될 때 TaskOps 폴더를 생성하고, 프로젝트 이름의 하위 폴더를 생성한다.
- 프로젝트 폴더에는 AGENTS.md 파일을 생성하고, 여기에 생성되는 파일이나 리소스에 대한 요약 정보를 포함한다.
- 아래 파일들은 AI Agent 가 프로젝트 작업 처리를 위해 참조해야 하는 파일이다
  - TODO.md 파일은 프로젝트의 workflow 와 ETS 정보를 포함한다.
  - TASK_OPERATIONS.md 파일은 프로젝트의 작업 처리 이력을 포함한다.
- 프로젝트 폴더에는 SQLite DB 파일이 생성된다. TaskOps 스킬은 SQLite DB 관리를 위한 스크립트를 포함해야 한다.
- 아래는 sqlite DB 에 저장되어야 하는 데이터이다.
  - tasks 테이블은 모든 ETS Component 의 상세정보와 상태가 저장되는 테이블이다.
  - operations 테이블은 AI Agent 의 작업 처리 진행상황을 모니터링하기 위한 테이블이다.
    - AI Agent 가 작업을 시작할 때 새로운 레코드를 생성하고 시간을 기록한다.
    - 작업의 주요 단계마다 생성한 레코드에 진행상황을 업데이트 한다.
    - 작업이 완료되면 완료시간을 기록하고, 작업 결과물 정보와 상태를 업데이트 한다.

---

## 기타









