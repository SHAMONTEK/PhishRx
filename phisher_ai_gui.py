# phisher_ai_gui.py # <-- Renamed file comment
import customtkinter as ctk
from datetime import datetime
import os
import sys
import re
import threading
import queue
import tkinter # For PhotoImage and TclError

# --- Import Utilities ---
# Import the external utils module
try:
    import utils
except ImportError:
    print("❌ FATAL ERROR: utils.py not found. Please ensure it's in the same directory.")
    sys.exit(1)
except Exception as e:
     print(f"❌ FATAL ERROR: Failed to import utils.py: {e}")
     sys.exit(1)


# --- Import Components ---
# Import actual components now, assuming they exist in a 'components' directory
try:
    from components import ai_handler
    from components import scan_logger
    from components import question_buttons
    from components import threat_breakdown
    from components import security_center
except ImportError as e:
    print(f"❌ ERROR importing components: {e}")
    print("Ensure 'components' directory exists and contains required .py files.")
    # Fallback to placeholders if import fails, allowing basic UI to run
    # Define simple placeholder classes if components fail to import
    class MockAIHandler:
        @staticmethod
        def get_ai_response(user_input, reasons, severity, ocr_text):
            print(f"MockAIHandler: Received query '{user_input}'")
            return f"Mock AI Response for '{user_input}' (Severity: {severity})"
    class MockScanLogger:
        @staticmethod
        def save_scan_to_csv(timestamp, severity, reasons, image_path, ocr_text):
            print(f"MockScanLogger: Save scan - {timestamp}, {severity}")
        @staticmethod
        def load_scan_history(): return []
        @staticmethod
        def delete_scan_history_item(timestamp): return True
    class MockQuestionButtons:
        @staticmethod
        def create_smart_question_buttons(parent_frame, button_click_callback, window_width):
             print("MockQuestionButtons: Creating buttons")
             button_frame = ctk.CTkFrame(parent_frame, fg_color="transparent")
             btn = ctk.CTkButton(button_frame, text="Mock Button")
             btn.pack()
             return button_frame, [btn] # Return frame and list
    class MockThreatBreakdown:
        @staticmethod
        def create_threat_breakdown_section(parent_frame, flagged_items):
             print(f"MockThreatBreakdown: Displaying {len(flagged_items)} items")
             label_text = "Threat Breakdown (Mock)"
             if flagged_items:
                  label_text += f"\n- {flagged_items[0][1]}" # Show first reason
             ctk.CTkLabel(parent_frame, text=label_text).pack()
    class MockSecurityCenter:
         @staticmethod
         def create_security_center_tab(parent_frame):
              print("MockSecurityCenter: Creating tab")
              frame = ctk.CTkFrame(parent_frame, fg_color=utils.COLOR_CARD)
              ctk.CTkLabel(frame, text="Security Center (Mock)").pack()
              return frame

    ai_handler = MockAIHandler
    scan_logger = MockScanLogger
    question_buttons = MockQuestionButtons
    threat_breakdown = MockThreatBreakdown
    security_center = MockSecurityCenter


