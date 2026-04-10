import { spawn } from 'node:child_process'
import path from 'node:path'
import { projectRoot, resolvePythonExe } from './common.mjs'

const taskArgs = process.argv.slice(2)

if (taskArgs.length === 0) {
  console.error('Usage: npm run bu:task -- "your browser task here"')
  process.exit(1)
}

const env = {
  ...process.env,
  PYTHONUTF8: '1',
  PYTHONIOENCODING: 'utf-8',
}

const child = spawn(
  resolvePythonExe(),
  [path.resolve(projectRoot, 'scripts', 'browser_use_task.py'), ...taskArgs],
  {
    env,
    stdio: 'inherit',
  },
)

child.on('exit', (code) => {
  process.exit(code ?? 0)
})

