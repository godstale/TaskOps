import React from 'react'
import { Box, Text } from 'ink'
import type { Setting } from '@taskboard/core'

interface Props {
  settings: Setting[]
}

export function Settings({ settings }: Props) {
  return (
    <Box flexDirection="column" padding={1}>
      <Text bold>Settings</Text>
      <Text dimColor>{'─'.repeat(50)}</Text>
      {settings.length === 0 && <Text dimColor>No settings found</Text>}
      {settings.map(s => (
        <Box key={s.key} marginBottom={0}>
          <Text color="cyan">{s.key.padEnd(24)}</Text>
          <Text color="yellow">{s.value.padEnd(16)}</Text>
          {s.description && <Text dimColor>{s.description}</Text>}
        </Box>
      ))}
    </Box>
  )
}
