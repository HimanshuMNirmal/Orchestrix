#!/usr/bin/env python3
"""
Desktop Agent OS - LangGraph Edition
A production-style MVP using LangGraph for agent orchestration
Modular architecture with separate components
"""

# ================== IMPORTS ==================
import sys
import os
import argparse
import signal
import atexit

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.main_window import DesktopAgentOS


# ================== CLEANUP ==================

app_instance = None

def force_cleanup():
    """Force cleanup of all Python processes and tkinter windows"""
    global app_instance
    
    # Kill any remaining Python processes
    os.system("pkill -f python 2>/dev/null")
    
    # Force exit if still running
    os._exit(0)

def signal_handler(signum, frame):
    """Handle termination signals"""
    print(f"\nReceived signal {signum}, terminating...")
    force_cleanup()

# ================== MAIN ==================

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Desktop Agent OS - LangGraph Edition')
    parser.add_argument('--integration-mode', 
                       choices=['real', 'mock'], 
                       default='mock',
                       help='Integration mode: real (uses actual APIs) or mock (uses simulated responses)')
    
    args = parser.parse_args()
    
    # Register signal handlers for force cleanup
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    atexit.register(force_cleanup)
    
    print("=" * 60)
    print("  Desktop Agent OS  —  LangGraph Edition")
    print("=" * 60)
    print()
    print("  Graph topology:")
    print("  [START] → intake")
    print("              ├─ extract → tools ↔ extract → summarize → END")
    print("              ├─ monitor → tools ↔ monitor → summarize → END")
    print("              └─ chat    → tools ↔ chat               → END")
    print()
    print("  Modules:")
    print("  - models/     : Data models and memory store")
    print("  - integrations/: External service integrations (mode: {})".format(args.integration_mode))
    print("  - agent/      : LangGraph components (nodes, tools, runner)")
    print("  - ui/         : User interface components")
    print()
    print("  Nodes    : intake, extract, monitor, chat, tools, summarize")
    print("  State    : AgentState (TypedDict) with add_messages reducer")
    print("  Memory   : MemorySaver checkpointer (thread_id persistent)")
    print("  Tools    : 12 LangChain tools bound to Ollama llama3.2:3b")
    print()
    print("  Install:  pip install langgraph langchain-anthropic")
    print()
    print("  Integration Mode: {}".format(args.integration_mode.upper()))
    if args.integration_mode == 'real':
        print("  ¡ Real API connections - ensure credentials are configured")
    else:
        print("  ¡ Mock responses - no external API calls")
    print("=" * 60)

    app = DesktopAgentOS(integration_mode=args.integration_mode)
    app_instance = app
    app.mainloop()
