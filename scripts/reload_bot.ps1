$ErrorActionPreference = "Stop"

# Soft reload: restart ONLY the Python bot process, leave the NapCat container alone.
# Use this to apply qqbot_jm.py code changes without affecting the QQ login
# (no QR popup, no extra logins -- frequent logins risk QQ风控). NapCat will
# auto-reconnect its reverse WebSocket to the new Python process within ~30s.

$root = Split-Path $PSScriptRoot -Parent
Set-Location $root

$logDir = Join-Path $root "logs"
$pidFile = Join-Path $logDir "jmcomic-bot.pid"
$logFile = Join-Path $logDir "jmcomic-bot.log"
$errFile = Join-Path $logDir "jmcomic-bot.err.log"

New-Item -ItemType Directory -Force $logDir | Out-Null

# Kill ALL qqbot Python processes by command line (catches stale/duplicate
# interpreters not on 8080 or in the pid file -- a zombie like that caused 403s).
Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Where-Object { $_.CommandLine -like '*qqbot_jm*' } |
  ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }

# Backup: anything still on 8080, plus the pid file
$ids = Get-NetTCPConnection -LocalPort 8080 -State Listen -ErrorAction SilentlyContinue |
  Select-Object -ExpandProperty OwningProcess -Unique
foreach ($id in $ids) { Stop-Process -Id $id -Force -ErrorAction SilentlyContinue }
if (Test-Path $pidFile) {
  $oldPid = Get-Content $pidFile | Select-Object -First 1
  if ($oldPid) { Stop-Process -Id ([int]$oldPid) -Force -ErrorAction SilentlyContinue }
}

Start-Sleep -Seconds 1

$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"

$process = Start-Process `
  -FilePath ".\.venv\Scripts\python.exe" `
  -ArgumentList ".\qqbot_jm.py" `
  -WorkingDirectory $root `
  -RedirectStandardOutput $logFile `
  -RedirectStandardError $errFile `
  -WindowStyle Hidden `
  -PassThru

Set-Content -Path $pidFile -Value $process.Id -Encoding ASCII
Write-Host "Soft-reloaded Python bot (NapCat container untouched, QQ stays logged in). PID=$($process.Id)"
Write-Host "NapCat reconnects within ~30s; run tail_bot_log.bat and watch for 'Bot ... connected'."