# --- Main Application Class ---
class PhishRxApp(ctk.CTk): # <-- Renamed class

    def __init__(self, severity, reasons, image_path):
        super().__init__()

        # Store initial data
        self.severity = severity
        # Note: 'reasons' passed here might be initial placeholder.
        # Actual reasons are determined by find_suspicious_text below.
        self.initial_reasons_placeholder = reasons
        self.image_path = image_path

        # Initialize state variables
        self.ocr_text = ""
        self.flagged_items = [] # Store results from utils.find_suspicious_text -> list of (phrase, reason_label)
        self.reasons_for_ai = [] # Store just the reason labels for the AI prompt
        self.smart_buttons_widgets = []
        self.is_loading = False
        self.response_queue = queue.Queue()
        self.logo_image = None # CTkImage for UI logo
        self.last_ai_response = "" # Potentially store fuller AI response
        self.last_ai_summary = "" # Store summary shown in label
        self.progress_bar = None
        self.ai_summary_label = None
        self.dashboard_frame = None # Reference to the main dashboard frame
        self.security_center_frame = None # Reference to the security center frame

        # --- Basic Window Setup ---
        self.title("PhishRx") # <-- Renamed window title
        # --- Set Application Icon ---
        try:
            # Consider renaming icon file too, e.g., phishrx_icon.png
            icon_path = "phishrx_icon.png" # <-- Potentially rename icon file
            if not os.path.exists(icon_path):
                 icon_path = "phisher_icon.png" # Fallback to old name if new one doesn't exist yet

            if os.path.exists(icon_path):
                 # Use tkinter.PhotoImage for the window icon (taskbar/dock)
                 icon_image = tkinter.PhotoImage(file=icon_path)
                 self.iconphoto(True, icon_image)
                 print(f"✅ Successfully set application icon from: {icon_path}")
                 # Load CTkImage for use in the UI later using utils function
                 self.logo_image = utils.load_ctk_image(icon_path, size=(32, 32))
                 if not self.logo_image:
                      print("⚠️ Logo image not loaded for UI (PIL unavailable or error).")
            else:
                 print(f"⚠️ Warning: Icon file not found at '{icon_path}' or fallback. Using default icon.")
        except Exception as e:
            print(f"⚠️ Warning: Could not set application icon or load logo. Error: {e}")

        # --- Window Geometry ---
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        self.win_width = 800
        self.win_height = 750 # Adjusted height
        x = max(0, (screen_width // 2) - (self.win_width // 2))
        y = max(0, (screen_height // 2) - (self.win_height // 2))
        self.geometry(f"{self.win_width}x{self.win_height}+{x}+{y}")
        self.minsize(750, 700) # Adjusted min size

        # --- Apply Dark Theme ---
        ctk.set_appearance_mode("dark") # Set dark mode
        self.configure(fg_color=utils.COLOR_BACKGROUND)

        # --- Perform OCR & Initial Analysis ---
        # Ensure image_path exists before proceeding
        if not os.path.exists(self.image_path):
             print(f"❌ ERROR: Screenshot image path does not exist: {self.image_path}")
             # Display error in UI instead of just printing
             self.ocr_text = f"Error: Screenshot file not found at\n{self.image_path}"
             self.flagged_items = []
             self.severity = "Error" # Set severity to Error
        else:
             self.ocr_text = utils.perform_ocr(self.image_path)
             # Use the find_suspicious_text function from utils
             self.flagged_items = utils.find_suspicious_text(self.ocr_text)
             # Extract just the reasons/labels for the AI prompt and display
             self.reasons_for_ai = [label for _, label in self.flagged_items]
             # Optional: Update severity based on OCR/flagged items if initial was "Unknown"
             if self.severity == "Unknown":
                  if len(self.flagged_items) >= 3: self.severity = "High"
                  elif len(self.flagged_items) > 0: self.severity = "Medium"
                  else: self.severity = "Low" # Or "Safe" if OCR text is very short/benign

        # --- Log Scan ---
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Use the extracted reasons for logging
        scan_logger.save_scan_to_csv(timestamp, self.severity, self.reasons_for_ai, self.image_path, self.ocr_text)

        # --- Main Structure ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1) # Make content area expand

        # --- Top Navigation Frame ---
        self.nav_frame = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self.nav_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(10, 5))
        self.nav_frame.grid_columnconfigure(0, weight=0) # Logo
        self.nav_frame.grid_columnconfigure(1, weight=1) # Title
        self.nav_frame.grid_columnconfigure(2, weight=0) # Buttons

        # Logo
        if self.logo_image and isinstance(self.logo_image, ctk.CTkImage): # Check if it's a CTkImage
            logo_label = ctk.CTkLabel(self.nav_frame, image=self.logo_image, text="")
            logo_label.grid(row=0, column=0, sticky="w", padx=(0, 10))
        else:
             # Fallback text/placeholder if image loading failed
             ctk.CTkLabel(self.nav_frame, text="Rx", font=("Arial", 24, "bold"), text_color=utils.COLOR_TEXT_ACCENT).grid(row=0, column=0, sticky="w", padx=(0, 10)) # Changed placeholder

        # Title
        self.title_label = ctk.CTkLabel(self.nav_frame, text="PhishRx", font=utils.TITLE_FONT, text_color=utils.COLOR_TEXT_ACCENT) # <-- Renamed Title Label
        self.title_label.grid(row=0, column=1, sticky="w", padx=5)

        # Tab Buttons
        self.tab_buttons_frame = ctk.CTkFrame(self.nav_frame, fg_color="transparent")
        self.tab_buttons_frame.grid(row=0, column=2, sticky="e")
        self.dashboard_button = ctk.CTkButton(self.tab_buttons_frame, text="Dashboard", command=self.show_dashboard_frame,
                                              font=utils.BUTTON_FONT, fg_color="transparent", hover=False,
                                              text_color=utils.COLOR_TEXT_SECONDARY, width=100)
        self.dashboard_button.grid(row=0, column=0, padx=(0, 10))
        self.security_center_button = ctk.CTkButton(self.tab_buttons_frame, text="Security", command=self.show_security_center_frame,
                                                   font=utils.BUTTON_FONT, fg_color="transparent", hover=False,
                                                   text_color=utils.COLOR_TEXT_SECONDARY, width=100)
        self.security_center_button.grid(row=0, column=1)

        # --- Content Frame ---
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(10, 20))
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)

        # --- Build Initial View ---
        self.show_dashboard_frame() # Show dashboard by default

        # --- Start checking the queue ---
        self.after(100, self._check_response_queue)

        # --- Force focus on startup ---
        self.after(200, lambda: utils.force_window_focus(self)) # Delay focus slightly


    def clear_content_frame(self):
        """Removes all widgets from the content frame."""
        # Safely stop and forget progress bar IF it exists AND is still a valid widget
        if hasattr(self, 'progress_bar') and self.progress_bar is not None:
            try:
                if self.progress_bar.winfo_exists():
                    if self.progress_bar.winfo_manager() == 'grid':
                        self.progress_bar.stop()
                        self.progress_bar.grid_forget()
            except tkinter.TclError as e:
                print(f"Ignoring TclError during progress bar cleanup: {e}")
            except Exception as e:
                print(f"Error clearing progress bar: {e}")

        # Destroy all direct children of content_frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # Reset frame references AFTER destroying children
        self.dashboard_frame = None
        self.security_center_frame = None
        # Reset references to widgets within the dashboard frame
        self.progress_bar = None
        self.ai_summary_label = None
        self.smart_buttons_widgets = [] # Clear button references


    def create_dashboard_frame(self):
        """Creates the dashboard content frame based on the dark UI spec."""
        # Main frame for the dashboard view
        self.dashboard_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.dashboard_frame.grid(row=0, column=0, sticky="nsew")
        self.dashboard_frame.grid_columnconfigure(0, weight=1) # Single column layout

        # Configure rows based on the dark UI spec layout
        self.dashboard_frame.grid_rowconfigure(0, weight=0) # Top Body Frame (Screenshot/Breakdown + Severity)
        self.dashboard_frame.grid_rowconfigure(1, weight=0) # AI Summary Label
        self.dashboard_frame.grid_rowconfigure(2, weight=0) # Smart Buttons Row
        self.dashboard_frame.grid_rowconfigure(3, weight=0) # User Input Row
        self.dashboard_frame.grid_rowconfigure(4, weight=0) # Progress bar row (initially empty)
        self.dashboard_frame.grid_rowconfigure(5, weight=1) # Spacer row pushes content up


        # --- 1. Top Body Frame (Groups Screenshot/Breakdown and Severity Meter) ---
        top_body_frame = ctk.CTkFrame(self.dashboard_frame, fg_color=utils.COLOR_CARD, corner_radius=8, border_width=1, border_color=utils.COLOR_BORDER) # Use card color
        top_body_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20), padx=10) # Grid this frame first
        top_body_frame.grid_columnconfigure(0, weight=1) # Allow content to span width

        # --- 1a. Screenshot + Threat Breakdown Row (Inside top_body_frame) ---
        screenshot_breakdown_row = ctk.CTkFrame(top_body_frame, fg_color="transparent")
        screenshot_breakdown_row.grid(row=0, column=0, sticky="ew", pady=(15, 15), padx=15) # Add internal padding
        screenshot_breakdown_row.grid_columnconfigure(0, weight=3, minsize=250) # Screenshot column (adjust weight/min)
        screenshot_breakdown_row.grid_columnconfigure(1, weight=4) # Threat Breakdown column
        screenshot_breakdown_row.grid_rowconfigure(0, weight=0) # Let content define height

        # Screenshot Display
        img_card_frame = ctk.CTkFrame(screenshot_breakdown_row, fg_color=utils.COLOR_BACKGROUND, border_color=utils.COLOR_BORDER, border_width=1, corner_radius=6) # Slightly different bg
        img_card_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 15)) # Stick to all sides, add right padding
        img_card_frame.grid_rowconfigure(0, weight=1)
        img_card_frame.grid_columnconfigure(0, weight=1)

        try:
            # Load image using the function from utils.py
            screenshot_image = utils.load_ctk_image(self.image_path, size=(280, 180)) # Adjusted size
            if screenshot_image and isinstance(screenshot_image, ctk.CTkImage): # Check if CTkImage was returned
                img_label = ctk.CTkLabel(img_card_frame, image=screenshot_image, text="")
                img_label.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
            else: # Handle case where load_ctk_image returned None
                 print(f"Warning: Screenshot CTkImage not loaded successfully for {self.image_path}. Displaying placeholder text.")
                 # Display error/placeholder text if image failed to load
                 error_text = f"[Image Load Failed]\n{os.path.basename(self.image_path)}" if os.path.exists(self.image_path) else "[Image Not Found]"
                 error_label = ctk.CTkLabel(img_card_frame, text=error_text, text_color=utils.COLOR_TEXT_SECONDARY, font=utils.INFO_FONT)
                 error_label.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        except Exception as e:
             print(f"Error displaying screenshot: {e}")
             error_label = ctk.CTkLabel(img_card_frame, text=f"[Display Error]\n{os.path.basename(self.image_path)}", text_color=utils.COLOR_TEXT_ERROR, font=utils.INFO_FONT)
             error_label.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Threat Breakdown
        # Create a frame to pass to the component function
        breakdown_content_frame = ctk.CTkFrame(screenshot_breakdown_row, fg_color="transparent")
        breakdown_content_frame.grid(row=0, column=1, sticky="nsew", padx=(15, 0)) # Add left padding
        # Call the component function from threat_breakdown module
        threat_breakdown.create_threat_breakdown_section(
            parent_frame=breakdown_content_frame, # Pass the content frame
            flagged_items=self.flagged_items # Use the data found during init
        )


        # --- 1b. Severity / Reasons / Recommendation Row (Inside top_body_frame) ---
        info_frame = ctk.CTkFrame(top_body_frame, fg_color="transparent") # Transparent bg, part of the card
        info_frame.grid(row=1, column=0, sticky="ew", padx=15, pady=(0, 15)) # Grid below the row above
        info_frame.grid_columnconfigure(0, weight=0) # Severity label fixed
        info_frame.grid_columnconfigure(1, weight=1) # Meter expands

        # Severity Meter and Text
        severity_text = f"Severity: {self.severity}"
        sev_lower = self.severity.lower()
        meter_value, meter_color = 0.0, utils.COLOR_TEXT_SECONDARY
        if sev_lower == 'high': meter_value, meter_color = 0.95, utils.COLOR_SEVERITY_HIGH
        elif sev_lower == 'medium': meter_value, meter_color = 0.6, utils.COLOR_SEVERITY_MEDIUM
        elif sev_lower == 'low': meter_value, meter_color = 0.3, utils.COLOR_SEVERITY_LOW
        elif sev_lower == 'safe' or sev_lower == 'none': meter_value, meter_color = 0.05, utils.COLOR_SEVERITY_SAFE
        else: meter_value, meter_color = 0.1, utils.COLOR_TEXT_SECONDARY # Handle "Unknown" or "Error"

        ctk.CTkLabel(info_frame, text=severity_text, text_color=meter_color, font=utils.LABEL_FONT, anchor="w").grid(row=0, column=0, sticky="w", padx=(0, 10), pady=(0, 5))
        severity_meter = ctk.CTkProgressBar(info_frame, orientation='horizontal', determinate_speed=1, mode='determinate', height=8, corner_radius=4, border_width=0, fg_color=utils.COLOR_BORDER, progress_color=meter_color) # Thinner bar
        severity_meter.set(meter_value)
        severity_meter.grid(row=0, column=1, sticky="ew", padx=(0, 0), pady=(0, 5))

        # Reasons Text (using the reasons extracted from flagged_items)
        reasons_display_str = f"Reasons: {', '.join(self.reasons_for_ai) if self.reasons_for_ai else 'None detected'}"
        ctk.CTkLabel(info_frame, text=reasons_display_str, wraplength=self.win_width - 80, font=utils.INFO_FONT, text_color=utils.COLOR_TEXT_SECONDARY, anchor="w", justify="left").grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 5))

        # Recommendation Text
        rec_text = ""
        rec_text_color = utils.COLOR_TEXT_PRIMARY # Default
        rec_icon = "" # No default icon needed? Spec shows red icon for high
        if sev_lower == 'high': rec_text, rec_text_color, rec_icon = "Recommendation: Delete this message immediately.", utils.COLOR_SEVERITY_HIGH, "⚠️ "
        elif sev_lower == 'medium': rec_text, rec_text_color, rec_icon = "Recommendation: Proceed with extreme caution.", utils.COLOR_SEVERITY_MEDIUM, "⚠️ "
        elif sev_lower == 'low': rec_text, rec_text_color = "Recommendation: Review carefully before proceeding.", utils.COLOR_TEXT_SECONDARY # Subtle for low
        elif sev_lower == 'safe' or sev_lower == 'none': rec_text, rec_text_color = "Recommendation: Appears safe, but remain vigilant.", utils.COLOR_SEVERITY_SAFE

        if rec_text:
            recommendation_label = ctk.CTkLabel(info_frame,
                                                text=f"{rec_icon}{rec_text}", # Prepend icon if exists
                                                font=utils.INFO_FONT,
                                                text_color=rec_text_color,
                                                wraplength=self.win_width - 80,
                                                anchor="w", justify="left")
            recommendation_label.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 0)) # No bottom padding


        # --- 2. AI Interaction Area Label (Replaces Chatbox) ---
        ai_area_frame = ctk.CTkFrame(self.dashboard_frame, fg_color=utils.COLOR_CARD, corner_radius=8, border_width=1, border_color=utils.COLOR_BORDER)
        ai_area_frame.grid(row=1, column=0, pady=(0, 15), sticky="ew", padx=10)
        ai_area_frame.grid_columnconfigure(0, weight=1)

        self.ai_summary_label = ctk.CTkLabel(ai_area_frame, text="Initializing AI analysis...", font=utils.BODY_FONT, # Use Body font
                                             text_color=utils.COLOR_TEXT_SECONDARY, anchor="w", justify="left",
                                             wraplength=self.win_width - 80) # Adjust wraplength
        self.ai_summary_label.grid(row=0, column=0, sticky="ew", padx=15, pady=15)
        # Trigger initial AI response to populate this label only if OCR was successful
        if not self.ocr_text.startswith("Error:"):
             self.after(100, lambda: self.on_ask("Initial analysis based on OCR text")) # Ask for initial summary
        else:
             # If OCR failed, update label immediately
             self.ai_summary_label.configure(text=f"Cannot analyze: {self.ocr_text}", text_color=utils.COLOR_TEXT_ERROR)


        # --- 3. Smart Question Buttons ---
        # Call the component function from question_buttons module
        returned_value = question_buttons.create_smart_question_buttons(
            parent_frame=self.dashboard_frame, # Pass the main dashboard frame
            button_click_callback=self.on_smart_button_click,
            window_width=self.win_width
        )
        # The component now returns the frame and the buttons
        if isinstance(returned_value, tuple) and len(returned_value) == 2:
            smart_buttons_frame, self.smart_buttons_widgets = returned_value
            # Grid the returned frame below AI summary
            smart_buttons_frame.grid(row=2, column=0, pady=(0, 20), padx=10, sticky="ew")
        else:
            print("Warning: question_buttons.create_smart_question_buttons did not return the expected (frame, buttons) tuple.")
            self.smart_buttons_widgets = []


        # --- 4. User Input & Action Buttons ---
        input_area_frame = ctk.CTkFrame(self.dashboard_frame, fg_color="transparent")
        input_area_frame.grid(row=3, column=0, pady=(0, 10), padx=10, sticky="ew")
        input_area_frame.grid_columnconfigure(1, weight=1) # Make entry expand
        input_area_frame.grid_columnconfigure(0, weight=0) # Copy button fixed
        input_area_frame.grid_columnconfigure(2, weight=0) # Ask button fixed

        # Copy Button (Left)
        self.copy_button = ctk.CTkButton(input_area_frame, text="Copy", command=self._copy_last_response,
                                         font=utils.BUTTON_FONT, width=80, height=40,
                                         fg_color=utils.COLOR_BUTTON_COPY_FG, # Use specific copy colors if needed
                                         hover_color=utils.COLOR_BUTTON_COPY_HOVER,
                                         text_color=utils.COLOR_BUTTON_COPY_TEXT,
                                         border_width=1, border_color=utils.COLOR_BORDER,
                                         corner_radius=8, state="disabled")
        self.copy_button.grid(row=0, column=0, sticky="w", padx=(0, 10))

        # User Input Entry (Center)
        self.user_entry = ctk.CTkEntry(input_area_frame, placeholder_text="Ask about the risk or how to proceed…",
                                       height=40, fg_color=utils.COLOR_CARD, # Use card color for entry bg
                                       text_color=utils.COLOR_TEXT_PRIMARY, font=utils.BODY_FONT, # Use body font
                                       border_color=utils.COLOR_BORDER, border_width=1, corner_radius=8)
        self.user_entry.grid(row=0, column=1, sticky="ew", padx=0)
        self.user_entry.bind("<Return>", self.on_ask)

        # Ask AI Button (Right)
        self.ask_button = ctk.CTkButton(input_area_frame, text="Ask AI", command=self.on_ask,
                                        font=utils.BUTTON_FONT, width=100, height=40,
                                        fg_color=utils.COLOR_BUTTON_PRIMARY_FG,
                                        hover_color=utils.COLOR_BUTTON_PRIMARY_HOVER,
                                        text_color=utils.COLOR_BUTTON_PRIMARY_TEXT,
                                        corner_radius=8)
        self.ask_button.grid(row=0, column=2, sticky="e", padx=(10, 0))

        # Progress Bar (Created but not gridded initially)
        self.progress_bar = ctk.CTkProgressBar(self.dashboard_frame, orientation='horizontal',
                                               mode='indeterminate', height=5, corner_radius=3,
                                               progress_color=utils.COLOR_TEXT_ACCENT)


    # --- Tab Switching Methods ---
    def show_dashboard_frame(self):
        """Clears content frame and shows the dashboard frame."""
        self.clear_content_frame()
        self.create_dashboard_frame() # This now sets up the new dashboard layout
        # Highlight the active tab button (use text color)
        self.dashboard_button.configure(text_color=utils.COLOR_TEXT_PRIMARY) # Active color
        self.security_center_button.configure(text_color=utils.COLOR_TEXT_SECONDARY) # Inactive color

    def show_security_center_frame(self):
        """Clears content frame and shows the security center frame using the component."""
        self.clear_content_frame()
        # Call the component function from security_center module
        self.security_center_frame = security_center.create_security_center_tab(self.content_frame)
        # The component itself should handle its internal gridding.
        # We just need to make sure the content_frame is clear.
        # Highlight the active tab button
        self.dashboard_button.configure(text_color=utils.COLOR_TEXT_SECONDARY) # Inactive color
        self.security_center_button.configure(text_color=utils.COLOR_TEXT_PRIMARY) # Active color

    # --- Event Handlers and AI Interaction ---
    def on_smart_button_click(self, question):
        """Handles clicks on the smart suggestion buttons."""
        if self.is_loading: return
        # Check if user_entry exists before manipulating
        if hasattr(self, 'user_entry') and self.user_entry is not None and self.user_entry.winfo_exists():
             self.user_entry.delete(0, "end")
             self.user_entry.insert(0, question)
             self.on_ask() # Trigger the AI query with the button's question
        else:
             print("Error: Cannot handle smart button click, user entry missing.")


    def _run_ai_in_thread(self, user_input):
        """Runs the AI handler in a separate thread."""
        print("Starting AI request thread...")
        try:
            # Get the summary statement from the AI handler
            # Pass the extracted reasons list to the AI handler
            response_summary = ai_handler.get_ai_response(user_input, self.reasons_for_ai, self.severity, self.ocr_text)
            self.response_queue.put(response_summary) # Put summary in queue
        except Exception as e:
            print(f"Error in AI thread: {e}")
            self.response_queue.put(f"Error: Could not get AI analysis.") # Put error message in queue
        finally:
            print("AI request thread finished.")


    def _check_response_queue(self):
        """Checks the queue for AI responses."""
        try:
            response_summary = self.response_queue.get_nowait()
            print("Found response summary in queue:", response_summary)
            self._handle_ai_response(response_summary)
        except queue.Empty:
            pass # No response yet
        except Exception as e:
            print(f"Error checking response queue: {e}")
        finally:
            # Schedule the next check only if the window still exists
            try:
                 if self.winfo_exists():
                      self.after(100, self._check_response_queue)
            except Exception:
                 pass # Window likely destroyed


    def _handle_ai_response(self, response_summary):
        """Updates the AI summary label after the response is received."""
        print("Handling AI response in main thread...")
        self.last_ai_summary = response_summary # Store the summary
        self.is_loading = False

        # Stop and hide the progress bar safely
        if hasattr(self, 'progress_bar') and self.progress_bar is not None:
             try:
                 if self.progress_bar.winfo_exists():
                     if self.progress_bar.winfo_manager() == 'grid':
                         self.progress_bar.stop()
                         self.progress_bar.grid_forget()
             except tkinter.TclError as e: print(f"Ignoring TclError during progress bar cleanup: {e}")
             except Exception as e: print(f"Error handling progress bar: {e}")

        # Re-enable UI elements safely
        if hasattr(self, 'user_entry') and self.user_entry is not None and self.user_entry.winfo_exists(): self.user_entry.configure(state="normal")
        if hasattr(self, 'ask_button') and self.ask_button is not None and self.ask_button.winfo_exists(): self.ask_button.configure(state="normal")
        if hasattr(self, 'copy_button') and self.copy_button is not None and self.copy_button.winfo_exists(): self.copy_button.configure(state="normal" if self.last_ai_summary else "disabled")

        # Re-enable smart buttons
        if hasattr(self, 'smart_buttons_widgets'):
             for btn in self.smart_buttons_widgets:
                 try:
                     if isinstance(btn, ctk.CTkButton) and btn.winfo_exists(): btn.configure(state="normal")
                 except Exception as e: print(f"Error enabling smart button: {e}")

        # Update the AI summary label safely
        if hasattr(self, 'ai_summary_label') and self.ai_summary_label is not None:
            try:
                if self.ai_summary_label.winfo_exists():
                     # Determine text color based on whether it's an error message
                     text_color = utils.COLOR_TEXT_ERROR if response_summary.startswith("Error:") else utils.COLOR_TEXT_PRIMARY
                     self.ai_summary_label.configure(text=self.last_ai_summary, text_color=text_color) # Update text and color
            except Exception as e: print(f"Error updating AI summary label: {e}")

        print("UI updated with AI response summary.")


    def _copy_last_response(self):
        """Copies the last AI summary text to the clipboard."""
        text_to_copy = self.last_ai_summary
        if text_to_copy and not text_to_copy.startswith("Error:"): # Don't copy error messages
            try:
                self.clipboard_clear()
                self.clipboard_append(text_to_copy)
                print("✅ Copied last AI summary to clipboard.")
                # Temporarily change button text for feedback
                if hasattr(self, 'copy_button') and self.copy_button.winfo_exists():
                    self.copy_button.configure(text="Copied!")
                    # Use lambda to ensure winfo_exists is checked *when* the after delay completes
                    self.after(1500, lambda: self.copy_button.configure(text="Copy") if hasattr(self, 'copy_button') and self.copy_button.winfo_exists() else None)
            except Exception as e:
                print(f"❌ Error copying to clipboard: {e}")
                # Optionally show error in UI
                if hasattr(self, 'ai_summary_label') and self.ai_summary_label.winfo_exists():
                     self.ai_summary_label.configure(text="Error copying text.", text_color=utils.COLOR_TEXT_ERROR)
        elif text_to_copy.startswith("Error:"):
             print("⚠️ Cannot copy error messages.")
        else:
            print("⚠️ No AI summary available to copy.")


    def on_ask(self, event=None):
        """Handles the user asking a question (via button or Enter key)."""
        # Determine user input source
        if isinstance(event, str):
             user_input = event # Use the string directly for initial analysis/specific calls
             print(f"AI analysis triggered with context: '{user_input}'")
             # Do not proceed if OCR failed initially
             if self.ocr_text.startswith("Error:"):
                  print("Skipping initial analysis due to OCR error.")
                  return
        else:
             # Check if user_entry exists and is valid before getting value
             if not hasattr(self, 'user_entry') or self.user_entry is None or not self.user_entry.winfo_exists():
                  print("Error: User entry widget does not exist.")
                  return
             user_input = self.user_entry.get().strip() # Get text from entry
             if not user_input:
                 print("Empty input, ignoring.")
                 return # Ignore empty input
             print(f"Ask triggered with input: '{user_input}', starting loading...")
             self.user_entry.delete(0, "end") # Clear the entry

        if self.is_loading:
            print("Already loading, ignoring request.")
            return # Prevent multiple simultaneous requests

        self.is_loading = True
        self.last_ai_summary = "" # Clear previous summary

        # Disable UI elements safely
        if hasattr(self, 'user_entry') and self.user_entry.winfo_exists(): self.user_entry.configure(state="disabled")
        if hasattr(self, 'ask_button') and self.ask_button.winfo_exists(): self.ask_button.configure(state="disabled")
        if hasattr(self, 'copy_button') and self.copy_button.winfo_exists(): self.copy_button.configure(state="disabled")
        if hasattr(self, 'smart_buttons_widgets'):
            for btn in self.smart_buttons_widgets:
                 try: # Add try-except for safety
                      if isinstance(btn, ctk.CTkButton) and btn.winfo_exists(): btn.configure(state="disabled")
                 except Exception as e: print(f"Error disabling smart button: {e}")


        # Show and start the progress bar
        if hasattr(self, 'progress_bar') and self.progress_bar is not None:
             try:
                 if self.progress_bar.winfo_exists():
                     # Grid it in row 4 of dashboard_frame
                     self.progress_bar.grid(row=4, column=0, sticky="ew", pady=(5, 10), padx=10) # Added bottom padding
                     self.progress_bar.start()
                 else: print("Warning: Progress bar widget no longer exists when trying to grid.")
             except tkinter.TclError as e: print(f"Ignoring TclError during progress bar grid: {e}")
             except Exception as e: print(f"Error gridding progress bar: {e}")
        else: print("Warning: Progress bar not initialized.")

        # Update summary label to show loading state
        if hasattr(self, 'ai_summary_label') and self.ai_summary_label is not None:
             try:
                 if self.ai_summary_label.winfo_exists():
                      self.ai_summary_label.configure(text="Asking AI...", text_color=utils.COLOR_TEXT_SECONDARY)
             except Exception as e: print(f"Error updating summary label to loading: {e}")


        self.update_idletasks() # Ensure UI updates before thread start

        # Start the AI request thread
        thread = threading.Thread(target=self._run_ai_in_thread, args=(user_input,), daemon=True)
        thread.start()


