# components/threat_breakdown.py
import customtkinter as ctk

try:
    import utils # Use the centralized utils module
except ImportError:
    print("Error: Unable to import 'utils' in threat_breakdown.py.")
    # Fallback mock for standalone testing (less likely needed now)
    class MockUtils:
        LABEL_FONT = ("Arial", 14, "bold")
        INFO_FONT = ("Arial", 12)
        COLOR_TEXT_PRIMARY = "#E6EDF3" # Dark mode fallback
        COLOR_TEXT_SECONDARY = "#8B949E"
    utils = MockUtils()

def create_threat_breakdown_section(parent_frame, flagged_items):
    """
    Creates and populates the threat breakdown section using theme colors
    and icons as per the dark UI specification.

    Args:
        parent_frame: The CTkFrame designated to hold the threat breakdown content.
                      This frame should be transparent as its parent provides the card background.
        flagged_items: A list of tuples, where each tuple is (phrase, reason).
    """
    # Configure the parent frame passed to it
    parent_frame.grid_columnconfigure(0, weight=1)
    parent_frame.grid_rowconfigure(1, weight=1) # Allow items frame to expand if needed

    # --- Title ---
    title = ctk.CTkLabel(parent_frame, text="Threat Breakdown",
                         font=utils.LABEL_FONT,
                         text_color=utils.COLOR_TEXT_PRIMARY, # Use primary text color
                         anchor="w")
    # Padding is handled by the parent row's configuration in phisher_ai_gui
    title.grid(row=0, column=0, sticky="ew", padx=0, pady=(0, 10)) # Add bottom padding

    # --- Content Area ---
    if not flagged_items:
        no_items_label = ctk.CTkLabel(parent_frame, text="No specific threats identified.",
                                      text_color=utils.COLOR_TEXT_SECONDARY, # Use secondary text color
                                      font=utils.INFO_FONT, anchor="center") # Center align
        # Grid to fill the space below title
        no_items_label.grid(row=1, column=0, sticky="nsew", padx=0, pady=10)
        return

    # Frame to hold the list items (Not scrollable for now, matching spec image)
    items_frame = ctk.CTkFrame(parent_frame, fg_color="transparent")
    items_frame.grid(row=1, column=0, sticky="new", padx=0, pady=0) # Stick to top-left-right
    items_frame.grid_columnconfigure(1, weight=1) # Allow text label to expand

    # Icons based on spec image and common reasons
    icons = {
        "Urgency Detected": "⚠️", # Clock icon might be better if available
        "Contains URL": "🔗",
        "Generic Greeting": "🏷️",
        "Password Mentioned": "🔑",
        "Account Information Request": "👤",
        "Verification prompt": "🔒",
        "Password reset": "🔐",
        "Clickbait Link": "🖱️",
        "Account Threat": "🚫",
        "Security Alert": "🛡️",
        "Prize/Lottery Scam": "💰",
        "Fake Invoice/Payment": "🧾",
        "Suspicious Price/Offer": "💰",
        "Too-good-to-be-true Job Offer": "💼",
        "Recruitment Lure": "🧲",
        "Time pressure tactic": "⏳",
        "Phone Call Request": "📞",
        "Sensitive Info Request": "👤",
        "Suspicious Job Offer": "💼"
        # Add more mappings as needed based on SUSPICIOUS_PATTERNS labels
    }

    # Add items to the frame
    for i, (item_text, reason) in enumerate(flagged_items):
         icon = icons.get(reason, "•") # Get icon or default bullet
         # Create a frame for each item row
         item_row_frame = ctk.CTkFrame(items_frame, fg_color="transparent")
         item_row_frame.grid(row=i, column=0, columnspan=2, sticky="ew", pady=4) # Vertical padding between items
         # Icon Label
         ctk.CTkLabel(item_row_frame, text=icon, font=utils.INFO_FONT, width=20, text_color=utils.COLOR_TEXT_SECONDARY).grid(row=0, column=0, sticky="w", padx=(0, 8)) # Padding after icon
         # Text Label (using BODY_FONT for slightly larger text)
         ctk.CTkLabel(item_row_frame, text=item_text, font=utils.BODY_FONT, text_color=utils.COLOR_TEXT_PRIMARY, anchor="w", justify="left").grid(row=0, column=1, sticky="ew")

