import React, { useState } from 'react'
import { Box, Text } from 'ink'
import type { Key } from 'ink'
import { useSafeInput } from '../useSafeInput.js'
import type { EpicWithTasks, Operation } from '@taskboard/core'

const OP_ICON: Record<string, string> = {
  start: '▶',
  progress: '│',
  complete: '✓',
  error: '✕',
  interrupt: '⚠',
}

const OP_COLOR: Record<string, string> = {
  start: 'cyan',
  progress: 'white',
  complete: 'green',
  error: 'red',
  interrupt: 'yellow',
}

interface Props {
  epics: EpicWithTasks[]
  operations: Operation[]
  selectedTaskId: string | null
  setSelectedTask: (id: string | null) => void
  [key: string]: any
}

export function TaskOperations({ epics, operations, selectedTaskId, setSelectedTask }: Props) {
  const allTasks = epics.flatMap(e => e.tasks.map(t => t.task))
  const [taskIdx, setTaskIdx] = useState(0)

  const selectedTask = selectedTaskId
    ? allTasks.find(t => t.id === selectedTaskId)
    : allTasks[taskIdx]

  useSafeInput((_: string, key: Key) => {
    if (key.leftArrow) setTaskIdx(i => Math.max(0, i - 1))
    if (key.rightArrow) setTaskIdx(i => Math.min(allTasks.length - 1, i + 1))
  })

  const taskOps = selectedTask
    ? operations.filter(o => o.task_id === selectedTask.id)
    : []

  return (
    <Box flexDirection="column" padding={1}>
      {/* Task selection bar */}
      <Box marginBottom={1} flexWrap="wrap">
        {allTasks.map((t, i) => (
          <Box key={t.id} marginRight={2}>
            <Text
              color={t === selectedTask ? 'cyan' : 'white'}
              bold={t === selectedTask}
            >
              {t === selectedTask ? `▶${t.id}◀` : t.id}
            </Text>
          </Box>
        ))}
      </Box>
      <Text dimColor>[←→] Task 선택</Text>

      {/* Operation Flow */}
      <Box borderStyle="single" flexDirection="column" paddingX={2} marginTop={1}>
        {selectedTask ? (
          <>
            <Text bold>{selectedTask.id}: {selectedTask.title}</Text>
            <Text dimColor>{'─'.repeat(40)}</Text>
            {taskOps.length === 0 && <Text dimColor>No operations recorded</Text>}
            {taskOps.map(op => (
              <Box key={op.id}>
                <Text color={OP_COLOR[op.operation_type]}>
                  {OP_ICON[op.operation_type]} {op.operation_type.padEnd(10)}
                </Text>
                <Text dimColor>{op.created_at.slice(11, 16)}  </Text>
                <Text color={op.agent_platform ? 'blue' : 'white'}>
                  {op.agent_platform ?? ''}{'  '}
                </Text>
                <Text>{op.summary ?? ''}</Text>
              </Box>
            ))}
          </>
        ) : (
          <Text dimColor>No task selected</Text>
        )}
      </Box>
    </Box>
  )
}
