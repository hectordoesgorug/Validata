@echo off
setlocal
cd /d "%~dp0"

set "PYTHON=%~dp0.venv\Scripts\python.exe"

if not exist "%PYTHON%" (
    echo ERROR: Python virtual environment not found.
    echo Expected: "%PYTHON%"
    echo Check the environment setup instructions in README.md.
    pause
    exit /b 1
)

"%PYTHON%" -m validata
set "EXIT_CODE=%ERRORLEVEL%"

if not "%EXIT_CODE%"=="0" (
    echo.
    echo Validata exited with error code %EXIT_CODE%.
    pause
)
exit /b %EXIT_CODE%
