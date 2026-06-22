@echo off
cd /d "%~dp0.."
docker cp jm-napcat:/app/napcat/cache/qrcode.png "%~dp0..\tools\napcat-docker\qrcode.png"
start "" "%~dp0..\tools\napcat-docker\qrcode.png"
pause
