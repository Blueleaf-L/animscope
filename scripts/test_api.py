"""Quick API smoke test."""
import urllib.request
import json

BASE = "http://127.0.0.1:8000"

def get(path):
    r = urllib.request.urlopen(f"{BASE}{path}")
    return json.loads(r.read())

def test(name, path, check=None):
    try:
        data = get(path)
        if check:
            check(data)
        print(f"  [OK] {name}")
        return data
    except Exception as e:
        print(f"  [FAIL] {name}: {e}")
        return None

print("=== API Smoke Tests ===\n")

# 1. Health
test("Health check", "/api/health",
     lambda d: d["status"] == "ok" or print(f"    status={d['status']}"))

# 2. Overview
def check_overview(d):
    s = d["stats"]
    print(f"    companies={s['total_companies']}, works={s['total_works']}, avg={s['avg_score']}")
    assert s["total_companies"] == 72
    assert s["total_works"] >= 585
test("Overview", "/api/v1/analysis/overview", check_overview)

# 3. Companies list
def check_companies(d):
    print(f"    total={d['total']}, first={d['items'][0]['name']}")
    assert d["total"] == 72
test("Companies list", "/api/v1/companies?size=3", check_companies)

# 4. Company detail
def check_detail(d):
    print(f"    name={d['name']}, works={d['works_count']}, avg={d['avg_score']}")
    assert "works" in d
test("Company detail", "/api/v1/companies/1", check_detail)

# 5. Works search
def check_works(d):
    print(f"    total={d['total']}, first={d['items'][0]['name']}")
    assert d["total"] >= 580
test("Works search", "/api/v1/works?size=3", check_works)

# 6. Rankings
def check_rankings(d):
    print(f"    #1: {d['items'][0]['company_name']} (score={d['items'][0]['avg_score']})")
    assert len(d["items"]) > 0
test("Rankings (recommended)", "/api/v1/analysis/rankings?tab=recommended", check_rankings)

# 7. Rankings trash
def check_trash(d):
    print(f"    top trash: {d['items'][0]['company_name']} ({d['items'][0]['trash_count']} trash)")
test("Rankings (trash)", "/api/v1/analysis/rankings?tab=trash", check_trash)

# 8. Trends
def check_trends(d):
    print(f"    {len(d['by_type'])} years, {len(d['companies'])} companies in heatmap")
test("Trends", "/api/v1/analysis/trends", check_trends)

# 9. Compare
def check_compare(d):
    print(f"    {d['companies'][0]['name']} vs {d['companies'][1]['name']}")
    assert len(d["companies"]) == 2
test("Compare", "/api/v1/analysis/compare?ids=1,2", check_compare)

# 10. Diff
def check_diff(d):
    print(f"    Cohen's d={d['cohens_d']}, dims={len(d['dimensions'])}")
test("Diff", "/api/v1/analysis/compare/diff?a=1&b=2", check_diff)

# 11. Insights
def check_insights(d):
    print(f"    top={len(d['top_companies'])}, risks={len(d['risk_alerts'])}")
test("Insights", "/api/v1/analysis/insights", check_insights)

def get_raw(path):
    """Get raw binary response (for charts)."""
    r = urllib.request.urlopen(f"{BASE}{path}")
    data = r.read()
    return data, r.headers.get_content_type()

# 12. Charts (binary responses)
def test_chart(name, path):
    try:
        data, ct = get_raw(path)
        print(f"  [OK] {name} ({ct}, {len(data)} bytes)")
    except Exception as e:
        print(f"  [FAIL] {name}: {e}")

test("Chart: rating-dist", "/api/v1/analysis/overview")
test_chart("Chart: rating-dist PNG", "/api/v1/charts/rating-distribution")
test_chart("Chart: boxplot PNG", "/api/v1/charts/boxplot")
test_chart("Chart: heatmap PNG", "/api/v1/charts/heatmap?top_n=10")
test_chart("Chart: radar SVG", "/api/v1/charts/company-radar?id=1")
test_chart("Chart: dashboard HTML", "/api/v1/charts/industry-dashboard")
test_chart("Chart: PDF report", "/api/v1/charts/report?format=pdf")

print("\n=== All tests completed ===")
