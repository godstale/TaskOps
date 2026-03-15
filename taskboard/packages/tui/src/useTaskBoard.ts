import { useState, useEffect, useCallback } from 'react'
import { openDb, closeDb, getProject, getEpicsWithTasks,
         getWorkflowOrder, getOperations, getResources,
         getSettings, watch } from '@taskboard/core'
import type { EpicWithTasks, Operation, Resource, Setting, ProjectInfo } from '@taskboard/core'

export type Db = ReturnType<typeof openDb>

export type Screen = 'dashboard' | 'taskops' | 'resources' | 'settings'

interface TaskBoardState {
  project: ProjectInfo | undefined
  epics: EpicWithTasks[]
  operations: Operation[]
  resources: Resource[]
  settings: Setting[]
  selectedTaskId: string | null
  screen: Screen
  error: string | null
}

export function useTaskBoard(dbPath: string) {
  const [state, setState] = useState<TaskBoardState>({
    project: undefined, epics: [], operations: [], resources: [],
    settings: [], selectedTaskId: null, screen: 'dashboard', error: null,
  })

  const reload = useCallback(() => {
    let db: ReturnType<typeof openDb> | null = null
    try {
      db = openDb(dbPath)
      setState(prev => ({
        ...prev,
        project: getProject(db!),
        epics: getEpicsWithTasks(db!),
        operations: getOperations(db!),
        resources: getResources(db!),
        settings: getSettings(db!),
        error: null,
      }))
    } catch (e) {
      setState(prev => ({ ...prev, error: String(e) }))
    } finally {
      if (db) closeDb(db)
    }
  }, [dbPath])

  useEffect(() => {
    reload()
    const unwatch = watch(dbPath, reload)
    return () => unwatch()
  }, [dbPath, reload])

  const setScreen = (screen: Screen) => setState(prev => ({ ...prev, screen }))
  const setSelectedTask = (id: string | null) => setState(prev => ({ ...prev, selectedTaskId: id }))

  return { ...state, reload, setScreen, setSelectedTask }
}
