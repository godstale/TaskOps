# TaskBoard

TaskOps 프로젝트의 작업 현황을 시각화하는 도구. TUI(터미널)와 Electron(데스크탑) 두 가지 앱을 제공합니다.

> **TaskOps와 연동**: TaskBoard는 [TaskOps](https://github.com/godstale/TaskOps)가 생성한 `taskops.db` SQLite 파일을 읽기 전용으로 참조합니다. TaskOps 없이는 동작하지 않습니다.

---

## 설치 / Install

```bash
git clone https://github.com/godstale/TaskBoard.git
cd TaskBoard
pnpm install
```

**시스템 요구사항**
- Node.js 18+
- pnpm 8+

---

## 실행 방법 / Usage

### TUI (Terminal)

```bash
# 개발 모드
pnpm --filter @taskboard/tui dev -- --path /your/taskops/root

# 빌드 후 실행
pnpm --filter @taskboard/tui build
node packages/tui/dist/index.js --path /your/taskops/root
```

**키보드 단축키**: `Tab` 화면 전환 | `R` 새로고침 | `Q` 종료

### Electron (Desktop)

```bash
# 개발 모드
pnpm --filter @taskboard/electron dev

# 빌드
pnpm --filter @taskboard/electron build

# 패키징 (installer 생성)
pnpm --filter @taskboard/electron package
```

---

## 기능 / Features

| 화면 | TUI | Electron |
|------|-----|----------|
| Dashboard | Epic/Task 계층 + 진행률 바 | 카드 기반 진행 현황 |
| Task Operations | 텍스트 operation 플로우 | ReactFlow 노드-엣지 다이어그램 |
| Resources | 리소스 파일 목록 | 리소스 목록 + 타입 배지 |
| Settings | 설정 테이블 | 설정 테이블 |

- DB 변경 감지 자동 갱신 (chokidar + 3초 폴링 fallback)
- 읽기 전용 — 데이터 수정 불가 (수정은 TaskOps CLI 또는 AI Agent가 수행)

---

## 테스트 / Test

```bash
pnpm test
```

- `@taskboard/core`: Vitest 단위 테스트 (queries, watcher)
- `@taskboard/tui`: Vitest + ink-testing-library 컴포넌트 테스트
- `@taskboard/electron`: Vitest 빌드 검증 + Playwright E2E

---

## 구조 / Repository Structure

```
taskboard/
├── packages/
│   ├── core/       # 공통 비즈니스 로직 (DB 연결, 쿼리, 파일 감시)
│   ├── tui/        # Ink 5 기반 터미널 앱
│   └── electron/   # Electron 33 + React 18 데스크탑 앱
├── fixtures/
│   └── fixture.db  # 테스트용 샘플 DB
└── docs/
    ├── requirements.md  # 기획 문서
    ├── design.md        # 설계 문서
    └── todo.md          # 구현 계획
```

---

## 관련 프로젝트 / Related

- [TaskOps](https://github.com/godstale/TaskOps) — AI Agent용 프로젝트 관리 도구 (데이터 소스)
