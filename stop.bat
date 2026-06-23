@echo off
echo Stopping Meeting Room Service...
taskkill /F /IM python.exe /T
echo Service stopped.
pause