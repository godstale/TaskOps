import React from 'react'
import type { EpicWithTasks, Task, TaskStatus } from '@taskboard/core'

interface AllData {
  project: { title?: string } | undefined
  epics: EpicWithTasks[]
  workflowOrder: Task[]
  operations: any[]
  resources: any[]
  settings: any[]
}

interface Props {
  data: AllData
}

const STATUS_COLOR: Record<TaskStatus, string> = {
  done: 'bg-green-500',
  in_progress: 'bg-yellow-500',
  todo: 'bg-gray-500',
  interrupted: 'bg-red-500',
  cancelled: 'bg-gray-700',
}

const STATUS_TEXT: Record<TaskStatus, string> = {
  done: 'Done',
  in_progress: 'In Progress',
  todo: 'Todo',
  interrupted: 'Interrupted',
  cancelled: 'Cancelled',
}

function ProgressBar({ done, total }: { done: number; total: number }) {
  const pct = total > 0 ? Math.round((done / total) * 100) : 0
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 bg-gray-700 rounded-full h-2">
        <div
          className="bg-blue-500 h-2 rounded-full transition-all"
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs text-gray-400 w-10 text-right">{pct}%</span>
    </div>
  )
}

export function Dashboard({ data }: Props) {
  const { project, epics } = data
  const allTasks = epics.flatMap(e => e.tasks.map(t => t.task))
  const doneTasks = allTasks.filter(t => t.status === 'done').length
  const inProgressTasks = allTasks.filter(t => t.status === 'in_progress').length

  return (
    <div className="p-6">
      {/* Header Stats */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white mb-1">{project?.title ?? 'Project'}</h1>
        <div className="flex gap-6 text-sm text-gray-400">
          <span><span className="text-white font-medium">{epics.length}</span> Epics</span>
          <span><span className="text-white font-medium">{allTasks.length}</span> Tasks</span>
          <span><span className="text-green-400 font-medium">{doneTasks}</span> Done</span>
          <span><span className="text-yellow-400 font-medium">{inProgressTasks}</span> In Progress</span>
        </div>
      </div>

      {/* Epic Cards */}
      <div className="space-y-4">
        {epics.map(({ epic, tasks }) => {
          const epicDone = tasks.filter(t => t.task.status === 'done').length
          return (
            <div key={epic.id} className="bg-gray-900 border border-gray-800 rounded-xl p-4">
              <div className="flex items-start justify-between mb-3">
                <div>
                  <span className="text-xs text-gray-500 font-mono">{epic.id}</span>
                  <h3 className="text-white font-semibold">{epic.title}</h3>
                </div>
                <span className={`text-xs px-2 py-1 rounded-full ${STATUS_COLOR[epic.status]} text-white`}>
                  {STATUS_TEXT[epic.status]}
                </span>
              </div>
              <ProgressBar done={epicDone} total={tasks.length} />

              {/* Task list */}
              <div className="mt-3 space-y-1">
                {tasks.map(({ task, children }) => (
                  <div key={task.id}>
                    <div className="flex items-center gap-2 py-1">
                      <span className={`w-2 h-2 rounded-full flex-shrink-0 ${STATUS_COLOR[task.status]}`} />
                      <span className="text-xs text-gray-500 font-mono w-20 flex-shrink-0">{task.id}</span>
                      <span className="text-sm text-gray-200 flex-1">{task.title}</span>
                      <span className="text-xs text-gray-500">{STATUS_TEXT[task.status]}</span>
                    </div>
                    {children.map(child => (
                      <div key={child.id} className="flex items-center gap-2 py-1 pl-6">
                        <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${STATUS_COLOR[child.status]}`} />
                        <span className="text-xs text-gray-500 font-mono w-20 flex-shrink-0">{child.id}</span>
                        <span className="text-sm text-gray-400 flex-1">{child.title}</span>
                        <span className="text-xs text-gray-500">{STATUS_TEXT[child.status]}</span>
                      </div>
                    ))}
                  </div>
                ))}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
