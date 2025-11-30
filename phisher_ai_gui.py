#!/usr/bin/env python3
# ==============================================================================
# ==== GUARDIAN AI: ACTORS FRAMEWORK  ================
# ==============================================================================
# - Unified Codebase: Merged logic from previous iterations.
# - UI Polish: enhanced layout, spacing, and "SecOps" aesthetic.
# - Feature: Live "ACTORS" reasoning terminal simulation.
# - Feature: Dynamic Matplotlib integration with dark mode styling.
# ==============================================================================

import customtkinter as ctk
from tkinter import filedialog, messagebox
import tkinter as tk
import os
import sys
import threading
import queue
import time
import random
from datetime import datetime
import numpy as np
import matplotlib

# Ensure Matplotlib doesn't crash the GUI thread
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# ==============================================================================
#                                CONFIGURATION
# ==============================================================================

# Cyber/SecOps Color Palette
COLORS = {
    "bg_dark": "#050505",       # Deepest Black
    "bg_card": "#0f111a",       # Dark Navy
    "bg_nav": "#0a0c12",        # Navbar
    "accent_blue": "#3b82f6",   # Bright Blue
    "accent_red": "#ef4444",    # Danger Red
    "accent_green": "#10b981",  # Success Green
    "accent_warn": "#f59e0b",   # Warning Orange
    "text_main": "#e2e8f0",     # Off-white
    "text_dim": "#94a3b8",      # Gray
}

# ==============================================================================
#                             DATA STRUCTURES
# ==============================================================================

class AnalysisResult:
    """Holds data for a specific security scan."""
    def __init__(self, severity="✅ SAFE", reasons=None, image_path=None, confidence=0.85):
        self.severity = severity
        self.reasons = reasons or []
        self.image_path = image_path
        self.confidence = confidence
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# ==============================================================================
#                             LOGIC & MOCKS
# ==============================================================================

class MockEngine:
    """Simulates the backend AI/LLM processing."""
    
    @staticmethod
    def get_ai_response(query, analysis: AnalysisResult | None):
        """Simulates an LLM response with context awareness."""
        time.sleep(1.2) # Simulate thinking
        
        q_lower = query.lower()
        
        # Context: High Risk Analysis
        if analysis and "HIGH" in analysis.severity:
            if "click" in q_lower or "link" in q_lower:
                return "🚨 **CRITICAL:** Do not interact. The URL structure mimics a legitimate bank but uses a homograph attack."
            return "This page exhibits 98% similarity to a known phishing kit. Immediate isolation recommended."

        # Context: General Safe
        if "safe" in q_lower:
            return "✅ Heuristic analysis indicates this page is legitimate. SSL certificates are valid and domain age is >5 years."
            
        if "actors" in q_lower:
            return "The ACTORS framework (Adaptive Cognitive Threat Observation & Reasoning System) is currently monitoring this session."

        return "I've analyzed the DOM structure and visual layout. No immediate anomalies detected, but standard caution is advised."

    @staticmethod
    def generate_actors_trace():
        """Generates a fake execution trace for the ACTORS demo."""
        steps = [
            ("👀 OBSERVE", "Scanning visual elements... detected 'Login Button' and 'Urgency Banner'."),
            ("🧠 REASON", "Urgency banner ('Act Now!') correlates with social engineering tactics."),
            ("📚 RECALL", "Retrieving phishing signatures... Match found: Generic Microsoft harvest kit."),
            ("⚖️ EVALUATE", "Confidence Score calculated: 0.92 (High)."),
            ("🛡️ ACT", "Flagging URL as malicious. Generating user warning."),
        ]
        return steps

# ==============================================================================
#                                GUI CLASS
# ==============================================================================

