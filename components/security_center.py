# components/security_center.py
import customtkinter as ctk
from tkinter import ttk # Use ttk for Treeview
import tkinter as tk # For basic Tk stuff and messagebox
from tkinter import messagebox # For delete confirmation
import os # Needed for os.path.basename

try:
    import utils # Use the centralized utils module
except ImportError:
    print("Error: Unable to import 'utils' in security_center.py.")
    # Fallback mock
    class MockUtils: # Define fallback class if utils import fails
        TITLE_FONT = ("Arial", 20, "bold")
        TREEVIEW_FONT = ("Arial", 11)
        TREEVIEW_HEAD_FONT = ("Arial", 12, "bold")
        SMALL_BUTTON_FONT = ("Arial", 11, "bold")
        BUTTON_FONT = ("Arial", 14, "bold")
        INFO_FONT = ("Arial", 12)
        # Add fallback colors (dark mode)
        COLOR_CARD = "#22272E"
        COLOR_BORDER = "#2F363D"
        COLOR_BACKGROUND = "#1B1F23"
        COLOR_TEXT_PRIMARY = "#E6EDF3"
        COLOR_TEXT_SECONDARY = "#8B949E"
        COLOR_BUTTON_SECONDARY_FG = "#2F363D"
        COLOR_BUTTON_SECONDARY_HOVER = "#484F58"
        COLOR_BUTTON_SECONDARY_TEXT = "#E6EDF3"
        COLOR_TEXT_ACCENT = "#007AFF" # Blue accent
        COLOR_TEXT_ERROR = "#F04A4A" # Red error
        COLOR_BUTTON_PRIMARY_TEXT = "#FFFFFF" # White text
    utils = MockUtils()

try:
    # Import the REAL scan_logger component now
    from components import scan_logger
except ImportError:
    print("Error: Unable to import 'scan_logger' component in security_center.py.")
    # Mock scan_logger if it's not available
    class MockScanLogger: # Define fallback class if scan_logger import fails
        @staticmethod
        def load_scan_history():
            print("MockScanLogger: Loading sample history.")
            return [
                {'Timestamp': '2025-04-23 19:00:00', 'Severity': 'High', 'Reasons': 'Urgency|Contains URL', 'ImagePath': 'screenshot1.png', 'OCRText': 'Urgent action needed...'},
                {'Timestamp': '2025-04-23 18:30:00', 'Severity': 'Medium', 'Reasons': 'Verification prompt', 'ImagePath': 'screenshot2.png', 'OCRText': 'Verify your account...'},
                {'Timestamp': '2025-04-22 10:00:00', 'Severity': 'Safe', 'Reasons': '', 'ImagePath': 'screenshot3.png', 'OCRText': 'Hello there...'}
            ]
        @staticmethod
        def delete_scan_history_item(timestamp):
             print(f"MockScanLogger: Deleting item with timestamp {timestamp}")
             return True # Simulate success
    scan_logger = MockScanLogger()

# --- Helper Function to Populate Treeview ---
def _populate_scan_history_tree(treeview_widget):
    """Internal helper function to clear and populate the Treeview."""
    # Clear existing items
    for item in treeview_widget.get_children():
        treeview_widget.delete(item)
    # Load data using the imported scan_logger
    history_data = scan_logger.load_scan_history() # Calls the function from scan_logger.py
    history_data.reverse() # Show most recent first
    for i, record in enumerate(history_data):
        # Use alternating row tags for styling
        tag = 'evenrow' if i % 2 == 0 else 'oddrow'
        # Extract data safely using .get()
        timestamp = record.get('Timestamp', 'N/A')
        severity = record.get('Severity', 'N/A')
        reasons = record.get('Reasons', 'N/A').replace('|', ', ') # Format reasons
        image_path = record.get('ImagePath', 'N/A')
        # Insert data into the treeview, using timestamp as unique ID (iid)
        treeview_widget.insert("", "end", iid=timestamp, # Use timestamp as unique ID
                               values=(timestamp, severity, reasons, os.path.basename(image_path)), # Show only filename
                               tags=(tag,))
    # Configure alternating row colors using theme colors from utils
    treeview_widget.tag_configure('evenrow', background=utils.COLOR_CARD)
    treeview_widget.tag_configure('oddrow', background=utils.COLOR_BACKGROUND) # Use main bg for contrast
    treeview_widget.tag_configure('evenrow', foreground=utils.COLOR_TEXT_PRIMARY)
    treeview_widget.tag_configure('oddrow', foreground=utils.COLOR_TEXT_PRIMARY)


