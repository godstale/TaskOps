import React from 'react'
import { Box, Text } from 'ink'
import type { Key } from 'ink'
import { useTaskBoard, Screen } from './useTaskBoard.js'
import { useSafeInput } from './useSafeInput.js'
import { Dashboard } from './screens/Dashboard.js'
import { TaskOperations } from './screens/TaskOperations.js'
import { Resources } from './screens/Resources.js'
import { Settings } from './screens/Settings.js'

const SCREENS: Screen[] = ['dashboard', 'taskops', 'resources', 'settings']
const SCREEN_LABELS: Record<Screen, string> = {
  dashboard: 'Dashboard',
  taskops: 'Task Ops',
  resources: 'Resources',
  settings: 'Settings',
}

interface Props {
  dbPath: string
}

export function App({ dbPath }: Props) {
  const board = useTaskBoard(dbPath)

  useSafeInput((input: string, key: Key) => {
    if (input === 'q' || input === 'Q') process.exit(0)
    if (input === 'r' || input === 'R') board.reload()
    if (key.tab) {
      const idx = SCREENS.indexOf(board.screen)
      board.setScreen(SCREENS[(idx + 1) % SCREENS.length])
    }
  })

  if (board.error) {
    return <Text color="red">Error: {board.error}</Text>
  }

  return (
    <Box flexDirection="column" height="100%">
      {/* Tab navigation */}
      <Box borderStyle="single" paddingX={1}>
        {SCREENS.map((s) => (
          <Box key={s} marginRight={2}>
            <Text
              color={board.screen === s ? 'cyan' : 'white'}
              bold={board.screen === s}
            >
              {board.screen === s ? `[${SCREEN_LABELS[s]}]` : SCREEN_LABELS[s]}
            </Text>
          </Box>
        ))}
        <Box marginLeft={2}>
          <Text dimColor>[Tab]전환 [R]새로고침 [Q]종료</Text>
        </Box>
      </Box>

      {/* Screen content */}
      <Box flexGrow={1}>
        {board.screen === 'dashboard' && <Dashboard {...board} />}
        {board.screen === 'taskops' && <TaskOperations {...board} />}
        {board.screen === 'resources' && <Resources resources={board.resources} />}
        {board.screen === 'settings' && <Settings settings={board.settings} />}
      </Box>
    </Box>
  )
}
