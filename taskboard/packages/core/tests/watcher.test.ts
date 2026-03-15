import { describe, it, expect, vi } from 'vitest'
import { watch } from '../src/watcher'
import fs from 'fs'
import os from 'os'
import path from 'path'

describe('watch', () => {
  it('unwatch 함수를 반환한다', () => {
    const tmpPath = path.join(os.tmpdir(), `watch-test-${Date.now()}.db`)
    fs.writeFileSync(tmpPath, '')
    const unwatch = watch(tmpPath, vi.fn())
    expect(typeof unwatch).toBe('function')
    unwatch()
    fs.unlinkSync(tmpPath)
  })

  it('파일 변경 시 콜백이 호출된다', async () => {
    const tmpPath = path.join(os.tmpdir(), `watch-test-${Date.now()}.db`)
    fs.writeFileSync(tmpPath, 'initial')

    const callback = vi.fn()
    const unwatch = watch(tmpPath, callback)

    await new Promise(r => setTimeout(r, 200))
    fs.writeFileSync(tmpPath, 'changed')
    await new Promise(r => setTimeout(r, 500))

    expect(callback).toHaveBeenCalled()
    unwatch()
    fs.unlinkSync(tmpPath)
  })
})
