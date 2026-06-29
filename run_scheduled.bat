@echo off
setlocal EnableExtensions

set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

set "PYTHON=%PROJECT_DIR%.venv\Scripts\python.exe"
set "LOG_DIR=%PROJECT_DIR%output\logs"
set "TIMESTAMP=%date:~-4%%date:~3,2%%date:~0,2%_%time:~0,2%%time:~3,2%%time:~6,2%"
set "TIMESTAMP=%TIMESTAMP: =0%"
set "LOG_FILE=%LOG_DIR%\run_%TIMESTAMP%.log"
set "LATEST_LOG=%LOG_DIR%\latest.log"

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

echo ============================================================ >> "%LOG_FILE%"
echo Started at %date% %time% >> "%LOG_FILE%"
echo Project: %PROJECT_DIR% >> "%LOG_FILE%"
echo ============================================================ >> "%LOG_FILE%"

if not exist "%PYTHON%" (
    echo ERROR: Python not found at %PYTHON% >> "%LOG_FILE%"
    echo Run: uv sync >> "%LOG_FILE%"
    copy /y "%LOG_FILE%" "%LATEST_LOG%" >nul
    exit /b 1
)

"%PYTHON%" main.py all --store all >> "%LOG_FILE%" 2>&1
set "EXIT_CODE=%ERRORLEVEL%"

echo ============================================================ >> "%LOG_FILE%"
echo Finished at %date% %time% with exit code %EXIT_CODE% >> "%LOG_FILE%"
echo ============================================================ >> "%LOG_FILE%"

copy /y "%LOG_FILE%" "%LATEST_LOG%" >nul
exit /b %EXIT_CODE%
