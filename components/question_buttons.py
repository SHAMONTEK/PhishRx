# components/question_buttons.py
import customtkinter as ctk

try:
    import utils # Use the centralized utils module
except ImportError:
    print("Error: Unable to import 'utils' in question_buttons.py.")
    # Fallback mock
    class MockUtils:
        SMALL_BUTTON_FONT = ("Arial", 11, "bold")
        COLOR_BUTTON_SECONDARY_FG = "#2F363D"
        COLOR_BUTTON_SECONDARY_HOVER = "#484F58"
        COLOR_BUTTON_SECONDARY_TEXT = "#E6EDF3"
        COLOR_BORDER = "#2F363D"
    utils = MockUtils()

def create_smart_question_buttons(parent_frame, button_click_callback, window_width):
    """
    Creates and returns the frame containing the smart question buttons,
    styled according to the dark UI specification.

    Args:
        parent_frame: The frame within the dashboard where the button container should be placed.
        button_click_callback: The function to call when a button is clicked.
        window_width: The current width of the main window (unused here but kept for signature).

    Returns:
        Tuple: (button_container_frame, list_of_button_widgets)
    """
    # Main frame for the button row - this is the frame that gets gridded by the caller
    button_container_frame = ctk.CTkFrame(parent_frame, fg_color="transparent")
    button_container_frame.grid_columnconfigure(0, weight=1) # Allow inner frame to center

    # Inner frame to group buttons, prevents them stretching full width
    inner_button_frame = ctk.CTkFrame(button_container_frame, fg_color="transparent")
    inner_button_frame.grid(row=0, column=0, pady=0, sticky="") # Centered

    buttons = []
    # Questions from the spec image
    questions_config = [
        {"text": "Why flagged?", "query": "Explain why this message was flagged."},
        {"text": "Is safe?", "query": "Based on the analysis, is it safe to interact with this message?"},
        {"text": "Next steps", "query": "What are the recommended next steps?"}
    ]

    for i, btn_info in enumerate(questions_config):
         # Use secondary button colors and styling from utils
         btn = ctk.CTkButton(
             inner_button_frame, # Add buttons to the inner frame
             text=btn_info["text"],
             command=lambda q=btn_info["query"]: button_click_callback(q), # Send the full query
             font=utils.SMALL_BUTTON_FONT, # Use slightly smaller bold font
             fg_color=utils.COLOR_BUTTON_SECONDARY_FG,
             hover_color=utils.COLOR_BUTTON_SECONDARY_HOVER,
             text_color=utils.COLOR_BUTTON_SECONDARY_TEXT,
             height=35, # Button height
             corner_radius=8, # Rounded corners
             width=120, # Adjust width as needed
             border_width=1, # Subtle border
             border_color=utils.COLOR_BORDER
         )
         btn.grid(row=0, column=i, padx=6, pady=5) # Adjust padding
         buttons.append(btn)

    # Return the container frame AND the list of buttons
    return button_container_frame, buttons
