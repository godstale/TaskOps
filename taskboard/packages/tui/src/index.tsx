#!/usr/bin/env node
import React from 'react'
import { render } from 'ink'
import { ProjectSelect } from './screens/ProjectSelect'
import path from 'path'

const args = process.argv.slice(2)
const pathIdx = args.indexOf('--path')
const taskopsRoot = pathIdx !== -1 ? path.resolve(args[pathIdx + 1]) : null

render(<ProjectSelect taskopsRoot={taskopsRoot} />)
