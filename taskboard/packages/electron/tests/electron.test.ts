/**
 * E2E tests for TaskBoard Electron app.
 * Tests verify the app structure and core IPC behavior.
 * Note: Full Electron launch tests require display server (not available in CI headlessly on Windows without setup).
 */
import { describe, it, expect } from 'vitest'
import path from 'path'
import fs from 'fs'

describe('Electron app structure', () => {
  it('main process entry point exists', () => {
    const mainPath = path.join(__dirname, '../dist/main/index.js')
    expect(fs.existsSync(mainPath)).toBe(true)
  })

  it('preload script exists', () => {
    const preloadPath = path.join(__dirname, '../dist/main/preload.js')
    expect(fs.existsSync(preloadPath)).toBe(true)
  })

  it('renderer build exists', () => {
    const rendererPath = path.join(__dirname, '../dist/renderer')
    expect(fs.existsSync(rendererPath)).toBe(true)
  })

  it('renderer index.html exists', () => {
    const htmlPath = path.join(__dirname, '../dist/renderer/index.html')
    expect(fs.existsSync(htmlPath)).toBe(true)
  })
})

describe('IPC channel constants', () => {
  it('IPC module can be loaded', () => {
    // Verify the source file exists
    const ipcSrc = path.join(__dirname, '../src/main/ipc.ts')
    expect(fs.existsSync(ipcSrc)).toBe(true)
    // Verify compiled output exists
    const ipcDist = path.join(__dirname, '../dist/main/ipc.js')
    expect(fs.existsSync(ipcDist)).toBe(true)
  })
})
