@echo off
setlocal EnableExtensions

set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

set "LOG_DIR=%PROJECT_DIR%output\logs"
set "TIMESTAMP=%date:~-4%%date:~3,2%%date:~0,2%_%time:~0,2%%time:~3,2%%time:~6,2%"
set "TIMESTAMP=%TIMESTAMP: =0%"
set "LOG_FILE=%LOG_DIR%\git_push_%TIMESTAMP%.log"
set "LATEST_LOG=%LOG_DIR%\git_push_latest.log"
set "COMMIT_DATE=%date:~-4%-%date:~3,2%-%date:~0,2%"

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

echo ============================================================ >> "%LOG_FILE%"
echo Git push started at %date% %time% >> "%LOG_FILE%"
echo Project: %PROJECT_DIR% >> "%LOG_FILE%"
echo ============================================================ >> "%LOG_FILE%"

where git >nul 2>&1
if errorlevel 1 (
    echo ERROR: git not found in PATH >> "%LOG_FILE%"
    copy /y "%LOG_FILE%" "%LATEST_LOG%" >nul
    exit /b 1
)

if not exist "%PROJECT_DIR%.git" (
    echo ERROR: not a git repository >> "%LOG_FILE%"
    copy /y "%LOG_FILE%" "%LATEST_LOG%" >nul
    exit /b 1
)

git add -A >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    echo ERROR: git add failed >> "%LOG_FILE%"
    copy /y "%LOG_FILE%" "%LATEST_LOG%" >nul
    exit /b 1
)

git diff --cached --quiet >> "%LOG_FILE%" 2>&1
if not errorlevel 1 (
    echo No changes to commit >> "%LOG_FILE%"
    goto :finish
)

git commit -m "chore: daily sync %COMMIT_DATE%" >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    echo ERROR: git commit failed >> "%LOG_FILE%"
    copy /y "%LOG_FILE%" "%LATEST_LOG%" >nul
    exit /b 1
)

git pull --rebase origin main >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    echo ERROR: git pull failed >> "%LOG_FILE%"
    copy /y "%LOG_FILE%" "%LATEST_LOG%" >nul
    exit /b 1
)

git push origin main >> "%LOG_FILE%" 2>&1
set "EXIT_CODE=%ERRORLEVEL%"
if errorlevel 1 (
    echo ERROR: git push failed >> "%LOG_FILE%"
    copy /y "%LOG_FILE%" "%LATEST_LOG%" >nul
    exit /b %EXIT_CODE%
)

:finish
echo ============================================================ >> "%LOG_FILE%"
echo Finished at %date% %time% with exit code 0 >> "%LOG_FILE%"
echo ============================================================ >> "%LOG_FILE%"

copy /y "%LOG_FILE%" "%LATEST_LOG%" >nul
exit /b 0
