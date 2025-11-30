#!/usr/bin/env python3
# ==== GUARDIAN AI – ACTORS GUI =================================================
# Single-file GUI with:
# - Top nav (Analysis / Pipeline / ACTORS / Learning)
# - Verdict card + screenshot (if provided)
# - Smart ACTORS question buttons
# - Feedback buttons
# - Learning and ACTORS views
# ==============================================================================

import customtkinter as ctk
from tkinter import filedialog, messagebox
import tkinter as tk
import os
import sys
import threading
import queue
from datetime import datetime
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# ----------------- Simple data holder -----------------
class AnalysisResult:
    def __init__(self, severity="✅ SAFE", reasons=None, image_path=None, confidence=0.85):
        self.severity = severity
        self.reasons = reasons or []
        self.image_path = image_path
        self.confidence = confidence
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# ----------------- Mock “engine” hooks -----------------
def mock_ai_response(query, analysis: AnalysisResult | None):
    if analysis and "HIGH" in analysis.severity:
        return "🚨 This looks dangerous. Do NOT click links or enter credentials."
    if "safe" in query.lower():
        return "✅ This appears safe based on the current information."
    return "🔍 No immediate threats detected, but stay cautious."

def mock_record_feedback(was_correct: bool, confidence: float, severity: str):
    # Here you’d call your real analytics.record_scan_result(...)
    pass

def mock_calculate_accuracy():
    # Replace with analytics.calculate_accuracy()
    return 0.86 + np.random.random() * 0.05

