#!/usr/bin/env python3
"""
Start the server and create a public tunnel.
Supports multiple tunnel backends:
  - serveo.net   (default, no registration, free)
  - localhost.run (backup, no registration, free)

Usage:
  python scripts/public_server.py
  python scripts/public_server.py --port 8000 --backend serveo
"""

import subprocess
import sys
import time
import os
import signal
import threading

PORT = 8000
BACKEND = "serveo"


def start_tunnel_serveo():
    """Use serveo.net SSH tunnel (no registration needed)."""
    cmd = [
        "ssh", "-o", "StrictHostKeyChecking=no",
        "-o", "ServerAliveInterval=60",
        "-o", "ExitOnForwardFailure=yes",
        "-R", f"80:localhost:{PORT}",
        "serveo.net",
    ]
    print(f"[*] Starting serveo.net tunnel on port {PORT}...")
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    url = None
    for line in proc.stdout:
        line = line.strip()
        print(f"    {line}")
        if "https://" in line and "serveo" in line:
            # Extract URL
            import re
            match = re.search(r'https://[^\s]+', line)
            if match:
                url = match.group(0)
                print(f"\n{'='*60}")
                print(f"  PUBLIC URL: {url}")
                print(f"{'='*60}")
                print(f"\n  Share this URL to access the site from anywhere.")
                print(f"  Press Ctrl+C to stop.\n")
                break

    if not url:
        # Maybe the URL is in the first few lines
        print("[!] Could not detect URL. Check the output above.")
        print("[*] Tunnel is still running. Try opening the SSH output URL.")

    return proc


def start_tunnel_localhost_run():
    """Use localhost.run SSH tunnel (no registration needed)."""
    cmd = [
        "ssh", "-o", "StrictHostKeyChecking=no",
        "-o", "ServerAliveInterval=60",
        "-R", f"80:localhost:{PORT}",
        "nokey@localhost.run",
    ]
    print(f"[*] Starting localhost.run tunnel on port {PORT}...")
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    url = None
    for line in proc.stdout:
        line = line.strip()
        print(f"    {line}")
        if "https://" in line:
            import re
            match = re.search(r'https://[^\s]+', line)
            if match:
                url = match.group(0)
                print(f"\n{'='*60}")
                print(f"  PUBLIC URL: {url}")
                print(f"{'='*60}")
                print(f"\n  Press Ctrl+C to stop.\n")
                break

    if not url:
        print("[!] Tunnel is running but URL not auto-detected. Check output above.")

    return proc


def main():
    port = PORT
    backend = BACKEND

    # Parse args
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--port" and i + 1 < len(args):
            port = int(args[i + 1])
            i += 2
        elif args[i] == "--backend" and i + 1 < len(args):
            backend = args[i + 1]
            i += 2
        else:
            i += 1

    print(f"\n{'='*60}")
    print(f"  Public Server Launcher")
    print(f"  Port: {port}  |  Backend: {backend}")
    print(f"{'='*60}\n")

    # Check if backend is running
    import urllib.request
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{port}/api/health", timeout=2)
        print(f"[OK] Backend is running on port {port}")
    except Exception:
        print(f"[!] Backend NOT running on port {port}!")
        print(f"    Start it first: cd backend && python -m uvicorn app.main:app --port {port}")
        sys.exit(1)

    # Start tunnel
    if backend == "serveo":
        proc = start_tunnel_serveo()
    elif backend == "localhostrun":
        proc = start_tunnel_localhost_run()
    else:
        print(f"Unknown backend: {backend}. Use 'serveo' or 'localhostrun'")
        sys.exit(1)

    # Keep running
    try:
        proc.wait()
    except KeyboardInterrupt:
        print("\n[*] Shutting down...")
        proc.terminate()
        proc.wait()
        print("[OK] Tunnel closed.")


if __name__ == "__main__":
    main()
