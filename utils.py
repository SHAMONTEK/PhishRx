# utils.py
import os
import re
import sys # Needed for platform check in force_window_focus
import pytesseract
import customtkinter as ctk # Import CTkImage here
from customtkinter import CTkImage
import tkinter # Needed for TclError in force_window_focus

# Attempt to import Pillow (PIL) for image handling
# Define PIL_AVAILABLE globally within this module
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("⚠️ Warning: PIL (Pillow) not installed. Image display will use placeholders.")


# --- Configuration ---
SCAN_HISTORY_FILE = "scan_history.csv" # Define scan history file name

# --- Theme Colors (Dark Mode from UI Specification) ---
COLOR_BACKGROUND = "#1B1F23"        # Dark Charcoal
COLOR_CARD = "#22272E"              # Slightly lighter card background
COLOR_BORDER = "#2F363D"            # Subtle Gray Divider/Border
COLOR_TEXT_PRIMARY = "#E6EDF3"      # Light Gray/White Text
COLOR_TEXT_SECONDARY = "#8B949E"    # Medium Gray Text
COLOR_TEXT_ACCENT = "#007AFF"       # Vibrant Blue (Buttons, Links, Title)
COLOR_TEXT_INFO = "#58A6FF"         # Lighter Blue for info emphasis
COLOR_TEXT_ERROR = "#F04A4A"        # Alert Red
COLOR_SEVERITY_HIGH = "#F04A4A"
COLOR_SEVERITY_MEDIUM = "#F7B731"   # Adjusted Yellow/Orange for dark mode
COLOR_SEVERITY_LOW = "#58A6FF"      # Use Accent Blue for Low
COLOR_SEVERITY_SAFE = "#3FB950"     # Green for Safe

# --- Button Colors ---
COLOR_BUTTON_PRIMARY_FG = "#007AFF"
COLOR_BUTTON_PRIMARY_HOVER = "#005FCC" # Spec: Slight Blue Tint
COLOR_BUTTON_PRIMARY_TEXT = "#FFFFFF" # White text on blue button

# Secondary/Smart Question Buttons (Darker Background)
COLOR_BUTTON_SECONDARY_FG = "#2F363D" # Darker Gray for secondary buttons
COLOR_BUTTON_SECONDARY_HOVER = "#484F58" # Lighter Gray on hover
COLOR_BUTTON_SECONDARY_TEXT = "#E6EDF3" # Light text

# Copy Button (Matches Secondary)
COLOR_BUTTON_COPY_FG = COLOR_BUTTON_SECONDARY_FG
COLOR_BUTTON_COPY_HOVER = COLOR_BUTTON_SECONDARY_HOVER
COLOR_BUTTON_COPY_TEXT = COLOR_BUTTON_SECONDARY_TEXT

# --- Fonts (Using Tuples - Prioritize Inter if available) ---
# Define base font family - adjust if Inter isn't available system-wide
BASE_FONT_FAMILY = "Inter" # Or "Arial", "Roboto", "Segoe UI" as fallbacks

try:
    # Test if the base font is available (this is a basic check)
    import tkinter.font
    # Create a temporary root window only if one doesn't already exist
    try:
        # Attempt to get the default root window if it exists
        root = tkinter._get_default_root('Error checking fonts')
        root_created = False
        if root is None: # If no default root, create one
             raise tkinter.TclError("No default root window")
    except (tkinter.TclError, AttributeError): # Catch error if no default root
        root = tkinter.Tk()
        root_created = True

    if root: # Proceed only if we have a root window
        if root_created:
            root.withdraw() # Hide the window if we created it
        available_fonts = list(tkinter.font.families(root)) # Pass root explicitly
        if root_created:
            root.destroy() # Destroy the temporary window if we created it

        if BASE_FONT_FAMILY not in available_fonts:
            print(f"⚠️ Warning: Font '{BASE_FONT_FAMILY}' not found. Falling back to 'Arial'.")
            BASE_FONT_FAMILY = "Arial" # Default fallback
    else:
         print("⚠️ Could not get root window to check fonts. Defaulting to Arial.")
         BASE_FONT_FAMILY = "Arial"

except Exception as e:
    print(f"⚠️ Error checking fonts, defaulting to Arial: {e}")
    BASE_FONT_FAMILY = "Arial"

# Font definitions based on spec (adjust pt sizes if needed)
TITLE_FONT = (BASE_FONT_FAMILY, 20, "bold")        # e.g., 18-22pt
LABEL_FONT = (BASE_FONT_FAMILY, 14, "bold")        # e.g., Body bold
INFO_FONT = (BASE_FONT_FAMILY, 12, "normal")       # e.g., Body normal (14pt in spec, using 12 for less critical info)
BODY_FONT = (BASE_FONT_FAMILY, 14, "normal")       # Font for main text like AI statement (14pt)
BUTTON_FONT = (BASE_FONT_FAMILY, 14, "bold")       # e.g., 16pt semi-bold (using 14 bold)
SMALL_BUTTON_FONT = (BASE_FONT_FAMILY, 12, "bold") # Slightly smaller for smart buttons
# --- ADDED MISSING TREEVIEW FONTS ---
TREEVIEW_FONT = (BASE_FONT_FAMILY, 11, "normal")      # Font for Treeview rows
TREEVIEW_HEAD_FONT = (BASE_FONT_FAMILY, 12, "bold")   # Font for Treeview headings
# --- END OF ADDED FONTS ---

