# utils.py 
import customtkinter as ctk
import re
from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError
import os
import sys
import numpy as np

# --- OCR Imports ---
try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except ImportError:
    print("⚠️ pytesseract not found. OCR will be mocked.")
    PYTESSERACT_AVAILABLE = False

PIL_AVAILABLE = True
SCAN_HISTORY_FILE = 'scan_history.csv'

# === THEME ===
class AppColors:
    LIGHT_BACKGROUND = "#f0f2f5"
    LIGHT_CARD = "#ffffff"
    LIGHT_CHAT_USER = "#007aff"
    LIGHT_CHAT_BOT = "#e5e5ea"
    LIGHT_TEXT_PRIMARY = "#000000"
    LIGHT_TEXT_SECONDARY = "#8a8a8e"
    LIGHT_BORDER = "#d1d1d6"
    DARK_BACKGROUND = "#000000"
    DARK_CARD = "#1c1c1e"
    DARK_CHAT_USER = "#0a84ff"
    DARK_CHAT_BOT = "#2c2c2e"
    DARK_TEXT_PRIMARY = "#ffffff"
    DARK_TEXT_SECONDARY = "#8e8e93"
    DARK_BORDER = "#3a3a3c"
    RED = "#ff3b30"
    YELLOW = "#ffcc00"
    GREEN = "#34c759"
    BLUE = LIGHT_CHAT_USER

class AppFonts:
    PRIMARY_FAMILY = "Arial"
    TITLE = None
    SUBTITLE = None
    CHAT_FONT = None
    BUTTON_FONT = None
    INFO_FONT = None
    
    @classmethod
    def init_fonts(cls):
        try:
            ctk.CTkFont(family="Helvetica Neue")
            cls.PRIMARY_FAMILY = "Helvetica Neue"
            print("✅ Using 'Helvetica Neue' font.")
        except Exception:
            cls.PRIMARY_FAMILY = "Arial"
            print("⚠️ Using fallback font 'Arial'.")
        
        cls.TITLE = ctk.CTkFont(family=cls.PRIMARY_FAMILY, size=24, weight="bold")
        cls.SUBTITLE = ctk.CTkFont(family=cls.PRIMARY_FAMILY, size=18, weight="bold")
        cls.CHAT_FONT = ctk.CTkFont(family=cls.PRIMARY_FAMILY, size=15)
        cls.BUTTON_FONT = ctk.CTkFont(family=cls.PRIMARY_FAMILY, size=14, weight="normal")
        cls.INFO_FONT = ctk.CTkFont(family=cls.PRIMARY_FAMILY, size=12)

# === IMAGE LOADING ===
def load_ctk_image(path, size=(100, 100)):
    if not PIL_AVAILABLE or not os.path.exists(path):
        return None
    try:
        img = Image.open(path)
        img = img.resize(size, Image.Resampling.LANCZOS)
        return ctk.CTkImage(light_image=img, dark_image=img, size=size)
    except Exception as e:
        print(f"Error loading image: {e}")
        return None

# === OCR ===
def perform_ocr(image_path: str) -> str:
    if not PYTESSERACT_AVAILABLE:
        print("Mock OCR: Returning dummy text.")
        return """
        Subject: URGENT: Verify Your Account Password!
        Dear User, please confirm your password by clicking here: http://example-phish.com
        Thanks, Support Team
        """
    try:
        if not os.path.exists(image_path):
            return f"Error: Image path not found: {image_path}"
        
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img)
        return text.strip() if text.strip() else "No text found in image."
    except Exception as e:
        print(f"Error during OCR: {e}")
        return f"Error performing OCR: {e}"

# === SCAM ANALYSIS ===
def analyze_screenshot_advanced(image_path, ocr_text):
    try:
        from components.scam_classifier import scam_classifier
        result = scam_classifier.analyze_scam_risk(ocr_text)
        
        reasons_formatted = []
        reason_mapping = {
            "urgency_language": ("Urgent language detected", "Urgency"),
            "suspicious_url": ("Suspicious URL pattern", "Suspicious URL"),
            "password_request": ("Password/credential request", "Credential Theft"),
            "suspicious_popup": ("Suspicious popup/window", "UI Deception"),
            "ml_detected_phishing": ("AI detected phishing pattern", "ML Classification"),
            "ml_detected_urgent": ("AI detected urgency scam", "ML Classification")
        }
        
        for reason in result["reasons"]:
            if reason in reason_mapping:
                reasons_formatted.append(reason_mapping[reason])
            else:
                reasons_formatted.append((reason, "AI Detection"))
        
        print(f"🔍 ACTORS Analysis: {result['severity'].upper()} risk")
        print(f"   ML Confidence: {result.get('ml_confidence', 0):.2f}")
        
        return {
            "severity": result["severity"],
            "reasons": reasons_formatted,
            "confidence": result["confidence"],
            "ml_analysis": result
        }
        
    except Exception as e:
        print(f"❌ ML analysis failed: {e}")
        return _fallback_regex_analysis(ocr_text)

def _fallback_regex_analysis(ocr_text: str):
    findings = []
    text_lower = ocr_text.lower()

    if re.search(r'urgent|immediately|action required|verify now', text_lower):
        findings.append(("Urgent language detected", "Urgency"))
    
    if re.search(r'dear user|dear customer|valued member', text_lower):
        findings.append(("Generic greeting", "Impersonal"))

    urls = re.findall(r'https?://[^\s]+', text_lower)
    suspicious_domains = ['bit.ly', 'tinyurl', 'click-here', 'verify-account']
    for url in urls:
        if any(domain in url for domain in suspicious_domains):
            findings.append((f"Suspicious URL: {url[:50]}...", "Suspicious URL"))
            break

    if re.search(r'password|login|credentials|account verification', text_lower):
        findings.append(("Password/credential request", "Credential Theft"))

    if re.search(r'paypal|bank|credit card|ssn|social security', text_lower):
        findings.append(("Financial information request", "Financial"))

    return findings

# === UTILITIES ===
def calculate_text_entropy(text: str) -> float:
    if len(text) == 0:
        return 0.0
    from collections import Counter
    counts = Counter(text)
    return -sum((count/len(text)) * np.log2(count/len(text)) for count in counts.values())

def extract_urls(text: str) -> list[str]:
    import re
    return re.findall(r'https?://[^\s]+', text)

def contains_financial_terms(text: str) -> bool:
    financial_terms = ["paypal", "bank", "credit card", "ssn", "social security"]
    return any(term in text.lower() for term in financial_terms)

def create_test_image(filepath: str, text: str = "Test phishing content") -> bool:
    if not PIL_AVAILABLE:
        return False
    try:
        img = Image.new('RGB', (600, 400), color=(200, 220, 255))
        draw = ImageDraw.Draw(img)
        try: 
            fnt = ImageFont.truetype("arial.ttf", 15)
        except IOError: 
            fnt = ImageFont.load_default()
        draw.text((10, 10), text, fill=(0, 0, 0), font=fnt)
        img.save(filepath)
        return True
    except Exception as e:
        print(f"Failed to create test image: {e}")
        return False