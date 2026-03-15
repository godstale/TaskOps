import { describe, it, expect, afterEach } from 'vitest'
import { openDb, closeDb } from '../src/db'
import Database from 'better-sqlite3'
import fs from 'fs'
import os from 'os'
import path from 'path'

const tmpDb = () => path.join(os.tmpdir(), `test-${Date.now()}.db`)

describe('openDb', () => {
  const paths: string[] = []

  afterEach(() => {
    paths.forEach(p => { try { fs.unlinkSync(p) } catch {} })
    paths.length = 0
  })

  it('존재하는 DB 파일을 열 수 있다', () => {
    const p = tmpDb(); paths.push(p)
    const db = new Database(p)
    db.close()
    const conn = openDb(p)
    expect(conn).toBeDefined()
    closeDb(conn)
  })

  it('존재하지 않는 파일이면 에러를 던진다', () => {
    expect(() => openDb('/non/existent/path.db')).toThrow()
  })
})
