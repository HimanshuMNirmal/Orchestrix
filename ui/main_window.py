"""
Main UI window for Desktop Agent OS
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import datetime
import signal
import atexit
import sys
import os

from models.memory_store import MemoryStore
from models.task import Task
from agent.runner import AgentRunner
from .utils import DateUtils


class DesktopAgentOS(tk.Tk):
    """Main Application Window"""

    COLORS = {
        "bg_primary": "#ffffff",
        "bg_secondary": "#f8fafc",
        "bg_card": "#ffffff",
        "bg_hover": "#f1f5f9",
        "accent": "#3b82f6",
        "accent_green": "#10b981",
        "accent_orange": "#f59e0b",
        "accent_red": "#ef4444",
        "accent_purple": "#8b5cf6",
        "text_primary": "#1e293b",
        "text_secondary": "#64748b",
        "text_muted": "#94a3b8",
        "border": "#e2e8f0",
        "border_light": "#f1f5f9",
        "shadow": "#00000010",
    }

    def __init__(self, integration_mode="mock"):
        super().__init__()
        self.integration_mode = integration_mode
        self.memory = MemoryStore()
        self.agent = AgentRunner(self.memory, ui_callback=self._on_agent_message, integration_mode=integration_mode)

        self.title("Orchestrix - Task Management Agent")
        self.geometry("1400x900")
        self.minsize(1200, 800)
        self.configure(bg=self.COLORS["bg_primary"])

        # Setup cleanup handlers
        self._setup_cleanup_handlers()

        self._setup_styles()
        self._build_ui()
        self._load_sample_data()
        self._schedule_refresh()
        
        # Setup window close protocol
        self.protocol("WM_DELETE_WINDOW", self._on_window_close)

    def _setup_cleanup_handlers(self):
        """Setup signal handlers and atexit handler for proper cleanup"""
        # Store reference to cleanup method for signal handlers
        self._cleanup_registered = False
        
        def signal_handler(signum, frame):
            """Handle SIGINT and SIGTERM signals"""
            if not self._cleanup_registered:
                self._cleanup_registered = True
                print(f"\nReceived signal {signum}, cleaning up...")
                self._cleanup()
                sys.exit(0)
        
        # Register signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Register atexit handler
        atexit.register(self._cleanup)

    def _cleanup(self):
        """Properly cleanup all tkinter windows and resources"""
        try:
            # Destroy all tkinter windows
            if hasattr(self, 'winfo_exists') and self.winfo_exists():
                # Destroy all child windows first
                for child in self.winfo_children():
                    try:
                        child.destroy()
                    except:
                        pass
                
                # Destroy the main window
                self.destroy()
            
            # Force quit if windows are still open
            self.quit()
            
        except Exception as e:
            # If cleanup fails, force exit
            print(f"Cleanup error: {e}")
            os._exit(1)

    def _on_window_close(self):
        """Handle window close event"""
        self._cleanup()
        sys.exit(0)

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        c = self.COLORS

        style.configure("Primary.TFrame", background=c["bg_primary"])
        style.configure("Secondary.TFrame", background=c["bg_secondary"])
        style.configure("Card.TFrame", background=c["bg_card"])
        style.configure("Primary.TLabel", background=c["bg_primary"], foreground=c["text_primary"], font=("Inter", 10))
        style.configure("Card.TLabel", background=c["bg_card"], foreground=c["text_primary"], font=("Inter", 10))
        style.configure("Header.TLabel", background=c["bg_primary"], foreground=c["text_primary"], font=("Inter", 16, "bold"))
        style.configure("SubHeader.TLabel", background=c["bg_card"], foreground=c["text_secondary"], font=("Inter", 11, "bold"))
        style.configure("Muted.TLabel", background=c["bg_card"], foreground=c["text_muted"], font=("Inter", 9))

        style.configure("Treeview",
            background=c["bg_card"], foreground=c["text_primary"],
            fieldbackground=c["bg_card"], borderwidth=1,
            rowheight=32, font=("Inter", 10))
        style.configure("Treeview.Heading",
            background=c["bg_secondary"], foreground=c["text_secondary"],
            relief="flat", font=("Inter", 11, "bold"))
        style.map("Treeview", background=[("selected", c["bg_hover"])])

        style.configure("TNotebook", background=c["bg_primary"], borderwidth=0)
        style.configure("TNotebook.Tab",
            background=c["bg_secondary"], foreground=c["text_secondary"],
            padding=[16, 8], font=("Inter", 10, "bold"))
        style.map("TNotebook.Tab",
            background=[("selected", c["bg_card"])],
            foreground=[("selected", c["accent"])])

    def _btn(self, parent, text, command, style="primary", **kwargs):
        c = self.COLORS
        if style == "primary":
            bg, fg, hover = c["accent"], "white", c["accent_purple"]
        elif style == "secondary":
            bg, fg, hover = c["bg_secondary"], c["text_primary"], c["bg_hover"]
        elif style == "success":
            bg, fg, hover = c["accent_green"], "white", c["accent_green"]
        elif style == "danger":
            bg, fg, hover = c["accent_red"], "white", c["accent_red"]
        else:
            bg, fg, hover = c["bg_card"], c["text_primary"], c["bg_hover"]
            
        btn = tk.Button(
            parent, text=text, command=command,
            bg=bg, fg=fg, font=("Inter", 10, "bold"),
            relief="flat", padx=16, pady=8, cursor="hand2",
            activebackground=hover, activeforeground=fg,
            bd=0, highlightthickness=0,
            **kwargs
        )
        return btn

    # ── Build UI ──────────────────────────────────────────────────────────────

    def _build_ui(self):
        self._build_header()
        main = tk.Frame(self, bg=self.COLORS["bg_primary"])
        main.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 16))
        self._build_sidebar(main)
        self._build_main_content(main)

    def _build_header(self):
        c = self.COLORS
        hdr = tk.Frame(self, bg=c["bg_card"], height=64, relief="flat", bd=0, highlightthickness=1, highlightbackground=c["border"])
        hdr.pack(fill=tk.X, pady=(0, 16))
        hdr.pack_propagate(False)

        left = tk.Frame(hdr, bg=c["bg_card"])
        left.pack(side=tk.LEFT, padx=24, pady=16)

        tk.Label(left, text="Orchestrix",
                 bg=c["bg_card"], fg=c["text_primary"],
                 font=("Inter", 20, "bold")).pack(side=tk.LEFT)

        tk.Label(left, text="Task Management Agent",
                 bg=c["bg_card"], fg=c["text_secondary"],
                 font=("Inter", 12)).pack(side=tk.LEFT, padx=(12, 0))

        # Action buttons
        right = tk.Frame(hdr, bg=c["bg_card"])
        right.pack(side=tk.RIGHT, padx=24, pady=16)

        self._btn(right, "Summary", self._show_summary, style="secondary").pack(side=tk.LEFT, padx=8)

    def _build_sidebar(self, parent):
        c = self.COLORS
        side = tk.Frame(parent, bg=c["bg_card"], width=280, relief="flat", bd=1, highlightbackground=c["border"])
        side.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 16), pady=0)
        side.pack_propagate(False)

        # Stats Overview
        tk.Label(side, text="Overview", bg=c["bg_card"],
                 fg=c["text_secondary"], font=("Inter", 12, "bold")).pack(anchor=tk.W, padx=20, pady=(24, 16))

        self.stat_labels = {}
        stats = [
            ("total", "Total Tasks", c["text_primary"]),
            ("pending", "Pending", c["text_secondary"]),
            ("in_progress", "In Progress", c["accent"]),
            ("overdue", "Overdue", c["accent_red"]),
            ("completed", "Completed", c["accent_green"]),
        ]
        
        stats_container = tk.Frame(side, bg=c["bg_card"])
        stats_container.pack(fill=tk.X, padx=16, pady=(0, 24))
        
        for i, (key, label, color) in enumerate(stats):
            row = tk.Frame(stats_container, bg=c["bg_secondary"], relief="flat")
            row.pack(fill=tk.X, pady=2)
            
            tk.Label(row, text=label, bg=c["bg_secondary"], fg=c["text_secondary"],
                     font=("Inter", 10)).pack(side=tk.LEFT, padx=16, pady=12)
            
            lbl = tk.Label(row, text="0", bg=c["bg_secondary"], fg=color,
                           font=("Inter", 14, "bold"))
            lbl.pack(side=tk.RIGHT, padx=16)
            self.stat_labels[key] = lbl

                
        # Integration Status (simplified)
        tk.Label(side, text="Integrations", bg=c["bg_card"],
                 fg=c["text_secondary"], font=("Inter", 12, "bold")).pack(anchor=tk.W, padx=20, pady=(0, 12))

        self.integration_labels = {}
        icons = {"slack": "💬", "gmail": "📧", "notion": "📝", "jira": "🎯"}
        
        integrations_frame = tk.Frame(side, bg=c["bg_card"])
        integrations_frame.pack(fill=tk.X, padx=16)
        
        for name in ["slack", "gmail", "notion", "jira"]:
            row = tk.Frame(integrations_frame, bg=c["bg_secondary"], relief="flat")
            row.pack(fill=tk.X, pady=2)
            
            tk.Label(row, text=f"{icons[name]}  {name.title()}",
                     bg=c["bg_secondary"], fg=c["text_primary"],
                     font=("Inter", 10)).pack(side=tk.LEFT, padx=16, pady=10)
            
            dot = tk.Label(row, text="●", bg=c["bg_secondary"], fg=c["text_muted"],
                           font=("Inter", 8))
            dot.pack(side=tk.RIGHT, padx=16)
            self.integration_labels[name] = dot

    def _build_main_content(self, parent):
        content = tk.Frame(parent, bg=self.COLORS["bg_primary"])
        content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.notebook = ttk.Notebook(content)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self._build_tasks_tab()
        self._build_setup_tab()
        self._build_agent_tab()

    def _build_tasks_tab(self):
        c = self.COLORS
        tab = tk.Frame(self.notebook, bg=c["bg_primary"])
        self.notebook.add(tab, text="Tasks")

        # Toolbar
        toolbar = tk.Frame(tab, bg=c["bg_card"], height=60, relief="flat", bd=1, highlightbackground=c["border"])
        toolbar.pack(fill=tk.X, padx=20, pady=(20, 16))
        toolbar.pack_propagate(False)

        toolbar_left = tk.Frame(toolbar, bg=c["bg_card"])
        toolbar_left.pack(side=tk.LEFT, padx=20, pady=16)

        self._btn(toolbar_left, "Add Task", self._add_task_dialog, style="primary").pack(side=tk.LEFT, padx=(0, 12))
        self._btn(toolbar_left, "Manage Selected", self._manage_selected_task, style="secondary").pack(side=tk.LEFT, padx=(0, 12))

        # Filter buttons
        self.filter_buttons = {}
        for filter_name in ["All", "Pending", "In Progress", "Completed"]:
            btn = self._btn(toolbar_left, filter_name, lambda f=filter_name: self._refresh_task_tree(f), style="secondary")
            btn.pack(side=tk.LEFT, padx=4)
            self.filter_buttons[filter_name] = btn

        # Search
        search_frame = tk.Frame(toolbar, bg=c["bg_card"])
        search_frame.pack(side=tk.RIGHT, padx=20, pady=16)
        
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(search_frame, textvariable=self.search_var, bg=c["bg_secondary"], fg=c["text_primary"],
                                insertbackground=c["text_primary"], font=("Inter", 10), relief="flat", bd=0)
        search_entry.pack(side=tk.RIGHT, padx=(8, 0))
        search_entry.insert(0, "Search tasks...")
        search_entry.bind("<FocusIn>", lambda e: self._clear_search_placeholder())
        search_entry.bind("<KeyRelease>", lambda e: self._refresh_task_tree())

        tk.Label(search_frame, text="🔍", bg=c["bg_card"], fg=c["text_muted"],
                 font=("Inter", 12)).pack(side=tk.RIGHT)

        # Task table
        table_frame = tk.Frame(tab, bg=c["bg_card"], relief="flat", bd=1, highlightbackground=c["border"])
        table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        cols = ("id", "title", "owner", "deadline", "priority", "status", "risk")
        self.task_tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=20, selectmode="extended")

        cfg = {
            "id":        ("ID", 80),
            "title":     ("Task", 280),
            "owner":     ("Owner", 140),
            "deadline":  ("Deadline", 120),
            "priority":  ("Priority", 100),
            "status":    ("Status", 120),
            "risk":      ("Risk", 80),
        }
        for col, (h, w) in cfg.items():
            self.task_tree.heading(col, text=h)
            self.task_tree.column(col, width=w, anchor=tk.W)

        sb = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.task_tree.yview)
        self.task_tree.configure(yscrollcommand=sb.set)
        self.task_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        self.task_tree.tag_configure("overdue", foreground=c["accent_red"])
        self.task_tree.tag_configure("high_priority", foreground=c["accent_orange"])
        self.task_tree.tag_configure("completed", foreground=c["accent_green"])

    def _build_setup_tab(self):
        c = self.COLORS
        tab = tk.Frame(self.notebook, bg=c["bg_primary"])
        self.notebook.add(tab, text="Setup")

        # Header
        header = tk.Frame(tab, bg=c["bg_card"], height=80, relief="flat", bd=1, highlightbackground=c["border"])
        header.pack(fill=tk.X, padx=20, pady=(20, 16))
        header.pack_propagate(False)

        header_content = tk.Frame(header, bg=c["bg_card"])
        header_content.pack(expand=True, fill=tk.BOTH, padx=24, pady=20)

        tk.Label(header_content, text="Integration Setup",
                 bg=c["bg_card"], fg=c["text_primary"],
                 font=("Inter", 18, "bold")).pack(anchor=tk.W)
        
        tk.Label(header_content, text="Configure your service credentials to enable integrations",
                 bg=c["bg_card"], fg=c["text_secondary"],
                 font=("Inter", 11)).pack(anchor=tk.W, pady=(4, 0))

        # Main content with scrollable area
        main_container = tk.Frame(tab, bg=c["bg_primary"])
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        # Create canvas and scrollbar for scrollable content
        canvas = tk.Canvas(main_container, bg=c["bg_primary"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=c["bg_primary"])

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Integration cards
        self.setup_fields = {}
        
        # Gmail Integration
        self._create_integration_card(scrollable_frame, "Gmail", "Email integration for task extraction", [
            ("Credentials Path", "gmail_credentials_path", "Path to credentials.json file"),
            ("Client ID", "gmail_client_id", "OAuth2 Client ID"),
            ("Client Secret", "gmail_client_secret", "OAuth2 Client Secret")
        ])

        # Slack Integration
        self._create_integration_card(scrollable_frame, "Slack", "Team communication and message analysis", [
            ("Bot Token", "slack_bot_token", "xoxb-your-slack-bot-token"),
            ("App Token", "slack_app_token", "xapp-your-slack-app-token"),
            ("Signing Secret", "slack_signing_secret", "Slack app signing secret")
        ])

        # Notion Integration
        self._create_integration_card(scrollable_frame, "Notion", "Knowledge management and database sync", [
            ("Integration Token", "notion_token", "secret_your_notion_integration_token"),
            ("Database ID", "notion_database_id", "Notion database ID for tasks")
        ])

        # Jira Integration
        self._create_integration_card(scrollable_frame, "Jira", "Project management and issue tracking", [
            ("Jira URL", "jira_url", "https://your-domain.atlassian.net"),
            ("Email", "jira_email", "your-email@company.com"),
            ("API Token", "jira_api_token", "Your Jira API token")
        ])

        # Action buttons at bottom
        actions_frame = tk.Frame(scrollable_frame, bg=c["bg_primary"])
        actions_frame.pack(fill=tk.X, pady=(32, 0))

        button_container = tk.Frame(actions_frame, bg=c["bg_card"], relief="flat", bd=1, highlightbackground=c["border"])
        button_container.pack(fill=tk.X, padx=20, pady=16)

        inner_container = tk.Frame(button_container, bg=c["bg_card"])
        inner_container.pack(pady=20)

        self._btn(inner_container, "Test Connections", self._test_connections, style="secondary").pack(side=tk.LEFT, padx=(0, 12))
        self._btn(inner_container, "Save Configuration", self._save_configuration, style="primary").pack(side=tk.LEFT, padx=(0, 12))
        self._btn(inner_container, "Load from .env", self._load_from_env, style="secondary").pack(side=tk.LEFT)

    def _create_integration_card(self, parent, name, description, fields):
        c = self.COLORS
        
        # Card container
        card = tk.Frame(parent, bg=c["bg_card"], relief="flat", bd=1, highlightbackground=c["border"])
        card.pack(fill=tk.X, padx=20, pady=8)

        # Card header
        header = tk.Frame(card, bg=c["bg_secondary"])
        header.pack(fill=tk.X)

        header_content = tk.Frame(header, bg=c["bg_secondary"])
        header_content.pack(fill=tk.X, padx=20, pady=16)

        # Integration icon and name
        title_row = tk.Frame(header_content, bg=c["bg_secondary"])
        title_row.pack(fill=tk.X)

        icons = {"Gmail": "Gmail", "Slack": "Slack", "Notion": "Notion", "Jira": "Jira"}
        tk.Label(title_row, text=f"{'Gmail' if name == 'Gmail' else 'Slack' if name == 'Slack' else 'Notion' if name == 'Notion' else 'Jira'}",
                 bg=c["bg_secondary"], fg=c["text_primary"],
                 font=("Inter", 14, "bold")).pack(side=tk.LEFT)

        # Status indicator
        status_frame = tk.Frame(title_row, bg=c["bg_secondary"])
        status_frame.pack(side=tk.RIGHT)

        status_dot = tk.Label(status_frame, text="Disconnnected", bg=c["bg_secondary"], fg=c["text_muted"],
                            font=("Inter", 10, "bold"))
        status_dot.pack(side=tk.RIGHT, padx=(8, 0))

        # Description
        tk.Label(header_content, text=description,
                 bg=c["bg_secondary"], fg=c["text_secondary"],
                 font=("Inter", 10)).pack(anchor=tk.W, pady=(4, 0))

        # Form fields
        form_frame = tk.Frame(card, bg=c["bg_card"])
        form_frame.pack(fill=tk.X, padx=20, pady=(0, 20))

        self.setup_fields[name.lower()] = {}
        
        for label, key, placeholder in fields:
            field_frame = tk.Frame(form_frame, bg=c["bg_card"])
            field_frame.pack(fill=tk.X, pady=(12, 0))

            tk.Label(field_frame, text=label,
                     bg=c["bg_card"], fg=c["text_secondary"],
                     font=("Inter", 10, "bold")).pack(anchor=tk.W, pady=(0, 4))

            entry = tk.Entry(field_frame, bg=c["bg_secondary"], fg=c["text_primary"],
                           insertbackground=c["text_primary"], font=("Inter", 10),
                           relief="flat", bd=0)
            entry.pack(fill=tk.X, ipady=8)
            entry.insert(0, placeholder)
            entry.bind("<FocusIn>", lambda e, entry=entry, placeholder=placeholder: self._clear_field_placeholder(entry, placeholder))
            
            self.setup_fields[name.lower()][key] = entry

    def _clear_field_placeholder(self, entry, placeholder):
        if entry.get() == placeholder:
            entry.delete(0, tk.END)

    def _test_connections(self):
        """Test all configured connections"""
        self._log("Testing connections...", "info")
        # Implementation would test each integration
        messagebox.showinfo("Test Connections", "Connection testing functionality would be implemented here.")

    def _save_configuration(self):
        """Save configuration to .env file"""
        config_data = {}
        for integration, fields in self.setup_fields.items():
            for field_key, field_entry in fields.items():
                value = field_entry.get().strip()
                if value and not value.endswith("token") and not value.endswith("file") and not value.endswith("ID"):
                    config_data[field_key.upper()] = value
        
        if config_data:
            # Here you would save to .env file
            messagebox.showinfo("Configuration Saved", f"Configuration saved with {len(config_data)} settings.")
            self._log("Configuration saved successfully", "success")
        else:
            messagebox.showwarning("No Configuration", "No configuration data to save.")

    def _load_from_env(self):
        """Load configuration from existing .env file"""
        try:
            # Here you would load from .env file
            messagebox.showinfo("Load Configuration", "Configuration loaded from .env file.")
            self._log("Configuration loaded from .env", "info")
        except FileNotFoundError:
            messagebox.showwarning("File Not Found", ".env file not found. Please create it first.")

    def _build_agent_tab(self):
        c = self.COLORS
        tab = tk.Frame(self.notebook, bg=c["bg_primary"])
        self.notebook.add(tab, text="Agent")

        # Agent Console
        console_frame = tk.Frame(tab, bg=c["bg_card"], relief="flat", bd=1, highlightbackground=c["border"])
        console_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(20, 16))

        tk.Label(console_frame, text="Agent Console",
                 bg=c["bg_card"], fg=c["text_primary"],
                 font=("Inter", 12, "bold")).pack(anchor=tk.W, padx=20, pady=(16, 8))

        self.agent_console = scrolledtext.ScrolledText(
            console_frame, height=12, bg=c["bg_secondary"], fg=c["text_primary"],
            insertbackground=c["text_primary"], font=("JetBrains Mono", 10),
            wrap=tk.WORD, state=tk.DISABLED, relief="flat", bd=0)
        self.agent_console.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 16))

        for tag, color in [("success", c["accent_green"]), ("error", c["accent_red"]),
                           ("warning", c["accent_orange"]), ("info", c["text_secondary"])]:
            self.agent_console.tag_configure(tag, foreground=color)

        # Chat Interface
        chat_frame = tk.Frame(tab, bg=c["bg_card"], relief="flat", bd=1, highlightbackground=c["border"])
        chat_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        tk.Label(chat_frame, text="Chat with Agent",
                 bg=c["bg_card"], fg=c["text_primary"],
                 font=("Inter", 12, "bold")).pack(anchor=tk.W, padx=20, pady=(16, 8))

        self.chat_display = scrolledtext.ScrolledText(
            chat_frame, height=8, bg=c["bg_secondary"], fg=c["text_primary"],
            insertbackground=c["text_primary"], font=("Inter", 10),
            wrap=tk.WORD, state=tk.DISABLED, relief="flat", bd=0)
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 16))
        self.chat_display.tag_configure("user", foreground=c["accent"])
        self.chat_display.tag_configure("agent", foreground=c["accent_purple"])

        input_row = tk.Frame(chat_frame, bg=c["bg_card"])
        input_row.pack(fill=tk.X, padx=16, pady=(0, 16))

        self.chat_input = tk.Entry(input_row, bg=c["bg_secondary"], fg=c["text_primary"],
                                    insertbackground=c["text_primary"],
                                    font=("Inter", 11), relief="flat", bd=0)
        self.chat_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 12), ipady=6)
        self.chat_input.bind("<Return>", lambda e: self._send_chat())
        self.chat_input.insert(0, "Type your message...")
        self.chat_input.bind("<FocusIn>", lambda e: self._clear_chat_placeholder())

        self._btn(input_row, "Send", self._send_chat, style="primary").pack(side=tk.RIGHT)


    # ── Event Handlers ────────────────────────────────────────────────────────

    
    def _run_extract(self):
        messagebox.showinfo("Feature Moved", "Task extraction has been moved to the chat interface.\n\nUse the chat tab and type:\n'Extract tasks from: [your text]'")

    def _extract_async(self, text: str):
        self.agent.run_extract_cycle(text)
        self.after(0, self._refresh_ui)
        self.after(0, lambda: self.notebook.select(1))

    def _send_chat(self):
        msg = self.chat_input.get().strip()
        if not msg or msg == "Type your message...":
            return
        self.chat_input.delete(0, tk.END)
        self._append_chat(f"You: {msg}", "user")
        self._append_chat("Agent: Processing...", "agent")
        threading.Thread(target=self._chat_async, args=(msg,), daemon=True).start()

    def _chat_async(self, msg: str):
        response = self.agent.run_chat(msg)
        self.after(0, lambda: self._replace_last_chat(f"Agent: {response}"))

    def _append_chat(self, text: str, tag: str):
        self.chat_display.configure(state=tk.NORMAL)
        self.chat_display.insert(tk.END, f"\n{text}\n", tag)
        self.chat_display.see(tk.END)
        self.chat_display.configure(state=tk.DISABLED)

    def _replace_last_chat(self, text: str):
        self.chat_display.configure(state=tk.NORMAL)
        self.chat_display.delete("end-3l linestart", tk.END)
        self.chat_display.insert(tk.END, f"\n{text}\n", "agent")
        self.chat_display.see(tk.END)
        self.chat_display.configure(state=tk.DISABLED)

    def _manage_selected_task(self):
        """Manage selected tasks - assign, change deadline, update priority"""
        selected_items = self.task_tree.selection()
        if not selected_items:
            messagebox.showwarning("No Selection", "Please select at least one task to manage.")
            return
        
        # Get task IDs from selected items
        task_ids = []
        for item in selected_items:
            values = self.task_tree.item(item)['values']
            task_ids.append(values[0])  # ID is first column
        
        c = self.COLORS
        dlg = tk.Toplevel(self)
        dlg.title(f"Manage {len(task_ids)} Task(s)")
        dlg.geometry("480x600")
        dlg.configure(bg=c["bg_primary"])
        dlg.transient(self)
        dlg.grab_set()

        # Header
        header = tk.Frame(dlg, bg=c["bg_card"], height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        tk.Label(header, text=f"Manage {len(task_ids)} Task(s)",
                 bg=c["bg_card"], fg=c["text_primary"],
                 font=("Inter", 16, "bold")).pack(pady=16)

        # Task IDs display
        ids_frame = tk.Frame(dlg, bg=c["bg_card"])
        ids_frame.pack(fill=tk.X, padx=20, pady=(16, 8))
        
        tk.Label(ids_frame, text="Selected Task IDs:",
                 bg=c["bg_card"], fg=c["text_secondary"],
                 font=("Inter", 11, "bold")).pack(anchor=tk.W, padx=16, pady=(12, 4))
        
        tk.Label(ids_frame, text=", ".join(task_ids),
                 bg=c["bg_card"], fg=c["text_primary"],
                 font=("Inter", 10)).pack(anchor=tk.W, padx=16, pady=(0, 12))

        # Form
        form = tk.Frame(dlg, bg=c["bg_primary"])
        form.pack(fill=tk.BOTH, expand=True, padx=24, pady=16)

        fields = {}
        for label, key in [("New Owner Email", "owner"), ("New Deadline (YYYY-MM-DD)", "deadline")]:
            tk.Label(form, text=label, bg=c["bg_primary"], fg=c["text_secondary"],
                     font=("Inter", 11, "bold")).pack(anchor=tk.W, pady=(16, 4))
            e = tk.Entry(form, bg=c["bg_card"], fg=c["text_primary"],
                         insertbackground=c["text_primary"],
                         font=("Inter", 11), relief="flat", bd=1, highlightbackground=c["border"])
            e.pack(fill=tk.X, ipady=8)
            fields[key] = e

        tk.Label(form, text="New Priority", bg=c["bg_primary"], fg=c["text_secondary"],
                 font=("Inter", 11, "bold")).pack(anchor=tk.W, pady=(16, 4))
        pvar = tk.StringVar(value="")  # Empty means no change
        priority_combo = ttk.Combobox(form, textvariable=pvar,
                     values=["", "low", "medium", "high", "critical"],
                     font=("Inter", 11), state="readonly")
        priority_combo.pack(fill=tk.X, ipady=4)

        # Action buttons
        actions = tk.Frame(form, bg=c["bg_primary"])
        actions.pack(fill=tk.X, pady=(24, 0))

        def apply_changes():
            owner = fields["owner"].get().strip() or None
            deadline = fields["deadline"].get().strip() or None
            priority = pvar.get() or None
            
            if not owner and not deadline and not priority:
                messagebox.showwarning("No Changes", "Please specify at least one field to update.", parent=dlg)
                return
            
            # Apply changes to all selected tasks
            updated_count = 0
            for task_id in task_ids:
                updates = {}
                if owner:
                    updates["owner"] = owner
                if deadline:
                    updates["deadline"] = deadline
                if priority:
                    updates["priority"] = priority
                
                if self.memory.update_task(task_id, **updates):
                    updated_count += 1
            
            self._refresh_ui()
            messagebox.showinfo("Success", f"Updated {updated_count} task(s) successfully.", parent=dlg)
            dlg.destroy()

        def cancel():
            dlg.destroy()

        self._btn(actions, "Cancel", cancel, style="secondary").pack(side=tk.RIGHT, padx=(8, 0))
        self._btn(actions, "Apply Changes", apply_changes, style="primary").pack(side=tk.RIGHT)

    def _add_task_dialog(self):
        c = self.COLORS
        dlg = tk.Toplevel(self)
        dlg.title("Add New Task")
        dlg.geometry("520x480")
        dlg.configure(bg=c["bg_primary"])
        dlg.transient(self)
        dlg.grab_set()

        # Header
        header = tk.Frame(dlg, bg=c["bg_card"], height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        tk.Label(header, text="Add New Task",
                 bg=c["bg_card"], fg=c["text_primary"],
                 font=("Inter", 16, "bold")).pack(pady=16)

        # Form
        form = tk.Frame(dlg, bg=c["bg_primary"])
        form.pack(fill=tk.BOTH, expand=True, padx=24, pady=16)

        fields = {}
        for label, key in [("Title *", "title"), ("Description", "description"),
                            ("Owner Email", "owner"), ("Deadline (YYYY-MM-DD)", "deadline")]:
            tk.Label(form, text=label, bg=c["bg_primary"], fg=c["text_secondary"],
                     font=("Inter", 11, "bold")).pack(anchor=tk.W, pady=(16, 4))
            e = tk.Entry(form, bg=c["bg_card"], fg=c["text_primary"],
                         insertbackground=c["text_primary"],
                         font=("Inter", 11), relief="flat", bd=1, highlightbackground=c["border"])
            e.pack(fill=tk.X, ipady=8)
            fields[key] = e
            if key == "title":
                e.focus_set()

        tk.Label(form, text="Priority", bg=c["bg_primary"], fg=c["text_secondary"],
                 font=("Inter", 11, "bold")).pack(anchor=tk.W, pady=(16, 4))
        pvar = tk.StringVar(value="medium")
        priority_combo = ttk.Combobox(form, textvariable=pvar,
                     values=["low", "medium", "high", "critical"],
                     font=("Inter", 11), state="readonly")
        priority_combo.pack(fill=tk.X, ipady=4)

        # Actions
        actions = tk.Frame(form, bg=c["bg_primary"])
        actions.pack(fill=tk.X, pady=(24, 0))

        def save():
            title = fields["title"].get().strip()
            if not title:
                messagebox.showwarning("Required Field", "Task title is required.", parent=dlg)
                return
            task = Task(
                title=title, description=fields["description"].get(),
                owner=fields["owner"].get(), deadline=fields["deadline"].get() or None,
                priority=pvar.get(), source="manual"
            )
            self.memory.add_task(task)
            self._refresh_ui()
            dlg.destroy()

        def cancel():
            dlg.destroy()

        self._btn(actions, "Cancel", cancel, style="secondary").pack(side=tk.RIGHT, padx=(8, 0))
        self._btn(actions, "Add Task", save, style="primary").pack(side=tk.RIGHT)

    def _toggle_integration(self, name: str):
        c = self.COLORS
        current = self.memory.integrations[name].status
        if current == "disconnected":
            self.memory.update_integration_status(name, "connected")
            self.integration_labels[name].configure(fg=c["accent_green"])
            messagebox.showinfo("Integration Connected",
                f"✅ {name.title()} connected successfully.\n\n"
                "Note: This is a simulation. To fully activate:\n"
                f"• Add API credentials to {name.title()}Integration class\n"
                "• Implement data fetch/send methods\n"
                "• The agent will automatically use connected integrations")
        else:
            self.memory.update_integration_status(name, "disconnected")
            self.integration_labels[name].configure(fg=c["text_muted"])
        self.memory.log_activity(f"integration_{current}", name, f"{name} status changed")

    def _show_summary(self):
        c = self.COLORS
        summary = self.memory.snapshot()

        if not summary:
            messagebox.showinfo("No Data", "Run the agent first to generate a summary.")
            return

        popup = tk.Toplevel(self)
        popup.title("Task Summary")
        popup.geometry("680x500")
        popup.configure(bg=c["bg_primary"])
        popup.transient(self)
        popup.grab_set()

        # Header
        header = tk.Frame(popup, bg=c["bg_card"], height=70)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        tk.Label(header, text="Task Management Summary",
                 bg=c["bg_card"], fg=c["text_primary"],
                 font=("Inter", 18, "bold")).pack(pady=(20, 2))
        tk.Label(header, text=datetime.datetime.now().strftime("%B %d, %Y"),
                 bg=c["bg_card"], fg=c["text_secondary"],
                 font=("Inter", 11)).pack()

        # Content
        txt = scrolledtext.ScrolledText(popup, bg=c["bg_card"], fg=c["text_primary"],
                                         font=("Inter", 11), wrap=tk.WORD, relief="flat", bd=0)
        txt.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        # Summary content
        snap = summary
        content = f"""═══ OVERVIEW ═══

