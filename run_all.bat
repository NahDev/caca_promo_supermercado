@echo off
setlocal EnableExtensions

set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

uv run python main.py all --store all
exit /b %ERRORLEVEL%
