@echo off
rem Latveria Refinement v3 - run AFTER the main build, the expansion and the lighting overhaul.
rem Additive: nothing is cleared and no gamerule is changed. Every section can be re-run.
rem Uses the centre of the first build (799 70 -10090); you are asked to confirm it.
rem Extra options, e.g.:  Build-Latveria-Refinement-V3.bat -Section "Golem"   or   -ListSections
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Build-Latveria-Refinement-V3.ps1" -CommandFile "%~dp0latveria_refinement_v3_commands.txt" -Centre "799 70 -10090" %*
pause
