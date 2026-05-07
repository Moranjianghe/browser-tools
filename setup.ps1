param(
  [switch]$CopyEnv
)

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

function Get-PythonCommand {
  if (Get-Command python -ErrorAction SilentlyContinue) {
    return @('python')
  }

  if (Get-Command py -ErrorAction SilentlyContinue) {
    return @('py', '-3')
  }

  throw 'Python was not found. Install Python 3 first, then rerun setup.ps1.'
}

Push-Location $projectRoot
try {
  # Force array semantics so single-item return values don't degrade to a string.
  $pythonCommand = @(Get-PythonCommand)
  $pythonExe = $pythonCommand[0]
  $pythonArgs = @($pythonCommand | Select-Object -Skip 1)

  if (-not (Test-Path '.venv')) {
    & $pythonExe @pythonArgs -m venv .venv
    if ($LASTEXITCODE -ne 0) {
      throw 'Failed to create Python virtual environment.'
    }
  }

  & .\.venv\Scripts\python.exe -m pip install --upgrade pip
  if ($LASTEXITCODE -ne 0) {
    throw 'Failed to upgrade pip in .venv.'
  }

  & .\.venv\Scripts\pip.exe install -r requirements.txt
  if ($LASTEXITCODE -ne 0) {
    throw 'Failed to install Python dependencies from requirements.txt.'
  }

  & npm install
  if ($LASTEXITCODE -ne 0) {
    throw 'Failed to install Node dependencies with npm install.'
  }

  if ($CopyEnv -and -not (Test-Path '.env')) {
    Copy-Item .env.example .env
  }

  Write-Host 'Setup complete.'
  Write-Host 'Next steps:'
  Write-Host '1. Fill in .env with your API key if needed.'
  Write-Host '2. Run npm run pw:smoke'
  Write-Host '3. Run npm run bu:doctor'
}
finally {
  Pop-Location
}
