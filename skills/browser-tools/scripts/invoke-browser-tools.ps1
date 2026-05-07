param(
  [Parameter(Mandatory = $true, Position = 0)]
  [string]$Action,

  [Parameter(ValueFromRemainingArguments = $true)]
  [string[]]$Args
)

$ProjectRoot = '__BROWSER_TOOLS_REPO_ROOT__'
if ($ProjectRoot -like '__BROWSER_TOOLS_*') {
  throw 'This skill template must be installed via scripts/install-codex-skill.ps1 before use.'
}

$Launcher = Join-Path $ProjectRoot 'bt.ps1'
if (-not (Test-Path -LiteralPath $Launcher)) {
  throw "browser-tools launcher not found: $Launcher"
}

$PowerShell = (Get-Command powershell -ErrorAction SilentlyContinue).Source
if (-not $PowerShell) {
  throw 'powershell.exe not found.'
}

& $PowerShell -NoProfile -ExecutionPolicy Bypass -File $Launcher $Action @Args
exit $LASTEXITCODE
