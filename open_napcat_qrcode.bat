@echo off
cd /d "%~dp0"
docker cp jm-napcat:/app/napcat/cache/qrcode.png "%~dp0tools\napcat-docker\qrcode.png"
start "" "%~dp0tools\napcat-docker\qrcode.png"
pause
