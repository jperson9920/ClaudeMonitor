#!/usr/bin/env bash
set -euo pipefail

echo "Creating Python virtualenv 'scraper-env' in project root..."
python3 -m venv scraper-env

echo "Activating virtualenv..."
# shellcheck source=/dev/null
source scraper-env/bin/activate

python -m pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "Setup complete. To activate the venv in this shell run:"
echo "  source scraper-env/bin/activate"
echo "Run manual login with:"
echo "  ./run_manual_login.sh"

exit 0