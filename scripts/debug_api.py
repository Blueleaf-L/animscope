"""Debug: check if catch-all route intercepts API calls."""
import urllib.request
import json

BASE = "http://127.0.0.1:8000"

# Test API directly
tests = [
    "/api/health",
    "/api/v1/analysis/overview",
    "/api/v1/companies?size=2",
]

for path in tests:
    try:
        r = urllib.request.urlopen(f"{BASE}{path}")
        ct = r.headers.get_content_type()
        data = r.read()
        if "json" in ct:
            parsed = json.loads(data)
            print(f"  [OK] {path} -> JSON ({len(data)} bytes)")
            if "detail" in parsed:
                print(f"       WARNING: Got error response: {parsed['detail']}")
        else:
            print(f"  [WARN] {path} -> {ct} ({len(data)} bytes)")
    except Exception as e:
        print(f"  [FAIL] {path}: {e}")