class GuardianAI(ctk.CTk):
    def __init__(self, initial_analysis: AnalysisResult | None = None):
        super().__init__()
        
        # Core State
        self.current_analysis = initial_analysis
        self.ai_queue = queue.Queue()
        self.is_processing = False
        
        # UI Setup
        self._init_window()
        self._init_layout()
        
        # Start
        self.after(100, self.show_view_analysis)
        self.after(200, self._process_ai_queue)

    def _init_window(self):
        self.title("🛡️ GUARDIAN AI // PhishRx IEEE Ed.")
        self.geometry("1200x850")
        self.minsize(1000, 700)
        ctk.set_appearance_mode("Dark")
        self.configure(fg_color=COLORS["bg_dark"])

    def _init_layout(self):
        # 1. Header (Top Bar)
        self.header = ctk.CTkFrame(self, height=60, corner_radius=0, fg_color=COLORS["bg_nav"])
        self.header.pack(side="top", fill="x")
        
        # Logo Area
        logo_lbl = ctk.CTkLabel(
            self.header, 
            text="🛡️ GUARDIAN AI", 
            font=ctk.CTkFont(family="Roboto", size=22, weight="bold"),
            text_color=COLORS["accent_blue"]
        )
        logo_lbl.pack(side="left", padx=25, pady=15)

        # Status Indicator
        self.status_indicator = ctk.CTkLabel(
            self.header,
            text="● SYSTEM READY",
            font=ctk.CTkFont(family="Consolas", size=12),
            text_color=COLORS["accent_green"]
        )
        self.status_indicator.pack(side="right", padx=25)

        # 2. Main Navigation (Tabs)
        self.nav_frame = ctk.CTkFrame(self, height=50, corner_radius=0, fg_color=COLORS["bg_card"])
        self.nav_frame.pack(side="top", fill="x", pady=(1,0)) # 1px line separator effect
        
        self.nav_buttons = {}
        tabs = [
            ("ANALYSIS", self.show_view_analysis),
            ("PIPELINE", self.show_view_pipeline),
            ("ACTORS LOGIC", self.show_view_actors),
            ("LEARNING", self.show_view_learning)
        ]
        
        for idx, (text, cmd) in enumerate(tabs):
            btn = ctk.CTkButton(
                self.nav_frame,
                text=text,
                font=ctk.CTkFont(size=14, weight="bold"),
                fg_color="transparent",
                text_color=COLORS["text_dim"],
                hover_color="#1e293b",
                width=120,
                corner_radius=0,
                command=lambda c=cmd, t=text: self._nav_click(t, c)
            )
            btn.pack(side="left", fill="y", padx=5)
            self.nav_buttons[text] = btn

        # 3. Content Area
        self.main_content = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self.main_content.pack(side="top", fill="both", expand=True, padx=20, pady=20)

        # Set default active tab
        self._highlight_nav("ANALYSIS")

    def _nav_click(self, text, callback):
        self._highlight_nav(text)
        self._clear_content()
        callback()

    def _highlight_nav(self, active_text):
        for text, btn in self.nav_buttons.items():
            if text == active_text:
                btn.configure(text_color=COLORS["accent_blue"], fg_color="#171e2e")
            else:
                btn.configure(text_color=COLORS["text_dim"], fg_color="transparent")

    def _clear_content(self):
        for widget in self.main_content.winfo_children():
            widget.destroy()

    # ==============================================================================
    #                               VIEW: ANALYSIS
    # ==============================================================================
    
    def show_view_analysis(self):
        # Split into Left (Verdict) and Right (Chat)
        self.main_content.columnconfigure(0, weight=4) # Verdict
        self.main_content.columnconfigure(1, weight=6) # Chat
        self.main_content.rowconfigure(0, weight=1)

        left_panel = ctk.CTkFrame(self.main_content, fg_color="transparent")
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 15))

        right_panel = ctk.CTkFrame(self.main_content, fg_color=COLORS["bg_card"], corner_radius=15)
        right_panel.grid(row=0, column=1, sticky="nsew")

        # --- LEFT PANEL: Verdict Card ---
        self._render_verdict_card(left_panel)

        # --- RIGHT PANEL: Chat ---
        self._render_chat_interface(right_panel)

    def _render_verdict_card(self, parent):
        card = ctk.CTkFrame(parent, fg_color=COLORS["bg_card"], corner_radius=15)
        card.pack(fill="x", pady=(0, 15))

        # 1. Header
        if self.current_analysis:
            sev = self.current_analysis.severity
            conf = self.current_analysis.confidence
            
            if "HIGH" in sev: color, icon = COLORS["accent_red"], "🚨"
            elif "MED" in sev: color, icon = COLORS["accent_warn"], "⚠️"
            else: color, icon = COLORS["accent_green"], "✅"
        else:
            sev, conf, color, icon = "NO DATA", 0.0, COLORS["text_dim"], "☁️"

        # Badge
        badge = ctk.CTkFrame(card, fg_color=color, height=40, corner_radius=10)
        badge.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkLabel(
            badge, text=f"{icon}  {sev}", 
            font=ctk.CTkFont(size=20, weight="bold"), text_color="#000000"
        ).pack(pady=5)

        # 2. Risk Meter
        ctk.CTkLabel(card, text="Confidence Level", text_color=COLORS["text_dim"]).pack(anchor="w", padx=20, pady=(10,0))
        
        meter_frame = ctk.CTkFrame(card, fg_color="transparent")
        meter_frame.pack(fill="x", padx=20, pady=(5, 15))
        
        progress = ctk.CTkProgressBar(meter_frame, height=12, progress_color=color)
        progress.pack(fill="x", pady=5)
        progress.set(conf)

        # 3. Reasons List
        if self.current_analysis:
            ctk.CTkLabel(card, text="Detected Artifacts:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=20)
            for reason in self.current_analysis.reasons:
                row = ctk.CTkFrame(card, fg_color="#182030", corner_radius=6)
                row.pack(fill="x", padx=20, pady=2)
                ctk.CTkLabel(row, text=f"• {reason}", text_color=COLORS["text_main"], anchor="w").pack(fill="x", padx=10, pady=5)
        
        # 4. Action Buttons
        btn_frame = ctk.CTkFrame(parent, fg_color="transparent")
        btn_frame.pack(fill="x")
        
        ctk.CTkButton(
            btn_frame, text="📸 Upload Screenshot", 
            fg_color=COLORS["accent_blue"], hover_color="#2563eb",
            command=self._upload_screenshot, height=45
        ).pack(fill="x", pady=5)

        if self.current_analysis:
            self._render_smart_buttons(parent)

    def _render_smart_buttons(self, parent):
        # Quick actions based on analysis
        lbl = ctk.CTkLabel(parent, text="Smart Actions (ACTORS)", text_color=COLORS["text_dim"], font=ctk.CTkFont(size=12))
        lbl.pack(anchor="w", pady=(15, 5))

        actions = ["Explain Analysis", "Show Raw HTTP Headers", "Generate Report"]
        for action in actions:
            ctk.CTkButton(
                parent, text=f"⚡ {action}", 
                fg_color="#1e293b", hover_color="#334155", 
                border_width=1, border_color="#334155",
                command=lambda a=action: self._handle_input(a)
            ).pack(fill="x", pady=2)

    def _render_chat_interface(self, parent):
        # Chat Header
        ctk.CTkLabel(parent, text="Guardian Assistant", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=15)
        
        # Scrollable Area
        self.chat_scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        self.chat_scroll.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Input Area
        input_container = ctk.CTkFrame(parent, fg_color="#0b0f19", height=60)
        input_container.pack(fill="x", padx=10, pady=10)
        
        self.chat_entry = ctk.CTkEntry(
            input_container, placeholder_text="Ask about the threat...", 
            border_width=0, fg_color="#182030", height=45
        )
        self.chat_entry.pack(side="left", fill="x", expand=True, padx=5, pady=5)
        self.chat_entry.bind("<Return>", lambda e: self._handle_input())

        ctk.CTkButton(
            input_container, text="➤", width=50, height=45,
            fg_color=COLORS["accent_blue"], command=self._handle_input
        ).pack(side="right", padx=5)

        # Initial Message
        self._add_chat_bubble("Guardian AI", "System initialized. Waiting for input artifact or query.", is_user=False)

    def _add_chat_bubble(self, sender, text, is_user=False):
        bubble_color = "#2563eb" if is_user else "#1e293b"
        align = "e" if is_user else "w" # East (right) or West (left)
        
        wrapper = ctk.CTkFrame(self.chat_scroll, fg_color="transparent")
        wrapper.pack(fill="x", pady=4)
        
        # The Bubble
        container = ctk.CTkFrame(wrapper, fg_color=bubble_color, corner_radius=12)
        container.pack(side="right" if is_user else "left", anchor=align, padx=10)
        
        # Text
        ctk.CTkLabel(
            container, text=text, text_color="white", 
            wraplength=400, justify="left", font=ctk.CTkFont(size=13)
        ).pack(padx=12, pady=8)
        
        # Auto scroll
        self.after(10, lambda: self.chat_scroll._parent_canvas.yview_moveto(1.0))

    def _handle_input(self, text_override=None):
        text = text_override or self.chat_entry.get().strip()
        if not text: return
        
        self.chat_entry.delete(0, 'end')
        self._add_chat_bubble("You", text, is_user=True)
        
        self.status_indicator.configure(text="● PROCESSING...", text_color=COLORS["accent_warn"])
        
        # Threaded processing
        threading.Thread(
            target=lambda: self.ai_queue.put(MockEngine.get_ai_response(text, self.current_analysis)),
            daemon=True
        ).start()

    def _process_ai_queue(self):
        try:
            while True:
                response = self.ai_queue.get_nowait()
                self._add_chat_bubble("Guardian AI", response, is_user=False)
                self.status_indicator.configure(text="● SYSTEM READY", text_color=COLORS["accent_green"])
        except queue.Empty:
            pass
        self.after(100, self._process_ai_queue)

    def _upload_screenshot(self):
        path = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *.jpeg")])
        if path:
            # Mocking analysis result based on random chance for demo
            is_bad = random.choice([True, False])
            self.current_analysis = AnalysisResult(
                severity="HIGH RISK" if is_bad else "✅ SAFE",
                reasons=["Suspicious IFRAME detected", "Homograph URL match"] if is_bad else ["Valid SSL", "Domain whitelist"],
                image_path=path,
                confidence=random.uniform(0.75, 0.99)
            )
            self.show_view_analysis() # Refresh view
            self._add_chat_bubble("System", f"Image uploaded. Analysis complete: {self.current_analysis.severity}", is_user=False)

    # ==============================================================================
    #                               VIEW: PIPELINE
    # ==============================================================================

    def show_view_pipeline(self):
        container = ctk.CTkFrame(self.main_content, fg_color="transparent")
        container.pack(expand=True, fill="both", padx=50)

        ctk.CTkLabel(container, text="ACTORS Processing Pipeline", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=20)

        # Visual Flow
        steps = [
            ("📸 Input Layer", "Capture & Pre-processing"),
            ("👁️ Vision (YOLOv8)", "Object Detection (Logos, Forms)"),
            ("📝 Text (Tesseract)", "OCR & NLP Analysis"),
            ("🧠 Reasoner (LLM)", "Contextual Threat Scoring"),
            ("🛡️ Verdict", "Final Policy Execution")
        ]

        for i, (title, sub) in enumerate(steps):
            # Card
            step_frame = ctk.CTkFrame(container, fg_color=COLORS["bg_card"], border_width=1, border_color=COLORS["accent_blue"])
            step_frame.pack(fill="x", pady=5)
            
            ctk.CTkLabel(step_frame, text=f"Step 0{i+1}", text_color=COLORS["accent_blue"], font=ctk.CTkFont(weight="bold")).pack(side="left", padx=20)
            
            info = ctk.CTkFrame(step_frame, fg_color="transparent")
            info.pack(side="left", padx=10)
            ctk.CTkLabel(info, text=title, font=ctk.CTkFont(size=16, weight="bold"), anchor="w").pack(fill="x")
            ctk.CTkLabel(info, text=sub, text_color=COLORS["text_dim"], anchor="w").pack(fill="x")
            
            # Arrow
            if i < len(steps) - 1:
                ctk.CTkLabel(container, text="⬇", font=ctk.CTkFont(size=20), text_color=COLORS["text_dim"]).pack()

    # ==============================================================================
    #                               VIEW: ACTORS (Reasoning)
    # ==============================================================================

    def show_view_actors(self):
        # Terminal-style visualization
        container = ctk.CTkFrame(self.main_content, fg_color=COLORS["bg_card"], corner_radius=10)
        container.pack(expand=True, fill="both")

        header = ctk.CTkFrame(container, height=40, fg_color="#1e1e1e")
        header.pack(fill="x")
        ctk.CTkLabel(header, text="  >_ ACTORS LIVE TRACE", font=ctk.CTkFont(family="Consolas"), text_color=COLORS["accent_green"]).pack(side="left")

        # Console Output
        self.console_box = ctk.CTkTextbox(container, font=ctk.CTkFont(family="Consolas", size=14), fg_color="#000000", text_color="#00ff00")
        self.console_box.pack(fill="both", expand=True, padx=5, pady=5)
        self.console_box.insert("end", "Waiting for trigger...\n")
        self.console_box.configure(state="disabled")

        btn = ctk.CTkButton(
            self.main_content, text="▶ EXECUTE SIMULATION", 
            fg_color=COLORS["accent_green"], text_color="black",
            font=ctk.CTkFont(weight="bold"),
            command=self._run_actors_simulation
        )
        btn.pack(pady=20)

    def _run_actors_simulation(self):
        self.console_box.configure(state="normal")
        self.console_box.delete("1.0", "end")
        
        def type_line(text, color_tag=None):
            self.console_box.insert("end", f"{text}\n")
            self.console_box.see("end")
            time.sleep(random.uniform(0.3, 0.8))

        def run_thread():
            trace = MockEngine.generate_actors_trace()
            type_line("[INIT] Loading ACTORS Modules...", "sys")
            time.sleep(1)
            for stage, msg in trace:
                type_line(f"[{stage}] {msg}")
            type_line("[COMPLETE] Trace finished.")
            self.console_box.configure(state="disabled")

        threading.Thread(target=run_thread, daemon=True).start()

    # ==============================================================================
    #                               VIEW: LEARNING
    # ==============================================================================

    def show_view_learning(self):
        container = ctk.CTkFrame(self.main_content, fg_color="transparent")
        container.pack(expand=True, fill="both")

        ctk.CTkLabel(container, text="Model Performance Metrics", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=(0, 20))

        # Generate Plot
        fig, ax = plt.subplots(figsize=(10, 5), facecolor=COLORS["bg_card"])
        ax.set_facecolor(COLORS["bg_card"])
        
        # Fake Data
        x = np.linspace(0, 50, 50)
        y = 0.5 + 0.4 * (1 - np.exp(-0.1 * x)) + np.random.normal(0, 0.02, 50)
        
        # Plot styling
        ax.plot(x, y, color=COLORS["accent_blue"], linewidth=2, label="Accuracy")
        ax.fill_between(x, y, 0, color=COLORS["accent_blue"], alpha=0.1)
        
        ax.set_title("Reinforcement Learning Curve", color=COLORS["text_main"])
        ax.set_xlabel("Epochs", color=COLORS["text_dim"])
        ax.set_ylabel("Precision", color=COLORS["text_dim"])
        ax.spines['bottom'].set_color(COLORS["text_dim"])
        ax.spines['left'].set_color(COLORS["text_dim"])
        ax.tick_params(axis='x', colors=COLORS["text_dim"])
        ax.tick_params(axis='y', colors=COLORS["text_dim"])
        ax.grid(color="#334155", linestyle='--', linewidth=0.5, alpha=0.5)

        canvas = FigureCanvasTkAgg(fig, master=container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

        # Stats Row
        stats = ctk.CTkFrame(container, fg_color="transparent")
        stats.pack(fill="x", pady=20)
        
        for label, val in [("Accuracy", "94.2%"), ("False Positives", "1.2%"), ("Samples", "14,203")]:
            f = ctk.CTkFrame(stats, fg_color=COLORS["bg_card"])
            f.pack(side="left", expand=True, fill="x", padx=5)
            ctk.CTkLabel(f, text=label, text_color=COLORS["text_dim"]).pack(pady=(10,0))
            ctk.CTkLabel(f, text=val, font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(0,10))

# ==============================================================================
#                                ENTRY POINT
# ==============================================================================

if __name__ == "__main__":
    # Check for CLI args (simulating integration with a backend script)
    initial_data = None
    if len(sys.argv) == 4:
        initial_data = AnalysisResult(
            severity=sys.argv[1],
            reasons=sys.argv[2].split("|"),
            image_path=sys.argv[3]
        )

    app = GuardianAI(initial_analysis=initial_data)
    app.mainloop()