import { describe, it, expect } from 'vitest'
import { render } from 'ink-testing-library'
import React from 'react'
import { Dashboard } from '../src/screens/Dashboard'

const mockEpics = [{
  epic: { id: 'FIX-E001', title: '인증 시스템', status: 'in_progress' as const, type: 'epic' as const, project_id: 'FIX', created_at: '', updated_at: '' },
  tasks: [
    { task: { id: 'FIX-T001', title: '로그인 API', status: 'done' as const, type: 'task' as const, project_id: 'FIX', parent_id: 'FIX-E001', created_at: '', updated_at: '' }, children: [] },
    { task: { id: 'FIX-T002', title: '회원가입 API', status: 'in_progress' as const, type: 'task' as const, project_id: 'FIX', parent_id: 'FIX-E001', created_at: '', updated_at: '' }, children: [] },
  ]
}]

const baseProps = {
  project: undefined,
  epics: mockEpics,
  operations: [],
  resources: [],
  settings: [],
  selectedTaskId: null,
  screen: 'dashboard' as const,
  error: null,
  reload: () => {},
  setScreen: () => {},
  setSelectedTask: () => {},
}

describe('Dashboard', () => {
  it('Epic 제목을 표시한다', () => {
    const { lastFrame } = render(<Dashboard {...baseProps} />)
    expect(lastFrame()).toContain('인증 시스템')
  })

  it('Task 제목을 표시한다', () => {
    const { lastFrame } = render(<Dashboard {...baseProps} />)
    expect(lastFrame()).toContain('로그인 API')
    expect(lastFrame()).toContain('회원가입 API')
  })
})
