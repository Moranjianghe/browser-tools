import { spawn } from 'node:child_process'
import { resolveBrowserUseExe } from './common.mjs'

const env = {
  ...process.env,
  PYTHONUTF8: '1',
  PYTHONIOENCODING: 'utf-8',
}

const child = spawn(resolveBrowserUseExe(), ['doctor'], {
  env,
  stdio: 'inherit',
})

child.on('exit', (code) => {
  process.exit(code ?? 0)
})

