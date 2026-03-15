import { describe, it, expect, beforeEach } from 'vitest'
import { createTestDb } from './helpers'
import {
  getProject, getEpicsWithTasks, getWorkflowOrder,
  getOperations, getResources, getSettings
} from '../src/queries'
import type { Db } from '../src/db'

let db: Db

beforeEach(() => { db = createTestDb() as unknown as Db })

describe('getProject', () => {
  it('프로젝트 기본 정보를 반환한다', () => {
    const p = getProject(db)
    expect(p?.id).toBe('TST')
    expect(p?.title).toBe('Test Project')
  })
})

describe('getEpicsWithTasks', () => {
  it('Epic과 하위 Task를 계층으로 반환한다', () => {
    const epics = getEpicsWithTasks(db)
    expect(epics).toHaveLength(1)
    expect(epics[0].epic.id).toBe('TST-E001')
    expect(epics[0].tasks).toHaveLength(3)
  })
})

describe('getWorkflowOrder', () => {
  it('seq_order 순으로 정렬된 Task를 반환한다', () => {
    const tasks = getWorkflowOrder(db)
    expect(tasks[0].id).toBe('TST-T001')
    expect(tasks[1].id).toBe('TST-T002')
    expect(tasks[2].id).toBe('TST-T003')
  })
})

describe('getOperations', () => {
  it('전체 operations를 반환한다', () => {
    const ops = getOperations(db)
    expect(ops).toHaveLength(2)
  })

  it('특정 task의 operations만 반환한다', () => {
    const ops = getOperations(db, 'TST-T001')
    expect(ops).toHaveLength(2)
    expect(ops.every(o => o.task_id === 'TST-T001')).toBe(true)
  })
})

describe('getResources', () => {
  it('전체 resources를 반환한다', () => {
    const res = getResources(db)
    expect(res).toHaveLength(1)
  })
})

describe('getSettings', () => {
  it('설정 목록을 반환한다', () => {
    const settings = getSettings(db)
    expect(settings.length).toBeGreaterThan(0)
    expect(settings[0].key).toBe('autonomy_level')
  })
})
