#!/usr/bin/env bash
set -euo pipefail

if [ -f "scraper-env/bin/activate" ]; then
  # shellcheck source=/dev/null
  source scraper-env/bin/activate
else
  echo "Virtualenv not found. Run ./setup.sh first or ensure Python venv is active."
  exit 2
fi

echo "Starting manual login flow for Claude scraper..."
echo "A Chrome window will open. Complete the login and any CAPTCHAs/2FA in the browser."
echo "Do NOT close the Chrome window until the script indicates success."
echo ""
echo "Press ENTER to continue and open Chrome for manual login..."
read -r _

python -m src.scraper.claude_scraper --login

echo ""
echo "If login succeeded, session data will be saved to scraper/chrome-profile/ and logs are in scraper/scraper.log"
exit $?