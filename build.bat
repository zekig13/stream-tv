@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  python -m venv .venv
  ".venv\Scripts\python.exe" -m pip install --upgrade pip
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt
)
".venv\Scripts\python.exe" -m pip install "pyinstaller==6.11.1"
".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean --windowed --onefile --name "StreamTV" --collect-all customtkinter --collect-all darkdetect --hidden-import=bs4 --hidden-import=lxml --hidden-import=PIL --hidden-import=vlc --hidden-import=app --hidden-import=app.version --hidden-import=app.ui.main_window --hidden-import=app.fetcher.countries --hidden-import=app.fetcher.m3u_parser --hidden-import=app.player.vlc_player --hidden-import=app.settings.config main.py

if exist "dist\StreamTV.exe" (
  if not exist releases mkdir releases
  copy /Y "dist\StreamTV.exe" "releases\StreamTV.exe" >nul
  echo Built: dist\StreamTV.exe
) else (
  echo Build failed.
  exit /b 1
)
endlocal
