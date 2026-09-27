@echo off
rem Latveria Lighting Overhaul - run AFTER the main build and the expansion.
rem Uses the centre of the first build (799 70 -10090); you are asked to confirm it.
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Build-Latveria.ps1" -CommandFile "%~dp0latveria_lighting_commands.txt" -Centre "799 70 -10090" %*
pause
