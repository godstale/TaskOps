import React from 'react'
import { Box, Text } from 'ink'
import type { EpicWithTasks, ProjectInfo, TaskStatus } from '@taskboard/core'

const STATUS_ICON: Record<TaskStatus, string> = {
  done: '✓',
  in_progress: '●',
  todo: '○',
  interrupted: '✕',
  cancelled: '—',
}

const STATUS_COLOR: Record<TaskStatus, string> = {
  done: 'green',
  in_progress: 'yellow',
  todo: 'white',
  interrupted: 'red',
  cancelled: 'gray',
}

function ProgressBar({ value, total, width = 20 }: { value: number; total: number; width?: number }) {
  const filled = total > 0 ? Math.round((value / total) * width) : 0
  const bar = '█'.repeat(filled) + '░'.repeat(width - filled)
  const pct = total > 0 ? Math.round((value / total) * 100) : 0
  return <Text>{bar} {pct}%</Text>
}

interface Props {
  project: ProjectInfo | undefined
  epics: EpicWithTasks[]
  [key: string]: any
}

export function Dashboard({ project, epics }: Props) {
  const allTasks = epics.flatMap(e => e.tasks.map(t => t.task))
  const doneTasks = allTasks.filter(t => t.status === 'done').length
  const inProgressTasks = allTasks.filter(t => t.status === 'in_progress').length

  return (
    <Box flexDirection="column" padding={1}>
      {/* Header */}
      <Box borderStyle="single" paddingX={1} marginBottom={1}>
        <Text bold>{project?.title ?? 'Project'}</Text>
        <Text> | </Text>
        <Text>Epics: {epics.length}  Tasks: {allTasks.length}  </Text>
        <Text color="green">Done: {doneTasks}/{allTasks.length}  </Text>
        <Text color="yellow">In Progress: {inProgressTasks}</Text>
      </Box>

      {/* Epic list */}
      {epics.map(({ epic, tasks }) => {
        const epicDone = tasks.filter(t => t.task.status === 'done').length
        return (
          <Box key={epic.id} flexDirection="column" marginBottom={1}>
            <Box>
              <Text bold color="cyan">[{epic.id}] {epic.title}  </Text>
              <ProgressBar value={epicDone} total={tasks.length} />
            </Box>
            {tasks.map(({ task, children }) => (
              <Box key={task.id} flexDirection="column">
                <Box marginLeft={2}>
                  <Text color={STATUS_COLOR[task.status]}>
                    {STATUS_ICON[task.status]} [{task.id}] {task.title}
                  </Text>
                  <Text dimColor>  {task.status}</Text>
                </Box>
                {children.map(child => (
                  <Box key={child.id} marginLeft={4}>
                    <Text color={STATUS_COLOR[child.status]} dimColor>
                      {STATUS_ICON[child.status]} [{child.id}] {child.title}
                    </Text>
                  </Box>
                ))}
              </Box>
            ))}
          </Box>
        )
      })}
    </Box>
  )
}
