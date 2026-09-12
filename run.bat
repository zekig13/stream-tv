@echo off
setlocal
cd /d "%~dp0"

where python >nul 2>&1
if errorlevel 1 (
    echo Python bulunamadi. Lutfen Python 3.11+ kurun: https://www.python.org/downloads/
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo Sanal ortam olusturuluyor...
    python -m venv .venv
    if errorlevel 1 (
        echo venv olusturulamadi.
        pause
        exit /b 1
    )
    echo Bagimliliklar yukleniyor...
    ".venv\Scripts\python.exe" -m pip install --upgrade pip
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
)

echo Stream TV baslatiliyor...
".venv\Scripts\python.exe" -m app
if errorlevel 1 (
    echo.
    echo Uygulama hata ile kapandi.
    pause
)
endlocal
