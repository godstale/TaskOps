import chokidar from 'chokidar'
import fs from 'fs'

type UnwatchFn = () => void

/**
 * DB 파일 변경을 감시한다.
 * chokidar(fs.watch 기반) 우선, 실패 시 3초 폴링으로 fallback.
 * @returns unwatch 함수
 */
export function watch(dbPath: string, onChange: () => void): UnwatchFn {
  let watcher: ReturnType<typeof chokidar.watch> | null = null
  let pollTimer: ReturnType<typeof setInterval> | null = null
  let lastMtime = 0

  try {
    watcher = chokidar.watch(dbPath, {
      persistent: true,
      usePolling: false,
      ignoreInitial: true,
    })
    watcher.on('change', onChange)
    watcher.on('error', () => startPolling())
  } catch {
    startPolling()
  }

  function startPolling() {
    if (pollTimer) return
    pollTimer = setInterval(() => {
      try {
        const { mtimeMs } = fs.statSync(dbPath)
        if (lastMtime && mtimeMs !== lastMtime) onChange()
        lastMtime = mtimeMs
      } catch {}
    }, 3000)
  }

  return () => {
    watcher?.close()
    if (pollTimer) clearInterval(pollTimer)
  }
}
