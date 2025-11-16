#requires -Version 5.1
$ErrorActionPreference = 'Stop'

Write-Host "Creating Python virtualenv 'scraper-env' in project root..."
python -m venv scraper-env

Write-Host "Activating virtualenv for this session..."
# Activate affects this PowerShell session
& .\scraper-env\Scripts\Activate.ps1

Write-Host "Upgrading pip and installing requirements..."
python -m pip install --upgrade pip
pip install -r requirements.txt

Write-Host ""
Write-Host "Setup complete."
Write-Host "To activate the venv in a new PowerShell session run:"
Write-Host "  .\\scraper-env\\Scripts\\Activate.ps1"
Write-Host "Run manual login with:"
Write-Host "  .\\run_manual_login.ps1"

exit 0