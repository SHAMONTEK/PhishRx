#!/bin/zsh
cd "$(dirname "$0")"

echo "=== Activating Virtual Environment ==="
source venv/bin/activate

echo "=== Installing Core Dependencies ==="
pip install torch transformers Pillow opencv-python
pip install -r requirements.txt
pip install accelerate>=0.26.0
echo "=== Setting Up Guardian AI Models ==="
# Create models directory
mkdir -p models

# Download models in background (non-blocking)
python3 -c "
from components.guardian_vision import GuardianVision
print('✅ Vision system pre-loaded successfully')
" &

echo "=== Launching GUARDIAN AI ==="
python3 phisher_lite.py &

echo "=== System ready! Press ENTER to close ==="
read