# FALLON Launcher - Run this to start the app
$ErrorActionPreference = "Stop"

# Kill any existing Python/Streamlit processes
Get-Process | Where-Object {$_.ProcessName -match "python"} | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# Set working directory
Set-Location $PSScriptRoot
Set-Location ..

# Start Streamlit in background
$job = Start-Job -ScriptBlock {
    Set-Location $using:PWD
    python -m streamlit run FallonPrototype/app.py
}

# Wait for server to start
Start-Sleep -Seconds 5

# Open in Microsoft Edge
Start-Process "msedge" "http://localhost:8501"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  FALLON is running at localhost:8501  " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Keep script running
try {
    while ($true) {
        Receive-Job $job
        Start-Sleep -Seconds 1
    }
} finally {
    Stop-Job $job
    Remove-Job $job
    Get-Process | Where-Object {$_.ProcessName -match "python"} | Stop-Process -Force -ErrorAction SilentlyContinue
}