# --- Helper Function for Deleting Items ---
def _delete_selected_scan(treeview_widget, delete_button):
    """Deletes the selected item(s) from the Treeview and data source."""
    selected_items = treeview_widget.selection()
    if not selected_items:
        print("Delete Aborted: No item selected.")
        messagebox.showinfo("Delete Scan", "No scan selected to delete.")
        return

    # Assuming the item ID (iid) is the timestamp used during insertion
    timestamps_to_delete = [iid for iid in selected_items]

    # Confirmation dialog
    num_items = len(timestamps_to_delete)
    item_str = "item" if num_items == 1 else "items"
    if not messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete the selected {num_items} scan {item_str}?"):
        return

    deleted_count = 0
    failed_timestamps = []
    for timestamp in timestamps_to_delete:
        print(f"Attempting to delete scan with timestamp: {timestamp}")
        # Call the delete function from the imported scan_logger
        success = scan_logger.delete_scan_history_item(timestamp)
        if success:
            try:
                 if treeview_widget.exists(timestamp): # Check if item still exists in tree
                      treeview_widget.delete(timestamp)
                      deleted_count += 1
                 else:
                      print(f"Warning: Item {timestamp} already removed from Treeview.")
            except tk.TclError as e:
                 print(f"Error deleting item {timestamp} from Treeview: {e}")
                 failed_timestamps.append(timestamp) # Add to failed list if tree deletion fails
        else:
            print(f"Failed to delete scan record for timestamp: {timestamp}")
            failed_timestamps.append(timestamp) # Add to failed list if backend delete fails

    print(f"Deleted {deleted_count} item(s).")
    if failed_timestamps:
         messagebox.showerror("Delete Error", f"Failed to delete records for timestamps:\n{', '.join(failed_timestamps)}")
    elif deleted_count > 0:
         messagebox.showinfo("Delete Success", f"Successfully deleted {deleted_count} scan(s).")

    # Disable delete button again after deletion attempt
    delete_button.configure(state="disabled")


