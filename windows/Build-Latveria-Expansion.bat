@echo off
rem Latveria Survival Expansion v2 - run AFTER the main build has finished.
rem Uses the centre of the first build (799 70 -10090); you are asked to confirm it.
rem Extra options work as for Build-Latveria.bat, e.g.  -DelayMs 150   or   -FromSection "Harbour"
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Build-Latveria.ps1" -CommandFile "%~dp0latveria_expansion_commands.txt" -Centre "799 70 -10090" %*
pause