# ==============================================================================
#                                GUI CLASS
# ==============================================================================
class GuardianAI(ctk.CTk):
    def __init__(self, initial_analysis: AnalysisResult | None = None):
        super().__init__()
        self.current_analysis = initial_analysis
        self.ai_response_queue: queue.Queue[str] = queue.Queue()
        self.is_loading_ai = False

        self.chat_log_frame: ctk.CTkScrollableFrame | None = None
        self.chat_entry: ctk.CTkEntry | None = None
        self.smart_button_frame: ctk.CTkFrame | None = None
        self.feedback_frame: ctk.CTkFrame | None = None

        self._setup_window()
        self._setup_header()
        self._setup_content()
        self._setup_navigation()

        self.after(100, self.show_analysis_view)
        self.after(150, self._check_ai_response_queue)

    # ---------- window + header ----------
    def _setup_window(self):
        self.title("🛡️ GUARDIAN AI – PhishRx")
        self.geometry("1100x800")
        self.minsize(950, 700)
        ctk.set_appearance_mode("dark")
        self.configure(fg_color="#0b1015")

    def _setup_header(self):
        header = ctk.CTkFrame(self, height=70, corner_radius=0, fg_color="#020817")
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            header,
            text="🛡️ GUARDIAN AI",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color="#f97373",
        )
        title.grid(row=0, column=0, padx=30, pady=18, sticky="w")

        self.status_label = ctk.CTkLabel(
            header,
            text="Status: Ready",
            font=ctk.CTkFont(size=14),
            text_color="#22c55e",
        )
        self.status_label.grid(row=0, column=1, padx=20, pady=18, sticky="e")

    def _setup_content(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.content_frame = ctk.CTkFrame(self, fg_color="#020617", corner_radius=0)
        self.content_frame.grid(row=1, column=0, sticky="nsew")
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(1, weight=1)

    # ---------- navigation ----------
    def _setup_navigation(self):
        nav_frame = ctk.CTkFrame(self.content_frame, fg_color="#0f172a", height=58)
        nav_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        nav_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        tabs = [
            ("📱 Analysis", self.show_analysis_view),
            ("⚙️ Pipeline", self.show_pipeline_view),
            ("🔬 ACTORS", self.show_actors_view),
            ("📊 Learning", self.show_learning_view),
        ]
        self._nav_buttons = []
        for i, (label, callback) in enumerate(tabs):
            btn = ctk.CTkButton(
                nav_frame,
                text=label,
                height=44,
                font=ctk.CTkFont(size=16, weight="bold"),
                fg_color="#1f2937" if i == 0 else "transparent",
                text_color="#e5e7eb" if i == 0 else "#9ca3af",
                hover_color="#1d4ed8",
                command=lambda cb=callback, idx=i: self._on_tab_click(idx, cb),
            )
            btn.grid(row=0, column=i, padx=4, pady=7, sticky="ew")
            self._nav_buttons.append(btn)

    def _on_tab_click(self, index: int, callback):
        for i, btn in enumerate(self._nav_buttons):
            if i == index:
                btn.configure(fg_color="#1f2937", text_color="#e5e7eb")
            else:
                btn.configure(fg_color="transparent", text_color="#9ca3af")
        callback()

    def _clear_body(self):
        # Clear everything below the nav bar (row=1+)
        for child in self.content_frame.grid_slaves():
            info = child.grid_info()
            if info.get("row", 99) >= 1:
                child.destroy()

    # ==============================================================================
    #                                VIEWS
    # ==============================================================================
    def show_analysis_view(self):
        self._clear_body()
        self.status_label.configure(text="Analysis – upload or review last scan")
        self._build_analysis_view()

    def show_pipeline_view(self):
        self._clear_body()
        self.status_label.configure(text="Pipeline – ACTORS flow overview")
        self._build_pipeline_view()

    def show_actors_view(self):
        self._clear_body()
        self.status_label.configure(text="ACTORS – live reasoning demo")
        self._build_actors_view()

    def show_learning_view(self):
        self._clear_body()
        self.status_label.configure(text="Learning – performance over time")
        self._build_learning_view()

    # ---------- Analysis view ----------
    def _build_analysis_view(self):
        # Top: verdict + smart questions
        verdict_frame = ctk.CTkFrame(self.content_frame, fg_color="#020617")
        verdict_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 5))

        if self.current_analysis:
            self._render_verdict_card(verdict_frame, self.current_analysis)
            self._render_smart_questions(verdict_frame, self.current_analysis)
        else:
            lbl = ctk.CTkLabel(
                verdict_frame,
                text="No scan loaded yet. Upload a screenshot to begin.",
                font=ctk.CTkFont(size=14),
                text_color="#9ca3af",
            )
            lbl.pack(pady=12, anchor="w", padx=10)

        # Middle: chat log
        self.chat_log_frame = ctk.CTkScrollableFrame(
            self.content_frame, fg_color="#020617"
        )
        self.chat_log_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 10))
        self.content_frame.grid_rowconfigure(2, weight=1)

        self._add_message(
            "🛡️ Guardian AI online. I’ll help you understand this page and stay safe.",
            "#22c55e",
        )
        self._add_message(
            "📸 Upload a screenshot or ask a question about the current analysis.",
            "#9ca3af",
        )

        # Bottom: input bar
        input_frame = ctk.CTkFrame(self.content_frame, fg_color="#020617", height=70)
        input_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 20))
        input_frame.grid_columnconfigure(1, weight=1)

        upload_btn = ctk.CTkButton(
            input_frame,
            text="📸 Upload",
            width=90,
            height=48,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color="#2563eb",
            hover_color="#1d4ed8",
            command=self._upload_screenshot,
        )
        upload_btn.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.chat_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="Ask Guardian AI about this page...",
            height=48,
            font=ctk.CTkFont(size=14),
        )
        self.chat_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        self.chat_entry.bind("<Return>", self._send_message)

        send_btn = ctk.CTkButton(
            input_frame,
            text="➤ Send",
            width=90,
            height=48,
            fg_color="#22c55e",
            hover_color="#16a34a",
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self._send_message,
        )
        send_btn.grid(row=0, column=2, padx=10, pady=10, sticky="e")

        # Feedback (appears only when we have an analysis)
        self._render_feedback_row()

    def _render_verdict_card(self, parent: ctk.CTkFrame, analysis: AnalysisResult):
        card = ctk.CTkFrame(parent, fg_color="#0f172a", corner_radius=10)
        card.pack(fill="x", padx=5, pady=(8, 4))

        # Icon + title
        if "HIGH" in analysis.severity:
            icon = "🚨 HIGH RISK"
            color = "#ef4444"
        elif "MEDIUM" in analysis.severity or "⚠️" in analysis.severity:
            icon = "⚠️ Suspicious"
            color = "#eab308"
        else:
            icon = "✅ Safe"
            color = "#22c55e"

        title = ctk.CTkLabel(
            card,
            text=f"{icon}   (confidence {analysis.confidence:.0%})",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=color,
        )
        title.pack(anchor="w", padx=10, pady=(8, 4))

        # Reasons
        reasons_text = (
            "\n".join(f"• {r}" for r in analysis.reasons) or "• No specific threats identified."
        )
        reasons_lbl = ctk.CTkLabel(
            card,
            text=reasons_text,
            font=ctk.CTkFont(size=14),
            text_color="#e5e7eb",
            justify="left",
        )
        reasons_lbl.pack(anchor="w", padx=10, pady=(0, 6))

        # Optional screenshot hint
        if analysis.image_path and os.path.exists(analysis.image_path):
            hint = ctk.CTkLabel(
                card,
                text=f"Screenshot: {os.path.basename(analysis.image_path)}",
                font=ctk.CTkFont(size=12),
                text_color="#9ca3af",
            )
            hint.pack(anchor="w", padx=10, pady=(0, 6))

    def _render_smart_questions(self, parent: ctk.CTkFrame, analysis: AnalysisResult):
        if not analysis.reasons:
            return
        self.smart_button_frame = ctk.CTkFrame(parent, fg_color="#020617")
        self.smart_button_frame.pack(fill="x", padx=5, pady=(0, 6))

        questions = {"What should I do next?", "How did you detect this?"}
        for reason in analysis.reasons:
            low = reason.lower()
            if any(w in low for w in ["urgent", "now", "immediate"]):
                questions.add("Why is the urgency tactic risky?")
            if any(w in low for w in ["link", "url", "click"]):
                questions.add("How can I safely check this link?")
            if any(w in low for w in ["password", "login", "account"]):
                questions.add("Why is it asking for my credentials?")

        for q in list(questions)[:4]:
            btn = ctk.CTkButton(
                self.smart_button_frame,
                text=q,
                height=32,
                fg_color="#111827",
                hover_color="#1f2937",
                text_color="#e5e7eb",
                font=ctk.CTkFont(size=13),
                command=lambda qq=q: self._ask_smart_question(qq),
            )
            btn.pack(side="left", padx=4, pady=4)

    def _render_feedback_row(self):
        if not self.current_analysis:
            return
        self.feedback_frame = ctk.CTkFrame(self.content_frame, fg_color="#020617")
        self.feedback_frame.grid(row=4, column=0, sticky="ew", padx=20, pady=(0, 10))

        label = ctk.CTkLabel(
            self.feedback_frame,
            text="Was this verdict accurate?",
            font=ctk.CTkFont(size=13),
            text_color="#9ca3af",
        )
        label.pack(side="left", padx=(5, 10))

        buttons = [
            ("✅ Correct", True, "#22c55e"),
            ("❌ Missed threat", False, "#ef4444"),
            ("⚠️ False alarm", False, "#eab308"),
        ]
        for text, is_correct, color in buttons:
            b = ctk.CTkButton(
                self.feedback_frame,
                text=text,
                height=30,
                fg_color=color,
                hover_color="#ffffff",
                text_color="#020617",
                font=ctk.CTkFont(size=12, weight="bold"),
                command=lambda ok=is_correct, t=text: self._on_feedback(ok, t),
            )
            b.pack(side="left", padx=4, pady=4)

    # ---------- other views ----------
    def _build_pipeline_view(self):
        frame = ctk.CTkFrame(self.content_frame, fg_color="#020617")
        frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)

        ctk.CTkLabel(
            frame,
            text="ACTORS Pipeline",
            font=ctk.CTkFont(size=30, weight="bold"),
            text_color="#f97373",
        ).pack(pady=(10, 20))

        steps = [
            "📸 Screenshot capture",
            "🔍 YOLOv8 element detection",
            "📝 OCR text extraction",
            "🎯 Threat scoring (rules + ML)",
            "🛡️ Guardian verdict",
            "💭 Smart questions",
            "👨‍🏫 Feedback → learning",
        ]
        for s in steps:
            ctk.CTkLabel(
                frame,
                text=s,
                font=ctk.CTkFont(size=18),
                text_color="#e5e7eb",
            ).pack(anchor="w", padx=20, pady=4)

    def _build_actors_view(self):
        frame = ctk.CTkFrame(self.content_frame, fg_color="#020617")
        frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)

        ctk.CTkLabel(
            frame,
            text="🔬 ACTORS Live Reasoning",
            font=ctk.CTkFont(size=30, weight="bold"),
            text_color="#f97373",
        ).pack(pady=(10, 25))

        desc = (
            "This demo walks through Reason → Evaluate → Execute on a fake scan.\n"
            "In your full build, this will replay the real decision trace for each verdict."
        )
        ctk.CTkLabel(
            frame,
            text=desc,
            font=ctk.CTkFont(size=14),
            text_color="#9ca3af",
            justify="left",
        ).pack(pady=(0, 20))

        demo_btn = ctk.CTkButton(
            frame,
            text="▶️ Run ACTORS demo",
            height=60,
            width=260,
            fg_color="#22c55e",
            hover_color="#16a34a",
            font=ctk.CTkFont(size=20, weight="bold"),
            command=self._run_actors_demo,
        )
        demo_btn.pack(pady=10)

    def _build_learning_view(self):
        frame = ctk.CTkFrame(self.content_frame, fg_color="#020617")
        frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)

        ctk.CTkLabel(
            frame,
            text="🧠 Guardian AI Learning",
            font=ctk.CTkFont(size=30, weight="bold"),
            text_color="#e5e7eb",
        ).pack(pady=(10, 25))

        acc = mock_calculate_accuracy()
        ctk.CTkLabel(
            frame,
            text=f"🎯 Current accuracy: {acc:.1%}",
            font=ctk.CTkFont(size=36, weight="bold"),
            text_color="#22c55e",
        ).pack(pady=10)

        btn_row = ctk.CTkFrame(frame, fg_color="transparent")
        btn_row.pack(pady=30)

        graph_btn = ctk.CTkButton(
            btn_row,
            text="📊 Show learning curve",
            height=70,
            width=280,
            fg_color="#2563eb",
            hover_color="#1d4ed8",
            font=ctk.CTkFont(size=20, weight="bold"),
            command=self._show_learning_graph,
        )
        graph_btn.pack(side="left", padx=10)

        train_btn = ctk.CTkButton(
            btn_row,
            text="👨‍🏫 Open training view",
            height=70,
            width=280,
            fg_color="#22c55e",
            hover_color="#16a34a",
            font=ctk.CTkFont(size=20, weight="bold"),
            command=self._show_training,
        )
        train_btn.pack(side="left", padx=10)

    # ==============================================================================
    #                          CHAT + EVENTS + HELPERS
    # ==============================================================================
    def _add_message(self, text: str, color: str = "#e5e7eb"):
        if not self.chat_log_frame:
            return
        frame = ctk.CTkFrame(self.chat_log_frame, fg_color="transparent")
        frame.pack(fill="x", padx=10, pady=4)
        lbl = ctk.CTkLabel(
            frame,
            text=text,
            font=ctk.CTkFont(size=14),
            text_color=color,
            justify="left",
            wraplength=800,
        )
        lbl.pack(anchor="w")
        self.chat_log_frame._parent_canvas.yview_moveto(1.0)

    def _send_message(self, event=None):
        if not self.chat_entry or self.is_loading_ai:
            return
        text = self.chat_entry.get().strip()
        if not text:
            return
        self.chat_entry.delete(0, "end")
        self._add_message(f"👤 You: {text}", "#60a5fa")
        self.is_loading_ai = True
        self._add_message("🤖 Guardian AI: 🔄 Analyzing...", "#fbbf24")
        threading.Thread(
            target=self._run_ai_thread, args=(text,), daemon=True
        ).start()

    def _ask_smart_question(self, q: str):
        if not self.chat_entry:
            return
        self._add_message(f"👤 You: {q}", "#60a5fa")
        self.is_loading_ai = True
        self._add_message("🤖 Guardian AI: 🔄 Analyzing...", "#fbbf24")
        threading.Thread(
            target=self._run_ai_thread, args=(q,), daemon=True
        ).start()

    def _run_ai_thread(self, query: str):
        resp = mock_ai_response(query, self.current_analysis)
        self.ai_response_queue.put(resp)
        self.is_loading_ai = False

    def _upload_screenshot(self):
        path = filedialog.askopenfilename(
            filetypes=[("Images", "*.png *.jpg *.jpeg *.webp")]
        )
        if not path:
            return
        # In your full build, you’d send this to the engine and get real severity/reasons.
        self.current_analysis = AnalysisResult(
            severity="⚠️ MEDIUM RISK",
            reasons=["Detected login form", "Contains external link", "Unusual sender"],
            image_path=path,
            confidence=0.82,
        )
        messagebox.showinfo(
            "Guardian AI",
            "Screenshot loaded. Reopening Analysis view with updated verdict.",
        )
        self.show_analysis_view()

    def _on_feedback(self, was_correct: bool, label: str):
        if not self.current_analysis:
            return
        mock_record_feedback(
            was_correct, self.current_analysis.confidence, self.current_analysis.severity
        )
        self._add_message(f"✅ Feedback received: {label}", "#9ca3af")
        # Disable buttons after one click
        if self.feedback_frame:
            for child in self.feedback_frame.winfo_children():
                if isinstance(child, ctk.CTkButton):
                    child.configure(state="disabled")

    def _run_actors_demo(self):
        messagebox.showinfo(
            "ACTORS Demo",
            "Reason → Evaluate → Execute demo.\n\nIn your full build, this will replay the actual decision trace.",
        )

    def _show_learning_graph(self):
        x = np.arange(1, 26)
        base = 0.6 + 0.015 * x
        noise = np.random.normal(0, 0.015, size=x.shape).cumsum()
        y = np.clip(base + noise, 0.4, 1.0)

        fig, ax = plt.subplots(figsize=(10, 6), facecolor="#020617")
        ax.set_facecolor("#020617")
        ax.plot(x, y, "o-", color="#22c55e", linewidth=3, markersize=8)
        ax.fill_between(x, y, 0.4, color="#22c55e", alpha=0.25)
        ax.set_ylim(0.4, 1.02)
        ax.set_xlabel("Feedback events", color="white", fontsize=12)
        ax.set_ylabel("Estimated accuracy", color="white", fontsize=12)
        ax.set_title("Guardian AI learning over time", color="white", fontsize=16)
        ax.tick_params(colors="white")
        ax.grid(True, alpha=0.3)

        win = ctk.CTkToplevel(self)
        win.title("Learning curve")
        win.geometry("900x600")
        canvas = FigureCanvasTkAgg(fig, master=win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
        plt.close(fig)

    def _show_training(self):
        win = ctk.CTkToplevel(self)
        win.title("Training interface")
        win.geometry("700x500")
        ctk.CTkLabel(
            win,
            text="Here you’ll add labeled examples and corrections.\nIn the full build this will write to your training/feedback store.",
            font=ctk.CTkFont(size=16),
            justify="left",
        ).pack(expand=True, padx=20, pady=40)

    def _check_ai_response_queue(self):
        try:
            while True:
                resp = self.ai_response_queue.get_nowait()
                self._add_message(f"🤖 Guardian AI: {resp}", "#e5e7eb")
        except queue.Empty:
            pass
        self.after(120, self._check_ai_response_queue)

# ==============================================================================
#                               ENTRY POINT
# ==============================================================================

def parse_cli_args() -> AnalysisResult | None:
    """
    Tray calls: python phisher_ai_gui.py "<severity>" "<reasons>|..." "<image_path>"
    Returns an AnalysisResult built from those args, or None if not provided.
    """
    if len(sys.argv) == 4:
        severity = sys.argv[1]
        reasons_raw = sys.argv[2]
        image_path = sys.argv[3]

        reasons = reasons_raw.split("|") if reasons_raw else []
        return AnalysisResult(
            severity=severity,
            reasons=reasons,
            image_path=image_path,
            confidence=0.85,
        )
    return None


if __name__ == "__main__":
    initial = parse_cli_args()
    app = GuardianAI(initial_analysis=initial)
    app.mainloop()
