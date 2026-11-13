# PhoneToolKit EXE Builder - PowerShell Version
# Run with: powershell -ExecutionPolicy Bypass -File build_exe.ps1

Write-Host "================================================" -ForegroundColor Green
Write-Host "     PhoneToolKit EXE Builder" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""

# Check Python
$pythonPath = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $pythonPath) {
    Write-Error "Python not found in PATH. Install Python 3.8+ and add to PATH."
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "Found Python: $pythonPath" -ForegroundColor Cyan

# Add common Python Scripts paths to PATH
$pythonScriptsPaths = @(
    "$env:APPDATA\Python\Python314\Scripts",
    "$env:LOCALAPPDATA\Programs\Python\Python314\Scripts",
    "$env:LOCALAPPDATA\Programs\Python\Python313\Scripts",
    "$env:LOCALAPPDATA\Programs\Python\Python312\Scripts",
    "$env:LOCALAPPDATA\Programs\Python\Python311\Scripts",
    "$env:LOCALAPPDATA\Programs\Python\Python310\Scripts"
)

foreach ($path in $pythonScriptsPaths) {
    if (Test-Path "$path\pyinstaller.exe") {
        $env:PATH = "$path;$env:PATH"
        Write-Host "Added to PATH: $path" -ForegroundColor Yellow
        break
    }
}

# Check pyinstaller
$pyinstallerPath = (Get-Command pyinstaller -ErrorAction SilentlyContinue).Source
if (-not $pyinstallerPath) {
    Write-Host "PyInstaller not found, installing..." -ForegroundColor Yellow
    python -m pip install pyinstaller --user
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to install PyInstaller"
        Read-Host "Press Enter to exit"
        exit 1
    }
    # Refresh PATH
    $env:PATH = "$env:APPDATA\Python\Python314\Scripts;$env:PATH"
    $pyinstallerPath = (Get-Command pyinstaller -ErrorAction SilentlyContinue).Source
}

Write-Host "Using PyInstaller: $pyinstallerPath" -ForegroundColor Cyan

# Install dependencies (includes Pillow for icon conversion)
Write-Host "Installing dependencies..." -ForegroundColor Yellow
python -m pip install -r requirements.txt --user
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to install dependencies"
    Read-Host "Press Enter to exit"
    exit 1
}

# Build EXE
Write-Host "Building EXE with PyInstaller..." -ForegroundColor Yellow
python -m PyInstaller PhoneToolKit.spec --clean --noconfirm
if ($LASTEXITCODE -ne 0) {
    Write-Host "Retrying with pyinstaller directly..." -ForegroundColor Yellow
    pyinstaller PhoneToolKit.spec --clean --noconfirm
}
if ($LASTEXITCODE -ne 0) {
    Write-Error "Build failed"
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host "     BUILD SUCCESSFUL!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "EXE location: dist\PhoneToolKit.exe" -ForegroundColor Cyan
Write-Host ""
Write-Host "To test: .\dist\PhoneToolKit.exe" -ForegroundColor Cyan
Write-Host ""
Read-Host "Press Enter to exit"