# --- Entry Point ---
if __name__ == "__main__":
    # --- Argument Parsing ---
    if len(sys.argv) != 4:
        print("Usage: python phishrx_ai_gui.py <Severity> <Reasons|''> <ImagePath>") # Updated usage message
        print("Example: python phishrx_ai_gui.py \"Medium\" \"Contains URL|Urgency\" \"/path/to/screenshot.png\"")
        print("\nAttempting to run with default test values...")
        # --- Default Test Values ---
        severity = "High"
        # Reasons are determined by find_suspicious_text, pass empty initially for test
        initial_reasons = []
        image_path = "test_screenshot.png" # Default test image name

        # Create dummy image if it doesn't exist and PIL is available
        if not os.path.exists(image_path) and utils.PIL_AVAILABLE: # Check utils.PIL_AVAILABLE
            try:
                from PIL import Image, ImageDraw, ImageFont # Import PIL locally for dummy image creation
                img = Image.new('RGB', (600, 400), color = (200, 220, 255))
                d = ImageDraw.Draw(img)
                try: fnt = ImageFont.truetype("arial.ttf", 15)
                except IOError: fnt = ImageFont.load_default()
                d.text((10,10), f"Subject: URGENT: Verify Your Account Password!\n\nDear User,\n\nPlease confirm your password by clicking here: http://example.com\n\nThanks,\nSupport Team", fill=(50,50,50), font=fnt)
                img.save(image_path)
                print(f"Created dummy image: {image_path}")
            except Exception as img_err:
                print(f"Could not create dummy image: {img_err}.")
        elif not os.path.exists(image_path):
             print(f"Warning: Test image '{image_path}' not found and cannot be created (PIL unavailable).")

        print(f"Running with default test values: Severity='{severity}', Image='{image_path}'")

    else:
        # Get values from command line arguments
        severity = sys.argv[1]
        # Reasons argument is not directly used now, as find_suspicious_text handles it
        initial_reasons_str = sys.argv[2] # Keep for potential future use or logging
        image_path = sys.argv[3]
        initial_reasons = initial_reasons_str.split('|') if initial_reasons_str else [] # Split if provided

        print(f"Received arguments: Severity='{severity}', Image='{image_path}'")
        if not os.path.exists(image_path):
             print(f"❌ ERROR: Image path from argument does not exist: {image_path}")
             # Handle error appropriately - maybe exit or show error in UI
             # For now, we'll let the __init__ handle the error message display
             # sys.exit(1)


    # Initialize and run the app
    app = PhishRxApp(severity, initial_reasons, image_path) # Use renamed class
    app.mainloop()
