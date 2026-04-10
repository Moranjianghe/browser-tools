import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import dotenv from 'dotenv'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

export const projectRoot = path.resolve(__dirname, '..')

dotenv.config({ path: path.resolve(projectRoot, '.env') })

const defaultChromePaths = [
  process.env.CHROME_PATH,
  'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
  'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
  'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
  'C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe',
].filter(Boolean)

export function ensureDir(targetPath) {
  fs.mkdirSync(targetPath, { recursive: true })
  return targetPath
}

export function resolveBrowserBinary() {
  const browserPath = defaultChromePaths.find((candidate) => candidate && fs.existsSync(candidate))
  if (!browserPath) {
    throw new Error('No Chrome or Edge executable was found. Set CHROME_PATH in .env.')
  }
  return browserPath
}

export function resolveProfileDir() {
  return ensureDir(process.env.BROWSER_PROFILE_DIR || path.resolve(projectRoot, 'profiles', 'shared'))
}

export function resolveDownloadsDir() {
  return ensureDir(path.resolve(projectRoot, 'downloads'))
}

export function resolveDebuggingPort() {
  return Number(process.env.REMOTE_DEBUGGING_PORT || 9222)
}

export function resolveCdpUrl() {
  return process.env.BROWSER_CDP_URL || `http://127.0.0.1:${resolveDebuggingPort()}`
}

export function resolvePythonExe() {
  const pythonExe = path.resolve(projectRoot, '.venv', 'Scripts', 'python.exe')
  if (!fs.existsSync(pythonExe)) {
    throw new Error('Python virtual environment not found. Expected .venv\\Scripts\\python.exe.')
  }
  return pythonExe
}

export function resolveBrowserUseExe() {
  const browserUseExe = path.resolve(projectRoot, '.venv', 'Scripts', 'browser-use.exe')
  if (!fs.existsSync(browserUseExe)) {
    throw new Error('browser-use executable not found in .venv\\Scripts\\browser-use.exe.')
  }
  return browserUseExe
}

