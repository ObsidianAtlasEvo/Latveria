@echo off
rem Optional: re-seat the nursery beds so that claims held by children who have left are released.
rem Run it after Refinement v3, whenever you want the nursery to breed again. Safe to repeat.
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Build-Latveria-Refinement-V3.ps1" -CommandFile "%~dp0latveria_v3_nursery_reset_commands.txt" -Centre "799 70 -10090" %*
pause
