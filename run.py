#!/usr/bin/env python3
"""
Fantasy Optimize - Quick start script
Run the Fantasy Football analysis server
"""
import subprocess
import sys
import os

def main():
    """Start the Fantasy Optimize server"""
    print("🏈 Starting Fantasy Optimize Server...")
    print("📊 Server will be available at: http://localhost:8000")
    print("🌐 Frontend available at: http://localhost:5173")
    print("=" * 50)
    
    try:
        # Run the server
        subprocess.run([sys.executable, "server.py"], check=True)
    except KeyboardInterrupt:
        print("\n👋 Fantasy Optimize server stopped.")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()