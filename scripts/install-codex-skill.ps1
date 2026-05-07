param(
  [string]$CodexHome = $env:CODEX_HOME
)

$RepoRoot = Split-Path -Parent $PSScriptRoot
if (-not $CodexHome) {
  $CodexHome = Join-Path $HOME '.codex'
}

$SkillSource = Join-Path $RepoRoot 'skills\browser-tools'
$SkillsRoot = Join-Path $CodexHome 'skills'
$TargetRoot = Join-Path $SkillsRoot 'browser-tools'

if (-not (Test-Path -LiteralPath $SkillSource)) {
  throw "Skill source not found: $SkillSource"
}

$ResolvedCodexHome = [System.IO.Path]::GetFullPath($CodexHome)
$ResolvedSkillsRoot = [System.IO.Path]::GetFullPath($SkillsRoot)
$ResolvedTargetRoot = [System.IO.Path]::GetFullPath($TargetRoot)

if (-not $ResolvedTargetRoot.StartsWith($ResolvedSkillsRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
  throw "Refusing to install outside Codex skills directory: $ResolvedTargetRoot"
}

New-Item -ItemType Directory -Force -Path $SkillsRoot | Out-Null

if (Test-Path -LiteralPath $TargetRoot) {
  Remove-Item -LiteralPath $TargetRoot -Recurse -Force
}

Copy-Item -LiteralPath $SkillSource -Destination $TargetRoot -Recurse -Force

$InvokeScript = Join-Path $TargetRoot 'scripts\invoke-browser-tools.ps1'
$RepoRootEscaped = $RepoRoot.Replace("'", "''")
$InvokeContent = Get-Content -LiteralPath $InvokeScript -Raw -Encoding UTF8
$InvokeContent = $InvokeContent.Replace('__BROWSER_TOOLS_REPO_ROOT__', $RepoRootEscaped)
[System.IO.File]::WriteAllText($InvokeScript, $InvokeContent, [System.Text.UTF8Encoding]::new($false))

Write-Host "Installed skill to: $ResolvedTargetRoot"
Write-Host "Codex home: $ResolvedCodexHome"
Write-Host "Repo root: $RepoRoot"
Write-Host "Invoke with:"
Write-Host "powershell -NoProfile -ExecutionPolicy Bypass -File ~\.codex\skills\browser-tools\scripts\invoke-browser-tools.ps1 pw:smoke"
