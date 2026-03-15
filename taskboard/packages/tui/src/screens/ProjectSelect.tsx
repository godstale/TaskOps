import React, { useState } from 'react'
import { Box, Text, render } from 'ink'
import { getProjectList } from '@taskboard/core'
import { useSafeInput } from '../useSafeInput'
import { App } from '../App'
import path from 'path'

interface Props {
  taskopsRoot: string | null
}

export function ProjectSelect({ taskopsRoot }: Props) {
  const [rootPath, setRootPath] = useState(taskopsRoot ?? '')
  const [submitted, setSubmitted] = useState(!!taskopsRoot)

  if (!submitted) {
    return (
      <PathInput
        value={rootPath}
        onChange={setRootPath}
        onSubmit={() => setSubmitted(true)}
      />
    )
  }

  const projects = getProjectList(path.resolve(rootPath))

  if (projects.length === 0) {
    return (
      <Box flexDirection="column" padding={1}>
        <Text color="yellow">No projects found in: {rootPath}</Text>
        <Text dimColor>Make sure the folder contains TaskOps projects (with taskops.db)</Text>
      </Box>
    )
  }

  return (
    <ProjectList projects={projects} />
  )
}

function PathInput({
  value,
  onChange,
  onSubmit,
}: {
  value: string
  onChange: (v: string) => void
  onSubmit: () => void
}) {
  useSafeInput((input, key) => {
    if (key.return) {
      onSubmit()
    } else if (key.backspace || key.delete) {
      onChange(value.slice(0, -1))
    } else if (input && !key.ctrl && !key.meta) {
      onChange(value + input)
    }
  })

  return (
    <Box flexDirection="column" padding={1}>
      <Text bold>TaskBoard</Text>
      <Text dimColor>Enter TaskOps root path:</Text>
      <Box>
        <Text>{'> '}</Text>
        <Text>{value}</Text>
        <Text inverse> </Text>
      </Box>
    </Box>
  )
}

function ProjectList({ projects }: { projects: Array<{ name: string; dbPath: string }> }) {
  const [selectedIdx, setSelectedIdx] = useState(0)
  const [launched, setLaunched] = useState(false)

  useSafeInput((_, key) => {
    if (key.upArrow) setSelectedIdx(i => Math.max(0, i - 1))
    if (key.downArrow) setSelectedIdx(i => Math.min(projects.length - 1, i + 1))
    if (key.return) {
      render(<App dbPath={projects[selectedIdx].dbPath} />)
      setLaunched(true)
    }
  })

  if (launched) return null

  return (
    <Box flexDirection="column" padding={1}>
      <Text bold>Select Project:</Text>
      <Text dimColor>[↑↓] navigate, [Enter] select</Text>
      {projects.map((p, i) => (
        <Box key={p.name}>
          <Text color={i === selectedIdx ? 'cyan' : 'white'}>
            {i === selectedIdx ? '▶ ' : '  '}{p.name}
          </Text>
        </Box>
      ))}
    </Box>
  )
}
