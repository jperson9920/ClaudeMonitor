#requires -Version 5.1
$ErrorActionPreference = 'Stop'

$activatePath = ".\scraper-env\Scripts\Activate.ps1"
if (Test-Path $activatePath) {
    Write-Host "Activating virtualenv..."
    & $activatePath
} else {
    Write-Host "Virtualenv not found. Run .\setup.ps1 first or activate a Python venv that has scraper requirements installed."
    exit 2
}

Write-Host ""
Write-Host "Starting manual login flow for Claude scraper..."
Write-Host "A Chrome window will open. Complete the login and any CAPTCHAs/2FA in the browser."
Write-Host "Do NOT close the Chrome window until the script indicates success."
Write-Host ""
Read-Host -Prompt "Press ENTER to continue and open Chrome for manual login"

$proc = Start-Process -NoNewWindow -FilePath (Get-Command python).Source -ArgumentList "-m","src.scraper.claude_scraper","--login" -PassThru -Wait
$exitCode = $proc.ExitCode

Write-Host ""
if ($exitCode -eq 0) {
    Write-Host "Login succeeded. Session data saved to scraper/chrome-profile/ (if implemented)."
    Write-Host "Logs written to scraper/scraper.log"
} else {
    Write-Host "Login process exited with code $exitCode. Check scraper/scraper.log for details."
}

exit $exitCode