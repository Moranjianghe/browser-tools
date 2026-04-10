param(
  [Parameter(Mandatory = $true, Position = 0)]
  [string]$Action,

  [Parameter(ValueFromRemainingArguments = $true)]
  [string[]]$Args
)

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

Push-Location $projectRoot
try {
  $npmArgs = @('run', $Action)
  if ($Args.Count -gt 0) {
    $npmArgs += '--'
    $npmArgs += $Args
  }

  & npm @npmArgs
  exit $LASTEXITCODE
}
finally {
  Pop-Location
}
