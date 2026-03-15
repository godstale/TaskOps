# TaskBoard

TaskOps 프로젝트의 작업 현황을 시각화하는 TUI와 Electron 두 앱.

## 실행 방법

### TUI (Terminal)
```bash
# 개발 모드
cd taskboard && pnpm --filter @taskboard/tui dev -- --path /your/taskops/root

# 빌드 후 실행
cd taskboard && pnpm --filter @taskboard/tui build
node packages/tui/dist/index.js --path /your/taskops/root
```

### Electron (Desktop)
```bash
# 개발 모드
cd taskboard && pnpm --filter @taskboard/electron dev

# 빌드
cd taskboard && pnpm --filter @taskboard/electron build

# 패키징 (installer 생성)
cd taskboard && pnpm --filter @taskboard/electron package
```

## 테스트
```bash
cd taskboard && pnpm test
```
