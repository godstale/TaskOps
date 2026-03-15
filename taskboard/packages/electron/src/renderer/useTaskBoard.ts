import { useState, useEffect, useCallback } from 'react'
import type { EpicWithTasks, Operation, Resource, Setting, ProjectInfo, Task } from '@taskboard/core'

declare global {
  interface Window {
    taskboard: {
      selectFolder: () => Promise<string | null>
      getProjectList: (root: string) => Promise<Array<{ name: string; dbPath: string }>>
      getAllData: (dbPath: string) => Promise<AllData>
      onDbChanged: (cb: (dbPath: string) => void) => void
      offDbChanged: () => void
    }
  }
}

interface AllData {
  project: ProjectInfo | undefined
  epics: EpicWithTasks[]
  workflowOrder: Task[]
  operations: Operation[]
  resources: Resource[]
  settings: Setting[]
}

export type Screen = 'dashboard' | 'taskops' | 'resources' | 'settings'

export function useTaskBoard(dbPath: string | null) {
  const [data, setData] = useState<AllData | null>(null)
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null)
  const [screen, setScreen] = useState<Screen>('dashboard')

  const reload = useCallback(async (path: string) => {
    const result = await window.taskboard.getAllData(path)
    setData(result)
  }, [])

  useEffect(() => {
    if (!dbPath) return
    reload(dbPath)
    window.taskboard.onDbChanged((changedPath) => {
      if (changedPath === dbPath) reload(dbPath)
    })
    return () => window.taskboard.offDbChanged()
  }, [dbPath, reload])

  return {
    data,
    selectedTaskId,
    setSelectedTaskId,
    screen,
    setScreen,
    reload: () => dbPath && reload(dbPath),
  }
}
