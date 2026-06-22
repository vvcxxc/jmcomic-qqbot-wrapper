$ErrorActionPreference = "Stop"

# Native mode (NapCatQQ-Desktop): this only stops the Python bot.
# NapCat itself is managed by the Desktop app (stop it there if needed).

$root = Split-Path $PSScriptRoot -Parent
Set-Location $root

$pidFile = Join-Path $root "logs\jmcomic-bot.pid"

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

Write-Host "Python bot stopped. (NapCat is managed by NapCatQQ-Desktop.)"
