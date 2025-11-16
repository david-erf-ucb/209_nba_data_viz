Param()

# Start Flask (8001) and Streamlit (8501) locally.
# No app code is modified; this just automates venv + installs + run.

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoDir = Join-Path $ScriptDir ".."
Set-Location $RepoDir

if (-not (Test-Path ".venv")) {
  python -m venv .venv
}

& .\.venv\Scripts\Activate.ps1
python -m pip install -U pip
pip install -r requirements.txt -r requirements-streamlit.txt

# Kill any previous instances
Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "*\.venv\*" -and ($_.MainWindowTitle -like "*app.py*" -or $_.ProcessName -eq "python") } | Stop-Process -Force -ErrorAction SilentlyContinue
Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "*streamlit.exe" } | Stop-Process -Force -ErrorAction SilentlyContinue

# Start Flask (8001)
Start-Process -NoNewWindow -FilePath "python" -ArgumentList "app.py"
Start-Sleep -Seconds 1

# Start Streamlit (8501)
Start-Process -NoNewWindow -FilePath "streamlit" -ArgumentList "run `"nba_scatter_live_app.py`" --server.port 8501 --server.baseUrlPath /nba --server.headless true"
Start-Sleep -Seconds 2

Write-Host ""
Write-Host "Flask:     http://localhost:8001"
Write-Host "Explorer:  http://localhost:8501/nba"
Write-Host ""
Write-Host "Tip: Close these processes from Task Manager or close this PowerShell session."



