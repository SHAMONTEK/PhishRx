#!/usr/bin/env python3
# phisher_lite.py / ai_window.py – cleaned up

print("📍 Welcome Shamonte. Your GUARDIAN AI App started!")

import os
import re
import sys
import subprocess
from datetime import datetime

import pystray
from PIL import Image
import pyautogui
import pytesseract

try:
    from components.analytics import analytics
except ImportError:
    print("ℹ️ Analytics not available – running without learning.")
    analytics = None

PHISHING_KEYWORDS = [
    "click here", "verify", "urgent", "account suspended", "reset password",
    "login now", "security alert", "confirm", "update info", "billing problem",
]

SAVE_DIR = os.path.expanduser("~/Desktop/phish_screenshots")
os.makedirs(SAVE_DIR, exist_ok=True)


def notify_mac(title: str, message: str) -> None:
    """Send a macOS notification (best‑effort)."""
    try:
        subprocess.run(
            [
                "terminal-notifier",
                "-title", title,
                "-message", message,
                "-group", "GUARDIAN AI",
            ],
            check=False,
        )
    except Exception as e:
        print("Notification error:", e)


def detect_phishing(text: str) -> list[str]:
    """Return list of matched heuristic indicators from page text."""
    found = [kw for kw in PHISHING_KEYWORDS if kw in text.lower()]
    urls = re.findall(r"https?://\S+", text)
    if urls:
        found.append("Contains URL")
    return found


def create_tray_icon_image() -> Image.Image:
    """Load tray icon image or fall back to a simple placeholder."""
    try:
        here = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(here, "phishericon.png")
        return Image.open(icon_path)
    except Exception as e:
        print("⚠️ Could not load phishericon.png, using blank icon:", e)
        # simple 32x32 gray square as fallback
        return Image.new("RGB", (32, 32), (80, 80, 80))


def scan_screen() -> None:
    """Capture the screen, OCR it, score risk, notify, update analytics, launch GUI."""
    try:
        notify_mac("GUARDIAN AI", "🔄 Scanning screen...")

        # 1. Screenshot
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        screenshot_path = os.path.join(SAVE_DIR, f"screenshot_{timestamp}.png")
        screenshot = pyautogui.screenshot()
        screenshot.save(screenshot_path)

        # 2. OCR + keyword / URL analysis
        notify_mac("GUARDIAN AI", "🔍 Analyzing text...")
        text = pytesseract.image_to_string(screenshot)  # or Image.open(screenshot_path)
        reasons = detect_phishing(text)

        # 3. Severity logic
        threat_score = len(reasons)
        if threat_score >= 3:
            severity = "🚨 HIGH RISK"
        elif threat_score >= 1:
            severity = "⚠️ MEDIUM RISK"
        else:
            severity = "✅ SAFE"

        summary = f"{severity}\nReasons: {', '.join(reasons) if reasons else 'None'}"

        # 4. Analytics (optional)
        if analytics is not None:
            # Until GUI feedback is wired, treat initial heuristic as “guess”
            was_correct = True  # will be refined later by feedback
            confidence = 0.8 if severity != "✅ SAFE" else 0.2
            try:
                analytics.record_scan_result(was_correct, confidence, severity)
                current_accuracy = analytics.calculate_accuracy()
                print(f"📈 Current Accuracy: {current_accuracy:.1%}")
            except Exception as e:
                print("Analytics error:", e)

        # 5. Notify + log
        notify_mac("GUARDIAN AI", f"✅ Scan Complete\n{summary}")
        print(summary)

        # 6. Launch full Guardian AI window (GUI)
        try:
            print("🧠 Launching GUARDIAN AI window...")
            subprocess.Popen(
                [
                    sys.executable,
                    "phisher_ai_gui.py",
                    severity,
                    "|".join(reasons),
                    screenshot_path,
                ]
            )
        except Exception as e:
            print(f"❌ Failed to open AI GUI window: {e}")

    except Exception as e:
        notify_mac("GUARDIAN AI", f"❌ Scan Failed\nError: {str(e)}")
        print("❌ Scan error:", e)


def view_scan_history() -> None:
    """Quick view of how many screenshots/scans have been saved."""
    try:
        screenshots = [
            f for f in os.listdir(SAVE_DIR) if f.startswith("screenshot_")
        ]
        notify_mac("GUARDIAN AI", f"📊 Scan History\nTotal scans: {len(screenshots)}")
        print(f"📊 Found {len(screenshots)} previous scans")
    except Exception as e:
        notify_mac("GUARDIAN AI", f"❌ No scan history\nError: {e}")
        print("History error:", e)


def run_tray() -> None:
    def quit_action(icon, item):
        icon.stop()
        os._exit(0)

    icon = pystray.Icon(
        "GUARDIAN AI",
        create_tray_icon_image(),
        "GUARDIAN AI",
        menu=pystray.Menu(
            pystray.MenuItem("📸 Scan Screen", lambda _icon, _item: scan_screen()),
            pystray.MenuItem(
                "📊 View Scan History",
                lambda _icon, _item: view_scan_history(),
            ),
            pystray.MenuItem("❌ Quit", quit_action),
        ),
    )
    icon.run()


if __name__ == "__main__":
    run_tray()
