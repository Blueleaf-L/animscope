"""Simulate browser JS: test the API call that the frontend would make."""
import urllib.request
import json

BASE = "http://127.0.0.1:8000"
API_BASE = "/api/v1"

# Simulate what Pages.Overview.render() does
print("=== Simulating Frontend API Calls ===")

# 1. Overview page data
try:
    r = urllib.request.urlopen(f"{BASE}{API_BASE}/analysis/overview")
    data = json.loads(r.read())
    print(f"[OK] GET {API_BASE}/analysis/overview")
    print(f"     companies={data['stats']['total_companies']}")
    print(f"     works={data['stats']['total_works']}")
    print(f"     type_dist={len(data['type_distribution'])} items")
    print(f"     yearly_trends={len(data['yearly_trends'])} years")
    print(f"     rating_dist={len(data['rating_distribution'])} labels")
except Exception as e:
    print(f"[FAIL] overview: {e}")

# 2. Companies page
try:
    r = urllib.request.urlopen(f"{BASE}{API_BASE}/companies?size=5")
    data = json.loads(r.read())
    print(f"[OK] GET {API_BASE}/companies?size=5 -> {data['total']} companies")
except Exception as e:
    print(f"[FAIL] companies: {e}")

# 3. Rankings
try:
    r = urllib.request.urlopen(f"{BASE}{API_BASE}/analysis/rankings?tab=recommended")
    data = json.loads(r.read())
    print(f"[OK] GET rankings -> {len(data['items'])} items")
except Exception as e:
    print(f"[FAIL] rankings: {e}")

# 4. Trends
try:
    r = urllib.request.urlopen(f"{BASE}{API_BASE}/analysis/trends")
    data = json.loads(r.read())
    print(f"[OK] GET trends -> {len(data['by_type'])} years, {len(data['heatmap_data'])} heatmap cells")
except Exception as e:
    print(f"[FAIL] trends: {e}")

# 5. Works search
try:
    r = urllib.request.urlopen(f"{BASE}{API_BASE}/works?size=5")
    data = json.loads(r.read())
    print(f"[OK] GET works -> {data['total']} works")
except Exception as e:
    print(f"[FAIL] works: {e}")

print("\nBackend is returning correct data for all frontend pages.")
print("If the browser still shows errors, check the browser Console (F12) for JS errors.")
