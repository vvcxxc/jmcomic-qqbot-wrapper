$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot

$pidFile = Join-Path $PSScriptRoot "jmcomic-bot.pid"

if (Test-Path $pidFile) {
  $botPid = Get-Content $pidFile | Select-Object -First 1
  if ($botPid) {
    Stop-Process -Id ([int]$botPid) -Force -ErrorAction SilentlyContinue
  }
  Remove-Item -LiteralPath $pidFile -Force -ErrorAction SilentlyContinue
}

$listeners = Get-NetTCPConnection -LocalPort 8080 -State Listen -ErrorAction SilentlyContinue |
  Select-Object -ExpandProperty OwningProcess -Unique

foreach ($ownerId in $listeners) {
  Stop-Process -Id $ownerId -Force -ErrorAction SilentlyContinue
}

Write-Host "NoneBot stopped."

docker stop jm-napcat 2>$null | Out-Null
Write-Host "NapCat container stopped."