# --- Main Function to Create the Security Center Tab ---
def create_security_center_tab(parent_frame):
    """Creates the entire Security Center tab content using the dark theme."""
    # Main container frame for this tab
    security_center_frame = ctk.CTkFrame(parent_frame,
                                         fg_color=utils.COLOR_BACKGROUND, # Use main background
                                         corner_radius=0) # No radius for the main container
    security_center_frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
    security_center_frame.grid_columnconfigure(0, weight=1)
    security_center_frame.grid_rowconfigure(1, weight=1) # Treeview row expands

    # --- Title ---
    security_label = ctk.CTkLabel(security_center_frame, text="🛡️ Scan History",
                                 font=utils.TITLE_FONT,
                                 text_color=utils.COLOR_TEXT_PRIMARY,
                                 anchor="w")
    security_label.grid(row=0, column=0, pady=(15, 10), padx=15, sticky="ew")

    # --- Treeview Frame (with card styling) ---
    tree_container_frame = ctk.CTkFrame(security_center_frame,
                                         fg_color=utils.COLOR_CARD,
                                         border_color=utils.COLOR_BORDER,
                                         border_width=1,
                                         corner_radius=8)
    tree_container_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=0)
    tree_container_frame.grid_rowconfigure(0, weight=1)
    tree_container_frame.grid_columnconfigure(0, weight=1)

    # --- Style Treeview using Theme Colors ---
    style = ttk.Style()
    style.theme_use("default") # Start with default and override

    # Configure base Treeview style
    style.configure("Treeview",
                    background=utils.COLOR_CARD, # Background of rows
                    foreground=utils.COLOR_TEXT_PRIMARY, # Text color
                    fieldbackground=utils.COLOR_CARD, # Background of the data area
                    borderwidth=0, # No internal border
                    rowheight=28, # Increase row height slightly
                    font=utils.TREEVIEW_FONT) # Use font from utils
    # Remove borders from Treeview itself
    style.layout("Treeview", [('Treeview.treearea', {'sticky': 'nswe'})]) # Remove borders

    # Configure selected item style
    style.map('Treeview',
              background=[('selected', utils.COLOR_TEXT_ACCENT)], # Blue background for selection
              foreground=[('selected', utils.COLOR_BUTTON_PRIMARY_TEXT)]) # White text for selection

    # Configure Heading style
    style.configure("Treeview.Heading",
                    background=utils.COLOR_BUTTON_SECONDARY_FG, # Darker gray background
                    foreground=utils.COLOR_BUTTON_SECONDARY_TEXT, # Light text
                    font=utils.TREEVIEW_HEAD_FONT, # Use heading font from utils
                    relief="flat", # Flat look
                    padding=(10, 5)) # Add padding to header text
    style.map("Treeview.Heading",
              background=[('active', utils.COLOR_BUTTON_SECONDARY_HOVER)]) # Slightly lighter gray on hover

    # Define Columns & Treeview Widget
    columns = ("timestamp", "severity", "reasons", "image_path")
    history_tree = ttk.Treeview(tree_container_frame, columns=columns, show="headings", style="Treeview", height=10) # Set initial height
    history_tree.heading("timestamp", text="Timestamp", anchor="w")
    history_tree.heading("severity", text="Severity", anchor="w")
    history_tree.heading("reasons", text="Reasons", anchor="w")
    history_tree.heading("image_path", text="Image File", anchor="w")
    history_tree.column("timestamp", anchor="w", width=160, stretch=False)
    history_tree.column("severity", anchor="center", width=100, stretch=False)
    history_tree.column("reasons", anchor="w", width=250) # Give more space for reasons
    history_tree.column("image_path", anchor="w", width=180)
    history_tree.grid(row=0, column=0, sticky="nsew", padx=(10,0), pady=10) # Padding, leave space for scrollbar

    # Add Scrollbar (Use CTkScrollbar for consistency)
    tree_scrollbar = ctk.CTkScrollbar(tree_container_frame, command=history_tree.yview,
                                       button_color=utils.COLOR_BUTTON_SECONDARY_FG,
                                       button_hover_color=utils.COLOR_BUTTON_SECONDARY_HOVER)
    history_tree.configure(yscrollcommand=tree_scrollbar.set)
    tree_scrollbar.grid(row=0, column=1, sticky="ns", padx=(0,10), pady=10) # Padding for scrollbar

    # Load initial data into Treeview using the helper
    _populate_scan_history_tree(history_tree)

    # --- Action Buttons Frame ---
    actions_frame = ctk.CTkFrame(security_center_frame, fg_color="transparent")
    actions_frame.grid(row=2, column=0, pady=(10, 15), padx=15, sticky="ew")
    # Configure columns to push buttons left and leave space on right
    actions_frame.grid_columnconfigure(0, weight=0) # Refresh
    actions_frame.grid_columnconfigure(1, weight=0) # Delete
    actions_frame.grid_columnconfigure(2, weight=0) # Re-analyze
    actions_frame.grid_columnconfigure(3, weight=1) # Spacer

    # Refresh Button
    refresh_button = ctk.CTkButton(actions_frame, text="Refresh",
                                   command=lambda: _populate_scan_history_tree(history_tree),
                                   width=100, font=utils.SMALL_BUTTON_FONT,
                                   fg_color=utils.COLOR_BUTTON_SECONDARY_FG,
                                   hover_color=utils.COLOR_BUTTON_SECONDARY_HOVER,
                                   text_color=utils.COLOR_BUTTON_SECONDARY_TEXT,
                                   border_width=1, border_color=utils.COLOR_BORDER, corner_radius=6)
    refresh_button.grid(row=0, column=0, padx=(0, 10))

    # Delete Button (Use error color)
    delete_button = ctk.CTkButton(actions_frame, text="Delete Selected",
                                  command=lambda: _delete_selected_scan(history_tree, delete_button), # Pass button to lambda
                                  width=120, state="disabled",
                                  font=utils.SMALL_BUTTON_FONT,
                                  fg_color=utils.COLOR_TEXT_ERROR, # Use error red
                                  hover_color="#b91c1c", # Darker red for hover
                                  text_color=utils.COLOR_BUTTON_PRIMARY_TEXT, corner_radius=6)
    delete_button.grid(row=0, column=1, padx=(0, 10))

    # Re-analyze Button (Placeholder - functionality TBD)
    # You would need to get the image path from the selected item and re-run the analysis
    reanalyze_button = ctk.CTkButton(actions_frame, text="Re-Analyze",
                                     width=100, state="disabled", # Disabled for now
                                     font=utils.SMALL_BUTTON_FONT,
                                     fg_color=utils.COLOR_BUTTON_SECONDARY_FG,
                                     hover_color=utils.COLOR_BUTTON_SECONDARY_HOVER,
                                     text_color=utils.COLOR_BUTTON_SECONDARY_TEXT,
                                     border_width=1, border_color=utils.COLOR_BORDER, corner_radius=6)
    reanalyze_button.grid(row=0, column=2)

    # Enable/disable Delete/Re-analyze button based on selection
    def on_tree_select(event):
        selected_items = history_tree.selection()
        if selected_items:
            delete_button.configure(state="normal")
            reanalyze_button.configure(state="normal") # Enable re-analyze too
        else:
            delete_button.configure(state="disabled")
            reanalyze_button.configure(state="disabled")

    history_tree.bind("<<TreeviewSelect>>", on_tree_select)


    return security_center_frame
