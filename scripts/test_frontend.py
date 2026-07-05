"""Test frontend serving through backend."""
import urllib.request

BASE = "http://127.0.0.1:8000"

print("=== Frontend Tests ===")
for path in ["/", "/js/config.js", "/css/style.css", "/overview", "/js/pages/overview.js"]:
    try:
        r = urllib.request.urlopen(f"{BASE}{path}")
        content = r.read()
        print(f"  [OK] {path} -> {r.status} ({len(content)} bytes)")
    except Exception as e:
        print(f"  [FAIL] {path}: {e}")

print("Done.")
