import React, { useState } from 'react'
import { Sidebar } from './components/Sidebar'
import { useTaskBoard } from './useTaskBoard'
import { ProjectSelect } from './screens/ProjectSelect'
import { Dashboard } from './screens/Dashboard'
import { TaskOperations } from './screens/TaskOperations'
import { Resources } from './screens/Resources'
import { Settings } from './screens/Settings'

export function App() {
  const [dbPath, setDbPath] = useState<string | null>(null)
  const { data, selectedTaskId, setSelectedTaskId, screen, setScreen } = useTaskBoard(dbPath)

  if (!dbPath || !data) {
    return (
      <div className="h-screen bg-gray-950 flex items-center justify-center">
        <ProjectSelect onSelect={setDbPath} />
      </div>
    )
  }

  return (
    <div className="h-screen flex bg-gray-950 text-gray-100">
      <Sidebar
        current={screen}
        onSelect={setScreen}
        projectName={data.project?.title}
      />
      <main className="flex-1 overflow-auto">
        {screen === 'dashboard' && <Dashboard data={data} />}
        {screen === 'taskops' && (
          <TaskOperations
            data={data}
            selectedTaskId={selectedTaskId}
            onSelectTask={setSelectedTaskId}
          />
        )}
        {screen === 'resources' && <Resources resources={data.resources} />}
        {screen === 'settings' && <Settings settings={data.settings} />}
      </main>
    </div>
  )
}
