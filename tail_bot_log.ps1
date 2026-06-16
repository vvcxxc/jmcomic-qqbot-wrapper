$ErrorActionPreference = "Stop"

$logFile = Join-Path $PSScriptRoot "logs\jmcomic-bot.log"

if (!(Test-Path $logFile)) {
  Write-Host "Log file does not exist yet: $logFile"
  exit 0
}

Get-Content -Path $logFile -Tail 120 -Wait
