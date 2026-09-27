@echo off
rem Double-click to build Castle Doom and Doomstadt. Extra options can be passed,
rem e.g.  Build-Latveria.bat -DelayMs 150     (slower, gentler on the server)
rem       Build-Latveria.bat -DryRun          (only write the resolved command list)
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Build-Latveria.ps1" %*
pause