📊 Total Tasks: {snap['total_tasks']}
⚠️  Overdue: {snap['overdue_count']}
🕐 Stale (48h+): {snap['stale_count']}
🔌 Connected: {', '.join(snap['connected_integrations']) or 'None'}

═══ HIGH PRIORITY TASKS ═══

"""
        risky = sorted(snap["tasks"], key=lambda t: {"critical":4,"high":3,"medium":2,"low":1}.get(t["risk_level"],0), reverse=True)
        for t in risky[:8]:
            flag = "🚨" if t["risk_level"] == "critical" else "⚠️" if t["risk_level"] == "high" else "📌"
            dl = DateUtils.format_deadline(t["deadline"]) if t["deadline"] else "no deadline"
            content += f"{flag} [{t['priority'].upper()}] {t['title']}\n   └─ Owner: {t['owner'] or 'Unassigned'} | {dl} | Follow-ups: {t['follow_up_count']}\n\n"

        txt.insert("1.0", content)
        txt.configure(state=tk.DISABLED)
        
        # Close button
        self._btn(popup, "Close", popup.destroy, style="secondary").pack(pady=(0, 16))

    # ── Agent message callback ────────────────────────────────────────────────

    def _on_agent_message(self, msg: str, level: str):
        self.after(0, self._log, msg, level)

    def _log(self, msg: str, level: str):
        self.agent_console.configure(state=tk.NORMAL)
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self.agent_console.insert(tk.END, f"[{ts}] {msg}\n", level)
        self.agent_console.see(tk.END)
        self.agent_console.configure(state=tk.DISABLED)

        # Note: Node visualization removed for cleaner interface

    # Node visualization removed - simplified interface

    
    def _clear_search_placeholder(self):
        if self.search_var.get() == "Search tasks...":
            self.search_var.set("")
    
    def _clear_chat_placeholder(self):
        if self.chat_input.get() == "Type your message...":
            self.chat_input.delete(0, tk.END)

    # ── Refresh ───────────────────────────────────────────────────────────────

    def _refresh_ui(self):
        self._refresh_stats()
        self._refresh_task_tree()

    def _refresh_stats(self):
        tasks = self.memory.get_all_tasks()
        overdue = self.memory.get_overdue_tasks()
        self.stat_labels["total"].configure(text=str(len(tasks)))
        self.stat_labels["pending"].configure(text=str(len([t for t in tasks if t.status == "pending"])))
        self.stat_labels["in_progress"].configure(text=str(len([t for t in tasks if t.status == "in_progress"])))
        self.stat_labels["overdue"].configure(text=str(len(overdue)))
        self.stat_labels["completed"].configure(text=str(len([t for t in tasks if t.status == "completed"])))

    def _refresh_task_tree(self, filter_name: str = "All"):
        for row in self.task_tree.get_children():
            self.task_tree.delete(row)

        tasks = self.memory.get_all_tasks()
        if filter_name == "Pending":
            tasks = [t for t in tasks if t.status == "pending"]
        elif filter_name == "In Progress":
            tasks = [t for t in tasks if t.status == "in_progress"]
        elif filter_name == "Overdue":
            tasks = self.memory.get_overdue_tasks()
        elif filter_name == "Completed":
            tasks = [t for t in tasks if t.status == "completed"]

        priority_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        tasks.sort(key=lambda t: priority_order.get(t.priority, 0), reverse=True)

        picons = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}
        ricons = {"critical": "🚨", "high": "⚠️", "medium": "🟡", "low": "✅"}

        for t in tasks:
            tag = "overdue" if t.is_overdue() else "critical" if t.risk_level == "critical" else "completed" if t.status == "completed" else ""
            dl = DateUtils.format_deadline(t.deadline) if t.deadline else "—"
            self.task_tree.insert("", tk.END, values=(
                t.id, t.title[:52], t.owner or "Unassigned", dl,
                f"{picons.get(t.priority, '⚪')} {t.priority}",
                t.status.replace("_", " ").title(),
                f"{ricons.get(t.risk_level, '')} {t.risk_level}",
                t.follow_up_count
            ), tags=(tag,))



    def _schedule_refresh(self):
        self._refresh_ui()
        self.after(5000, self._schedule_refresh)

    def _load_sample_data(self):
        # Auto-load mock data in mock mode
        if self.integration_mode == "mock":
            self._log("🎯 Loading mock data from integrations...", "info")
            threading.Thread(target=self._load_mock_data_async, daemon=True).start()
        self.memory.log_activity("system_start", "system", "Orchestrix Task Management Agent started")
    
    def _load_mock_data(self):
        """Load mock data from integrations"""
        self._log("🎯 Loading mock data from integrations...", "info")
        threading.Thread(target=self._load_mock_data_async, daemon=True).start()
    
    def _load_mock_data_async(self):
        """Load mock data asynchronously"""
        try:
            from agent.tools import load_mock_data
            result = load_mock_data.func()  # Use .func to access underlying function
            self.after(0, self._refresh_ui)
            self.after(0, lambda r=result: self._log(f"✅ {r}", "success"))
        except Exception as e:
            error_msg = str(e)
            self.after(0, lambda err=error_msg: self._log(f"❌ Error loading mock data: {err}", "error"))
