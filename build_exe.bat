@echo off
title PhoneToolKit EXE Builder
color 0A

echo ================================================
echo     PhoneToolKit EXE Builder
echo ================================================
echo.

:: Check if Python is available
where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python not found in PATH
    echo Please install Python 3.8+ and add to PATH
    pause
    exit /b 1
)

:: Add Python Scripts to PATH (common locations)
set "PYTHON_SCRIPTS=%APPDATA%\Python\Python314\Scripts"
if exist "%PYTHON_SCRIPTS%\pyinstaller.exe" (
    set "PATH=%PYTHON_SCRIPTS%;%PATH%"
    echo [INFO] Added %PYTHON_SCRIPTS% to PATH
)

:: Also check for Python installation in AppData\Local
for /d %%p in ("%LOCALAPPDATA%\Programs\Python\Python*") do (
    if exist "%%p\Scripts\pyinstaller.exe" (
        set "PATH=%%p\Scripts;%PATH%"
        echo [INFO] Added %%p\Scripts to PATH
    )
)

:: Check if PyInstaller is available
where pyinstaller >nul 2>nul
if errorlevel 1 (
    echo [INFO] PyInstaller not found in PATH, installing...
    python -m pip install pyinstaller --user
    if errorlevel 1 (
        echo [ERROR] Failed to install PyInstaller
        pause
        exit /b 1
    )
    :: Refresh PATH after install
    set "PYTHON_SCRIPTS=%APPDATA%\Python\Python314\Scripts"
    set "PATH=%PYTHON_SCRIPTS%;%PATH%"
)

:: Install dependencies (includes Pillow for icon conversion)
echo [INFO] Installing dependencies...
python -m pip install -r requirements.txt --user
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)

:: Build EXE
echo [INFO] Building EXE with PyInstaller...
python -m PyInstaller PhoneToolKit.spec --clean --noconfirm
if errorlevel 1 (
    echo [INFO] Retrying with pyinstaller binary...
    pyinstaller PhoneToolKit.spec --clean --noconfirm
)

if errorlevel 1 (
    echo [ERROR] Build failed
    pause
    exit /b 1
)

echo.
echo ================================================
echo     BUILD SUCCESSFUL!
echo ================================================
echo.
echo EXE location: dist\PhoneToolKit.exe
echo.
echo To test: dist\PhoneToolKit.exe
echo.
pause