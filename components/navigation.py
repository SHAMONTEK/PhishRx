# components/navigation.py - FIXED GRID/PACK CONFLICT
import customtkinter as ctk
from utils import AppColors, AppFonts

class ModernNavigation:
    def __init__(self, parent, content_frame):
        self.parent = parent
        self.content_frame = content_frame
        self.current_view = "analysis"
        self._create_modern_nav()
    
    def _create_modern_nav(self):
        """Modern bottom navigation bar using GRID to avoid pack/grid conflict"""
        # Bottom navigation container - USE GRID
        self.nav_frame = ctk.CTkFrame(self.parent, fg_color=AppColors.DARK_CARD, 
                                    height=60, corner_radius=0)
        self.nav_frame.grid(row=2, column=0, sticky="ew")  # ← CHANGED TO GRID
        self.nav_frame.grid_propagate(False)
        
        # Configure grid for equal spacing
        self.nav_frame.grid_columnconfigure((0,1,2,3,4), weight=1)
        
        # Navigation items - ICON + TEXT
        nav_items = [
            ("📊", "Analysis", self._show_analysis_view),
            ("🔧", "Tech Flow", self._show_tech_flow), 
            ("🛡️", "Security", self._show_security_center),
            ("📈", "Analytics", self._show_analytics),
            ("⚙️", "More", self._show_quick_menu)
        ]
        
        for i, (icon, text, command) in enumerate(nav_items):
            btn = ctk.CTkButton(self.nav_frame, text=f"{icon}\n{text}", 
                              font=AppFonts.INFO_FONT, height=50,
                              fg_color="transparent", 
                              text_color=AppColors.DARK_TEXT_SECONDARY,
                              hover_color=AppColors.DARK_CHAT_BOT,
                              command=command, anchor="center")
            btn.grid(row=0, column=i, sticky="nsew", padx=2, pady=5)  # ← USING GRID
            
            # Highlight current view
            if text.lower() == "analysis":
                btn.configure(fg_color=AppColors.BLUE, text_color="white")

    def _show_analysis_view(self):
        """Main analysis view with live tech flow"""
        self._update_nav_highlight("Analysis")
        self.parent._clear_content_frame()
        
        # MAIN LAYOUT: Tech Flow + Chat - USING GRID
        main_container = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        main_container.grid(row=0, column=0, sticky="nsew")  # ← USING GRID
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)
        
        # TOP: Live Tech Flow (60% of screen)
        tech_frame = ctk.CTkFrame(main_container, fg_color=AppColors.DARK_CARD, corner_radius=12)
        tech_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 10))  # ← USING GRID
        main_container.grid_rowconfigure(0, weight=3)  # 60% of space
        
        ctk.CTkLabel(tech_frame, text="🔄 LIVE ANALYSIS FLOW", 
                   font=AppFonts.SUBTITLE).pack(pady=10)
        
        # Live progress visualization
        self._create_live_tech_flow(tech_frame)
        
        # BOTTOM: Chat & Results (40% of screen)  
        chat_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        chat_frame.grid(row=1, column=0, sticky="nsew")  # ← USING GRID
        main_container.grid_rowconfigure(1, weight=2)  # 40% of space
        
        self.parent._setup_chat_interface(chat_frame)

    def _create_live_tech_flow(self, parent):
        """Create animated live tech flow"""
        flow_container = ctk.CTkFrame(parent, fg_color="transparent")
        flow_container.pack(fill="x", padx=20, pady=10)
        
        # Progress steps with real-time status
        self.flow_steps = [
            {"icon": "📸", "text": "Capturing Screen", "status": "completed"},
            {"icon": "🔍", "text": "Reading Text", "status": "completed"}, 
            {"icon": "🤖", "text": "AI Analyzing", "status": "active"},
            {"icon": "🎯", "text": "Threat Scoring", "status": "pending"},
            {"icon": "💬", "text": "Generating Report", "status": "pending"}
        ]
        
        # Create flow visualization
        steps_frame = ctk.CTkFrame(flow_container, fg_color="transparent")
        steps_frame.pack(fill="x")
        
        for i, step in enumerate(self.flow_steps):
            step_frame = ctk.CTkFrame(steps_frame, fg_color="transparent", width=120)
            step_frame.grid(row=0, column=i, padx=5)
            step_frame.grid_propagate(False)
            
            # Status indicator
            color = AppColors.GREEN if step["status"] == "completed" else \
                   AppColors.BLUE if step["status"] == "active" else AppColors.DARK_TEXT_SECONDARY
                   
            ctk.CTkLabel(step_frame, text=step["icon"], font=AppFonts.TITLE,
                       text_color=color).pack()
            ctk.CTkLabel(step_frame, text=step["text"], font=AppFonts.INFO_FONT,
                       text_color=color).pack()
            
            # Connector line (except last)
            if i < len(self.flow_steps) - 1:
                connector = ctk.CTkFrame(step_frame, fg_color=AppColors.DARK_TEXT_SECONDARY,
                                       height=2, width=20)
                connector.place(relx=1.0, rely=0.5, anchor="w")
        
        # Screenshot preview (click to enlarge)
        if hasattr(self.parent, 'current_analysis') and self.parent.current_analysis:
            self._create_screenshot_preview(flow_container)

    def _create_screenshot_preview(self, parent):
        """Create clickable screenshot preview"""
        preview_frame = ctk.CTkFrame(parent, fg_color=AppColors.DARK_CARD, corner_radius=8)
        preview_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(preview_frame, text="📷 Screenshot Preview", 
                   font=AppFonts.BUTTON_FONT).pack(pady=5)
        
        try:
            import utils
            img = utils.load_ctk_image(self.parent.current_analysis['image_path'], size=(400, 250))
            preview_btn = ctk.CTkButton(preview_frame, image=img, text="",
                                      fg_color="transparent", hover_color=AppColors.DARK_BORDER,
                                      command=self._enlarge_screenshot)
            preview_btn.pack(pady=5)
            
            # Future: Heatmap overlay
            ctk.CTkLabel(preview_frame, text="🔍 Click to view heatmap analysis", 
                       font=AppFonts.INFO_FONT, text_color=AppColors.DARK_TEXT_SECONDARY).pack(pady=5)
        except:
            ctk.CTkLabel(preview_frame, text="No screenshot available", 
                       text_color=AppColors.DARK_TEXT_SECONDARY).pack(pady=10)

    def _enlarge_screenshot(self):
        """Enlarge screenshot with heatmap overlay"""
        # Future: Show fullscreen with AI heatmaps
        self.parent._add_chat_bubble("🖼️ Opening detailed view with threat heatmap...", "bot")

    def _show_tech_flow(self):
        """Dedicated tech flow view"""
        self._update_nav_highlight("Tech Flow")
        self.parent._clear_content_frame()
        
        # Enhanced tech flow visualization
        tech_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        tech_frame.grid(row=0, column=0, sticky="nsew")  # ← USING GRID
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(tech_frame, text="🔧 ACTORS TECH FLOW", 
                   font=AppFonts.TITLE).pack(pady=10)
        
        # Simple flow for now
        ctk.CTkLabel(tech_frame, text="Real-time pipeline visualization\nComing soon with next update",
                   font=AppFonts.SUBTITLE, text_color=AppColors.DARK_TEXT_SECONDARY).pack(pady=20)

    def _update_nav_highlight(self, active_view):
        """Update navigation highlight"""
        for widget in self.nav_frame.winfo_children():
            if isinstance(widget, ctk.CTkButton):
                if active_view in widget.cget("text"):
                    widget.configure(fg_color=AppColors.BLUE, text_color="white")
                else:
                    widget.configure(fg_color="transparent", text_color=AppColors.DARK_TEXT_SECONDARY)

    def _show_security_center(self):
        """Show Security Center with logs"""
        self._update_nav_highlight("Security")
        self.parent._clear_content_frame()
        
        security_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        security_frame.grid(row=0, column=0, sticky="nsew")
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(security_frame, text="🛡️ Security Center", 
                   font=AppFonts.TITLE).pack(pady=10)
        
        # Simple placeholder
        ctk.CTkLabel(security_frame, text="Scan history and security logs\nComing soon",
                   font=AppFonts.SUBTITLE, text_color=AppColors.DARK_TEXT_SECONDARY).pack(pady=20)

    def _show_analytics(self):
        """Show analytics dashboard"""
        self._update_nav_highlight("Analytics")
        self.parent._clear_content_frame()
        
        analytics_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        analytics_frame.grid(row=0, column=0, sticky="nsew")
        
        ctk.CTkLabel(analytics_frame, text="📈 Analytics Dashboard", 
                   font=AppFonts.TITLE).pack(pady=10)
        
        # Simple placeholder
        ctk.CTkLabel(analytics_frame, text="Performance metrics and learning progress\nComing soon",
                   font=AppFonts.SUBTITLE, text_color=AppColors.DARK_TEXT_SECONDARY).pack(pady=20)

    def _show_quick_menu(self):
        """Show quick settings menu"""
        self._update_nav_highlight("More")
        self.parent._clear_content_frame()
        
        menu_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        menu_frame.grid(row=0, column=0, sticky="nsew")
        
        ctk.CTkLabel(menu_frame, text="⚙️ Quick Settings", 
                   font=AppFonts.TITLE).pack(pady=10)
        
        # Simple placeholder
        ctk.CTkLabel(menu_frame, text="Export data and app settings\nComing soon",
                   font=AppFonts.SUBTITLE, text_color=AppColors.DARK_TEXT_SECONDARY).pack(pady=20)AI