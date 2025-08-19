#!/bin/zsh
cd "$(dirname "$0")"

# Activate virtual environment
source venv/bin/activate

# Launch PHISH-ER main app in the background
python3 phisher_lite.py &

# Launch tray icon (menu bar app) in the background


echo ""
echo "=== PHISH-ER + Tray launched. Press ENTER to close this window. ==="
read
