@echo off
cd /d "%~dp0"
python scripts/verify_project.py %*
exit /b %ERRORLEVEL%
