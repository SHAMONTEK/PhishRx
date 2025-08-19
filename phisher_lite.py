# ai_window.py (Enhanced UI ×3 + Hugging Face API + Threat Intel)
print("📍 App started!")

import pystray
from PIL import Image
import pytesseract
import pyautogui
import os
import subprocess
import re
from datetime import datetime
import sys

PHISHING_KEYWORDS = [
    "click here", "verify", "urgent", "account suspended", "reset password",
    "login now", "security alert", "confirm", "update info", "billing problem"
]
SAVE_DIR = os.path.expanduser("~/Desktop/phish_screenshots")
os.makedirs(SAVE_DIR, exist_ok=True)

def notify_mac(title, message):
    try:
        subprocess.run([
            "terminal-notifier",
            "-title", title,
            "-message", message,
            "-group", "phish-er-lite"
        ])
    except Exception as e:
        print("Notification Error:", e)

def detect_phishing(text):
    found = [kw for kw in PHISHING_KEYWORDS if kw in text.lower()]
    urls = re.findall(r'https?://\S+', text)
    if urls:
        found.append("Contains URL")
    return found

def create_tray_icon_image():
    return Image.open("phishericon.png")

def scan_screen():
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    screenshot_path = os.path.join(SAVE_DIR, f"screenshot_{timestamp}.png")

    screenshot = pyautogui.screenshot()
    screenshot.save(screenshot_path)

    text = pytesseract.image_to_string(screenshot)
    reasons = detect_phishing(text)
    if len(reasons) >= 3:
        severity = "🚨 HIGH RISK"
    elif len(reasons) >= 1:
        severity = "⚠️ MEDIUM RISK"
    else:
        severity = "✅ SAFE"

    summary = f"{severity}\nReasons: {', '.join(reasons) if reasons else 'None'}"
    notify_mac("PHISH-ER Scan", summary)
    print(summary)

    try:
        print("🧠 Launching external AI window...")
        subprocess.Popen([
            "python3", "phisher_ai_gui.py", severity, "|".join(reasons), screenshot_path
        ])
    except Exception as e:
        print(f"❌ Failed to open AI GUI window: {e}")

def run_tray():
    def quit_action(icon, item):
        icon.stop()
        os._exit(0)

    icon = pystray.Icon("PHISH-ER", create_tray_icon_image(), "PHISH-ER Lite", menu=pystray.Menu(
        pystray.MenuItem("📸 Scan Screen", lambda icon, item: scan_screen()),
        pystray.MenuItem("❌ Quit", quit_action)
    ))
    icon.run()

if __name__ == "__main__":
    run_tray()
