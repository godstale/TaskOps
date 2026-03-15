# BUSINESS LOGIC

## About TaskOps

TaskOps는 사용자가 입력한 프로젝트 기획을 ETS(Epic-Task-SubTask) 구조로 관리할 수 있도록 변환해주고,
이렇게 작성된 계획을 모니터링 할 수 있도록 지원하는 AI Agent 용 스킬입니다.


## 프로젝트 실행 계획 구체화

TaskOps 는 사용자가 실행하고 싶은 프로젝트의 개요를 설명하면 AI Agent 를 이용해서 ETS(Epic-Task-SubTask) 구조로 변환합니다.
변환된 ETS 컴포넌트들은 AI Agent 가 순차적으로 처리할 수 있도록 처리 순서 기반으로 정렬되어야 합니다. 이를 workflow 라 합니다.
ETS 컴포넌트와 workflow 는 기존에 AI Agent 가 작성하는 TODO.md 파일과 유사하지만 추가적인 정보가 포함됩니다.
TaskOps 는 작성된 작업 계획을 기반으로 프로젝트를 관리하고, 실행하고, 모니터링하는 도구를 제공합니다.
이를 위해 Task ID 를 기반으로 SQLite DB 를 사용합니다.



## Project Component

프로젝트 구현을 위한 ETS 컴포넌트 정의와 특징 명세

- 프로젝트 컴포넌트
  - Project: 프로젝트 인스턴스를 의미. 프로젝트의 최상위 단위로 모든 프로젝트 컴포넌트와 에셋을 포함합니다.
  - Epic: 프로젝트를 세부 작업을 구현하기 위해 만든 최상위 작업 계획입니다. Epic은 실행 가능한 컴포넌트가 아닙니다.
  - Task: Epic을 구성하는 작업. 자식 task(subtask) 를 가질 수 있습니다. Task는 실행 가능한 컴포넌트입니다.
  - SubTask: 태스크를 구성하는 작업. Task와 본질적으로 동일하며, 부모 task 를 가진다는 점만 다릅니다. SubTask는 실행 가능한 컴포넌트입니다.
  - Workflow: Task, SubTask 에 정의된 작업을 실행하기 위한 작업 계획
  - Objective: 프로젝트에 설정한 목표 지점. 이벤트, 일정 등을 표시하는 용도로 사용.

- ETS 컴포넌트의 동작 특성
  - 프로젝트는 하나의 작업 폴더와 연동되어 있습니다.
  - 모든 ETS 컴포넌트는 프로젝트 특성(Project Properties)을 가집니다
  - Objective 는 프로젝트 관리 목적의 표식으로 작업의 진행과는 직접적인 관련이 없습니다.
  - Project ~ SubTask 는 수직적인 계층 구조를 가지지만, Objective는 자유롭게 지정할 수 있는 '프로젝트의 목표/이벤트'입니다.


## Project Assets: 프로젝트 지원 요소

프로젝트 구현 및 실행에 필요한 개념과 리소스.
TaskOps 는 AI Agent 가 workflow 수행을 위해 필요한 파일이나 생성된 자료, 메모리를 작업 폴더에 저장할 수 있도록 요청합니다.

- Working folder: 작업 폴더
  - 프로젝트는 하나의 작업 폴더와 연동되어 있습니다.
  - 프로젝트 폴더는 AI Agent 가 참조하는 md 파일과 사용자가 프로젝트 모니터링할 때 사용할 SQLite DB 파일을 포함합니다.

- Resource
  - 작업의 시작시 전달되어야 할 정보, 작업 종료시 생성되는 정보
  - 프로젝트에 사용되는 내, 외부의 문서 또는 작성된 코드
  - 기타 파일 형태의 모든 리소스
  - 리소스는 Task ID 를 파일명 prefix 로 사용


## Project Properties: 프로젝트 컴포넌트에 사용되는 특성

- Type
  - 프로젝트 컴포넌트의 타입을 나타냅니다.
  - 타입값은 Project, Epic, Task, SubTask, Objective 로 정의됩니다.

- Status
  - 프로젝트 컴포넌트의 현재 상태를 나타냅니다.
  - 상태값은 To do, In progress, Interrupted, Done, Cancelled 로 정의됩니다.

- 상위 작업
  - Task의 상위 작업을 나타냅니다.

- 하위 작업
  - Task의 하위 작업을 나타냅니다.

- TODO (Component)
  - 작업의 세부적인 구현 계획

- Interrupt
  - 작업이 오류로 중단되거나, 사용자의 입력이 필요한 상황인 경우 해당 내용을 상세히 기재한다.

- Description
  - ETS 컴포넌트 또는 작업에 대한 부가적인 설명


## Logger
- 프로젝트 컴포넌트의 작업 이력을 기록하는 기능
- SQLite DB의 operations 테이블을 이용해서 작업 이력을 기록

## Settings
- Project settings
  - 스킬이나 AI Agent 설정, 스킬 등 사용자 지침을 저장

