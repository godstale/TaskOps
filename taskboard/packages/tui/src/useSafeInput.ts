import { useInput, useStdin } from 'ink'
import type { Key } from 'ink'

type InputHandler = (input: string, key: Key) => void

/**
 * Wrapper around useInput that guards against environments (e.g. ink-testing-library)
 * where stdin.ref is not available, preventing crashes in tests.
 */
export function useSafeInput(handler: InputHandler) {
  const { stdin } = useStdin()
  // Only activate if stdin has the ref() method needed by Ink's raw mode
  const hasRef = typeof (stdin as any)?.ref === 'function'
  useInput(handler, { isActive: hasRef })
}
