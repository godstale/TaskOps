import { describe, it, expect, vi } from 'vitest'
import { render } from 'ink-testing-library'
import React from 'react'

vi.mock('@taskboard/core', () => ({
  getProjectList: () => [
    { name: 'my-project', dbPath: '/tmp/my-project/taskops.db' }
  ],
  openDb: vi.fn(),
  closeDb: vi.fn(),
  getProject: vi.fn(() => undefined),
  getEpicsWithTasks: vi.fn(() => []),
  getWorkflowOrder: vi.fn(() => []),
  getOperations: vi.fn(() => []),
  getResources: vi.fn(() => []),
  getSettings: vi.fn(() => []),
  watch: vi.fn(() => () => {}),
}))

import { ProjectSelect } from '../src/screens/ProjectSelect'

describe('ProjectSelect', () => {
  it('프로젝트 목록을 표시한다', () => {
    const { lastFrame } = render(
      <ProjectSelect taskopsRoot="/tmp/taskops" />
    )
    expect(lastFrame()).toContain('my-project')
  })

  it('taskopsRoot가 없으면 경로 입력 UI를 표시한다', () => {
    const { lastFrame } = render(
      <ProjectSelect taskopsRoot={null} />
    )
    expect(lastFrame()).toContain('path')
  })
})
