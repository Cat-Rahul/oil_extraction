#!/usr/bin/env python3
"""
Startup script for Valve Datasheet Automation API.

Usage:
    python run_api.py
    python run_api.py --port 8000
    python run_api.py --host 0.0.0.0 --port 8080
"""

import argparse
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))


def main():
    parser = argparse.ArgumentParser(
        description="Run Valve Datasheet Automation API Server"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to (default: 8000)"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        default=True,
        help="Enable auto-reload on code changes (default: True)"
    )
    parser.add_argument(
        "--no-reload",
        action="store_true",
        help="Disable auto-reload"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of worker processes (default: 1)"
    )

    args = parser.parse_args()

    # Import uvicorn here to avoid import issues if not installed
    try:
        import uvicorn
    except ImportError:
        print("Error: uvicorn is not installed.")
        print("Install it with: pip install uvicorn[standard]")
        sys.exit(1)

    reload_enabled = args.reload and not args.no_reload

    print("=" * 60)
    print("  Valve Datasheet Automation API Server")
    print("=" * 60)
    print(f"  Host:    {args.host}")
    print(f"  Port:    {args.port}")
    print(f"  Reload:  {reload_enabled}")
    print(f"  Workers: {args.workers}")
    print("=" * 60)
    print()
    print(f"  API Docs:    http://localhost:{args.port}/docs")
    print(f"  ReDoc:       http://localhost:{args.port}/redoc")
    print(f"  Health:      http://localhost:{args.port}/api/health")
    print()
    print("=" * 60)

    uvicorn.run(
        "valve_datasheet_automation.api.main:app",
        host=args.host,
        port=args.port,
        reload=reload_enabled,
        workers=args.workers if not reload_enabled else 1,
    )


if __name__ == "__main__":
    main()
