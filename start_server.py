#!/usr/bin/env python3
"""
LawVriksh Server Startup Script
==============================

This script starts the LawVriksh FastAPI server with integrated background email processing.

Features:
- Starts FastAPI server with uvicorn
- Automatically starts background email processor
- Processes emails every 60 seconds
- Graceful shutdown handling
- Production-ready configuration

Usage:
    python start_server.py [--host HOST] [--port PORT] [--reload]
"""

import sys
import os
import argparse
import logging
from datetime import datetime
import pytz

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# IST timezone
IST = pytz.timezone('Asia/Kolkata')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main startup function."""
    parser = argparse.ArgumentParser(description='LawVriksh Server with Background Email Processing')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=8000, help='Port to bind to (default: 8000)')
    parser.add_argument('--reload', action='store_true', help='Enable auto-reload for development')
    parser.add_argument('--workers', type=int, default=1, help='Number of worker processes (default: 1)')
    
    args = parser.parse_args()
    
    print("🚀 LawVriksh Server Startup")
    print("=" * 60)
    print(f"🕐 Starting at: {datetime.now(IST)}")
    print(f"🌐 Host: {args.host}")
    print(f"🔌 Port: {args.port}")
    print(f"🔄 Reload: {args.reload}")
    print(f"👥 Workers: {args.workers}")
    print("=" * 60)
    
    print("📧 Background Email Processing: ENABLED")
    print("   • Checks for pending emails every 60 seconds")
    print("   • Processes welcome emails immediately")
    print("   • Maintains campaign email schedules")
    print("   • Automatic startup/shutdown with server")
    print()
    
    try:
        import uvicorn
        
        # Configure uvicorn
        config = {
            "app": "app.main:app",
            "host": args.host,
            "port": args.port,
            "reload": args.reload,
            "workers": args.workers if not args.reload else 1,  # Reload mode requires single worker
            "log_level": "info",
            "access_log": True,
        }
        
        print("🎯 Starting FastAPI server with integrated email processing...")
        print("💡 The background email processor will start automatically")
        print("💡 Monitor the logs for email processing activity")
        print("💡 Press Ctrl+C to stop the server and email processor")
        print()
        
        # Start the server
        uvicorn.run(**config)
        
    except KeyboardInterrupt:
        print("\n🛑 Server shutdown requested")
        print("✅ Background email processor will stop automatically")
        
    except Exception as e:
        logger.error(f"❌ Server startup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
