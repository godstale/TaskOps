import React from 'react'
import { Box, Text } from 'ink'
import type { Resource } from '@taskboard/core'

const TYPE_COLOR: Record<string, string> = {
  input: 'blue',
  output: 'green',
  reference: 'white',
  intermediate: 'yellow',
}

interface Props {
  resources: Resource[]
}

export function Resources({ resources }: Props) {
  return (
    <Box flexDirection="column" padding={1}>
      <Text bold>Resources ({resources.length})</Text>
      <Text dimColor>{'─'.repeat(60)}</Text>
      {resources.length === 0 && <Text dimColor>No resources recorded</Text>}
      {resources.map(r => (
        <Box key={r.id} marginBottom={0}>
          <Text color={TYPE_COLOR[r.res_type]}>{r.res_type.padEnd(14)}</Text>
          <Text dimColor>{r.task_id.padEnd(12)}</Text>
          <Text>{r.file_path}</Text>
          {r.description && <Text dimColor>  {r.description}</Text>}
        </Box>
      ))}
    </Box>
  )
}
