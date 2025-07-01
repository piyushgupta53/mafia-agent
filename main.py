#!/usr/bin/env python3
"""
Main entry point for the Mafia Multi-Agent Game
Run this file to start the web interface and game server
"""

import sys
import os
import asyncio
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Import the Flask application
from frontend.app import app, socketio
from config import FLASK_CONFIG


def main():
    """Main function to start the Mafia game server"""

    print("🎭 Mafia Multi-Agent Game")
    print("=" * 50)
    print(f"🚀 Starting server on http://{FLASK_CONFIG['host']}:{FLASK_CONFIG['port']}")
    print("🔧 Make sure you have set your DEEPSEEK_API_KEY in the environment")
    print("📖 Open your browser to the URL above to start playing!")
    print("=" * 50)

    try:
        # Start the Flask-SocketIO server
        socketio.run(
            app,
            host=FLASK_CONFIG["host"],
            port=FLASK_CONFIG["port"],
            debug=FLASK_CONFIG["debug"],
            use_reloader=False,  # Disable reloader to prevent issues with threading
        )
    except KeyboardInterrupt:
        print("\n🛑 Game server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