# --- Suspicious Patterns (From User's File, refined regex) ---
SUSPICIOUS_PATTERNS = [
    # Regex Pattern                 # Label (Consider adding icons here too if desired)
    (r"https?://\S+", "🔗 Contains URL"),
    (r"\b(verify|confirm)\s+(your|my)\s+(account|identity|information)\b", "🔒 Verification prompt"),
    (r"\b(reset|update)\s+(your|my)\s+password\b", "🔐 Password reset"),
    (r"\b(urgent|immediate(ly)?|action\s+(required|needed)|final\s+notice)\b", "⚠️ Urgency"),
    (r"\bclick\s+here\b", "🖱️ Generic 'Click Here'"),
    (r"\baccount\s+(suspended|locked|compromised|closed|deactivated)\b", "🚫 Account Threat"),
    (r"\b(security|unusual|suspicious)\s+(alert|activity|login)\b", "🛡️ Security Alert"),
    (r"\b(won|prize|claim|lottery|winner)\b", "💰 Prize/Lottery Scam"),
    (r"\b(invoice|payment|due|overdue|bill)\b", "🧾 Fake Invoice/Payment"),
    (r"\b(dear\s+(user|customer|client)|hello\b((?!\s+\w+)|$))", "🏷️ Generic Greeting"), # More specific generic greeting
    (r"\b(password|passcode|credential)\b", "🔑 Password Mentioned"),
    (r"\b(account\s+number|ssn|social\s+security|bank\s+details)\b", "👤 Sensitive Info Request"),
    (r"\b(job\s+offer|hiring|recruiting|interview)\b", "💼 Suspicious Job Offer") # Added job offer
]


# --- Text Analysis ---
def find_suspicious_text(text):
    """Finds suspicious text patterns using regex."""
    results = []
    if not text:
        return results
    for pattern, label in SUSPICIOUS_PATTERNS:
        try:
            # Use finditer to find all non-overlapping matches
            for match in re.finditer(pattern, text, re.IGNORECASE):
                # Store the matched text and the label
                results.append((match.group(0).strip(), label))
        except re.error as e:
            print(f"Regex error for pattern '{pattern}': {e}")

    # Remove duplicates based on the matched text, keeping the first label found
    unique_results = []
    seen_matches = set()
    for match_text, label in results:
        # Use lower case for seen check to catch case variations of same match
        match_key = match_text.lower()
        # Basic check to avoid adding very short, potentially meaningless matches
        if len(match_key) > 2 and match_key not in seen_matches:
            unique_results.append((match_text, label))
            seen_matches.add(match_key)

    return unique_results

# --- OCR Function ---
def perform_ocr(image_path):
    """Extracts text from the specified image file using Tesseract."""
    try:
        print(f"Attempting OCR on: {image_path}")
        if not os.path.exists(image_path):
             print(f"❌ Error: Image file not found at {image_path}")
             return "Error: Image file not found."

        # Check if Tesseract executable path needs to be set explicitly
        # Example (uncomment and adjust path if needed):
        # if sys.platform == "win32":
        #     pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

        img = Image.open(image_path)
        ocr_text = pytesseract.image_to_string(img)
        print(f"✅ OCR successful. Text length: {len(ocr_text)}")
        return ocr_text.strip() # Return stripped text
    except pytesseract.TesseractNotFoundError:
         msg = "❌ Error: Tesseract is not installed or not in your system's PATH. Please install Tesseract OCR."
         print(msg)
         return "Error: Tesseract OCR engine not found."
    except FileNotFoundError:
         print(f"❌ Error: Image file disappeared before opening: {image_path}")
         return "Error: Image file disappeared."
    except Exception as e:
        print(f"❌ Error during OCR: {e}")
        return f"Error during OCR: {e}"


# --- UI Helper Functions ---
def force_window_focus(window):
    """Forces the window to the front (best effort, platform-dependent)."""
    print("Attempting to force window focus...")
    try:
        # Tkinter's methods first
        window.lift()
        window.focus_force() # Request focus
        window.attributes('-topmost', True) # Bring to top
        window.after(100, lambda: window.attributes('-topmost', False)) # Release topmost

        # Platform-specific attempts (might be less reliable)
        if sys.platform == "darwin": # macOS
            pid = os.getpid()
            script = f'''
            tell application "System Events"
                try
                    set frontmost of first process whose unix id is {pid} to true
                on error errMsg number errorNumber
                    log "Error focusing window (AppleScript): " & errMsg
                end try
            end tell
            '''
            os.system(f"/usr/bin/osascript -e '{script}' > /dev/null 2>&1") # Suppress output/errors
        elif sys.platform == "win32": # Windows
            import ctypes
            hwnd = window.winfo_id()
            if hwnd:
                ctypes.windll.user32.SetForegroundWindow(hwnd)
                ctypes.windll.user32.BringWindowToTop(hwnd)

    except tkinter.TclError as e:
         print(f"[Window Focus Error] Ignoring TclError: {e}")
    except Exception as e:
        print(f"[Window Focus Error] Could not force focus: {e}")


def load_ctk_image(path, size):
    """Safely loads a CTkImage using PIL, returning the image object or None."""
    # Use the global PIL_AVAILABLE check defined at the top of this file
    if PIL_AVAILABLE and os.path.exists(path):
        try:
            img = Image.open(path)
            # Ensure size is a tuple of integers
            size = (int(size[0]), int(size[1]))
            return CTkImage(img, size=size) # Return CTkImage directly
        except FileNotFoundError:
             print(f"Warning: Image file not found at {path} (inside load_ctk_image)")
             return None
        except Exception as e:
            print(f"Error loading image {path} with PIL: {e}")
            return None
    elif not os.path.exists(path):
         print(f"Warning: Image file not found at {path}")
         return None
    else: # PIL not available
         print(f"Cannot load image {path}: PIL (Pillow) is not installed.")
         return None
