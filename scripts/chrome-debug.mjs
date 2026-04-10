import { spawn } from 'node:child_process'
import { resolveBrowserBinary, resolveDebuggingPort, resolveProfileDir } from './common.mjs'

const browserBinary = resolveBrowserBinary()
const debuggingPort = resolveDebuggingPort()
const profileDir = resolveProfileDir()
const startUrl = process.argv[2] || 'about:blank'

const args = [
  `--remote-debugging-port=${debuggingPort}`,
  `--user-data-dir=${profileDir}`,
  '--no-first-run',
  '--no-default-browser-check',
  startUrl,
]

console.log(`Launching browser: ${browserBinary}`)
console.log(`Remote debugging URL: http://127.0.0.1:${debuggingPort}`)
console.log(`Shared profile directory: ${profileDir}`)

const child = spawn(browserBinary, args, {
  stdio: 'inherit',
})

child.on('exit', (code) => {
  process.exit(code ?? 0)
})

