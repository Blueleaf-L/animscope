"""
Generate all static data files for GitHub Pages deployment.
Loads JSON data -> computes everything -> outputs flat JSON files.

Output:
  data/static/
    overview.json       — homepage stats + distributions
    companies.json      — all companies with works
    rankings_*.json     — rankings by tab
    trends.json         — yearly trends + heatmap
    charts/             — pre-rendered chart images

Usage: python scripts/build_static.py
"""

import json
import os
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy import stats as scipy_stats

# ── Load source data ──
ROOT = Path(__file__).parent.parent
with open(ROOT / "data" / "companies.json", "r", encoding="utf-8") as f:
    companies_data = json.load(f)
with open(ROOT / "data" / "works.json", "r", encoding="utf-8") as f:
    works_data = json.load(f)

companies = companies_data["companies"]
works = works_data["works"]

# Build a company-id map (use index as ID)
company_id_map = {c["name"]: i + 1 for i, c in enumerate(companies)}
for i, c in enumerate(companies):
    c["id"] = i + 1

# Attach company_id, company_name, work_type to each work
for w in works:
    cname = w["company_name"]
    w["company_id"] = company_id_map.get(cname, 0)
    # Use per-work type if available, otherwise fall back to company type
    if "work_type" not in w:
        comp = next((c for c in companies if c["name"] == cname), None)
        w["work_type"] = comp["type"] if comp and comp["type"] != "混合型" else "3D"
    # Ensure company_type alias for compatibility
    w["company_type"] = w.get("work_type", "3D")

# Update company type counts
type_counts = {"2D": 0, "3D": 0, "三渲二": 0, "混合型": 0}
for c in companies:
    tp = c.get("type", "3D")
    type_counts[tp] = type_counts.get(tp, 0) + 1
print(f"Company types: {dict(type_counts)}")

OUT = ROOT / "frontend" / "data" / "static"
os.makedirs(OUT, exist_ok=True)
os.makedirs(OUT / "charts", exist_ok=True)

print(f"Loaded {len(companies)} companies, {len(works)} works\n")

# ═══════════════════════════════════════════════════════
# 1. Overview
# ═══════════════════════════════════════════════════════
print("[1/6] Generating overview.json...")

scored = [w for w in works if w["rating_score"] is not None]
scores = [w["rating_score"] for w in scored]
avg_score = round(float(np.mean(scores)), 2) if scores else 0.0

rec_count = sum(1 for w in scored if w["rating_label"] == "年度推荐")
good_count = sum(1 for w in scored if w["rating_label"] in ("佳作", "还行"))
trash_count = sum(1 for w in scored if w["rating_label"] in ("拉了", "史"))

stats = {
    "total_companies": len(companies),
    "total_works": len(works),
    "avg_score": avg_score,
    "recommended_count": rec_count,
    "good_count": good_count,
    "trash_count": trash_count,
}

# Type distribution
type_data = defaultdict(lambda: {"count": 0, "scores": []})
for w in scored:
    ct = w.get("company_type", "3D")
    type_data[ct]["count"] += 1
    type_data[ct]["scores"].append(w["rating_score"])
type_distribution = [
    {"type": t, "count": d["count"], "avg_score": round(float(np.mean(d["scores"])), 2)}
    for t, d in type_data.items()
]

# Yearly trends
year_data = defaultdict(lambda: {"count": 0, "scores": []})
for w in scored:
    y = w.get("year")
    if y:
        year_data[y]["count"] += 1
        year_data[y]["scores"].append(w["rating_score"])
yearly_trends = [
    {"year": y, "count": d["count"], "avg_score": round(float(np.mean(d["scores"])), 2)}
    for y, d in sorted(year_data.items())
]

# Rating distribution
RATING_ORDER = ["年度推荐", "佳作", "还行", "能看", "不明", "拉了", "史"]
rating_counts = defaultdict(int)
for w in works:
    if w.get("rating_label"):
        rating_counts[w["rating_label"]] += 1
total_labeled = sum(rating_counts.values()) or 1
rating_distribution = [
    {"label": l, "count": rating_counts.get(l, 0), "percentage": round(rating_counts.get(l, 0) / total_labeled * 100, 1)}
    for l in RATING_ORDER
]

# Diagnostics
diagnostics = []
if avg_score <= 0:
    diagnostics.append("行业平均评分为负值，整体作品质量有待提升。")
if trash_count > rec_count:
    diagnostics.append(f"翻车作品({trash_count})多于推荐作品({rec_count})，行业精品率偏低。")
if len(companies) > 0 and len(works) / len(companies) < 5:
    diagnostics.append("平均每家公司作品数量偏少，行业集中度或作品收录完整性需关注。")
recent_3 = yearly_trends[-3:] if len(yearly_trends) >= 3 else yearly_trends
older_3 = yearly_trends[:3] if len(yearly_trends) >= 3 else yearly_trends
if len(recent_3) >= 2 and len(older_3) >= 2:
    ra = np.mean([t["avg_score"] for t in recent_3])
    oa = np.mean([t["avg_score"] for t in older_3])
    if ra > oa:
        diagnostics.append("近年作品质量呈上升趋势，行业发展向好。")
    elif ra < oa:
        diagnostics.append("近年作品质量有所下滑，需关注行业生态。")

overview = {
    "stats": stats,
    "type_distribution": type_distribution,
    "yearly_trends": yearly_trends,
    "rating_distribution": rating_distribution,
    "diagnostics": diagnostics,
}
with open(OUT / "overview.json", "w", encoding="utf-8") as f:
    json.dump(overview, f, ensure_ascii=False, indent=2)
print(f"  -> {OUT / 'overview.json'}")

# ═══════════════════════════════════════════════════════
# 2. Companies (with all works embedded)
# ═══════════════════════════════════════════════════════
print("[2/6] Generating companies.json...")

comp_works = defaultdict(list)
for w in works:
    comp_works[w["company_id"]].append(w)

all_companies = []
for c in companies:
    cw = comp_works.get(c["id"], [])
    # Compute stats
    cs = [w["rating_score"] for w in cw if w["rating_score"] is not None]
    all_companies.append({
        "id": c["id"],
        "name": c["name"],
        "type": c["type"],
        "works_count": len(cw),
        "avg_score": round(float(np.mean(cs)), 2) if cs else None,
        "works": sorted(cw, key=lambda x: (x.get("year") or 0), reverse=True),
    })

with open(OUT / "companies_full.json", "w", encoding="utf-8") as f:
    json.dump(all_companies, f, ensure_ascii=False, indent=2)
print(f"  -> {OUT / 'companies_full.json'}")

# Also output a lite version without works for listing
companies_lite = [
    {"id": c["id"], "name": c["name"], "type": c["type"],
     "works_count": c["works_count"], "avg_score": c["avg_score"]}
    for c in all_companies
]
with open(OUT / "companies_lite.json", "w", encoding="utf-8") as f:
    json.dump(companies_lite, f, ensure_ascii=False, indent=2)
print(f"  -> {OUT / 'companies_lite.json'}")

# ═══════════════════════════════════════════════════════
# 3. Rankings
# ═══════════════════════════════════════════════════════
print("[3/6] Generating rankings_*.json...")

# Compute ranking data
ranking_items = []
for c in all_companies:
    cw = comp_works.get(c["id"], [])
    if not cw:
        continue
    rec = sum(1 for w in cw if w.get("rating_label") == "年度推荐")
    trash = sum(1 for w in cw if w.get("rating_label") in ("拉了", "史"))
    cs = [w["rating_score"] for w in cw if w["rating_score"] is not None]
    avg = float(np.mean(cs)) if cs else 0.0
    ranking_items.append({
        "company_id": c["id"], "company_name": c["name"], "company_type": c["type"],
        "works_count": len(cw), "avg_score": round(avg, 2),
        "recommended_count": rec, "trash_count": trash,
    })

# Z-scores
if ranking_items:
    scores_arr = np.array([r["avg_score"] for r in ranking_items])
    mean_s, std_s = np.mean(scores_arr), np.std(scores_arr) if np.std(scores_arr) > 0 else 1
    for r in ranking_items:
        r["z_score"] = round((r["avg_score"] - mean_s) / std_s, 2)

for tab, sort_key, reverse in [
    ("recommended", lambda x: (x["recommended_count"], x["avg_score"]), True),
    ("good", lambda x: (x["avg_score"],), True),
    ("trash", lambda x: (x["trash_count"],), True),
]:
    items = sorted(ranking_items, key=sort_key, reverse=reverse)
    for i, r in enumerate(items):
        r["rank"] = i + 1
    path = OUT / f"rankings_{tab}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"items": items, "tab": tab}, f, ensure_ascii=False, indent=2)
    print(f"  -> {path}")

# ═══════════════════════════════════════════════════════
# 4. Trends
# ═══════════════════════════════════════════════════════
print("[4/6] Generating trends.json...")

# By type per year
year_type = defaultdict(lambda: {"2D": [], "3D": [], "三渲二": []})
for w in scored:
    y = w.get("year")
    ct = w.get("company_type", "3D")
    if y and ct in year_type[0]:
        year_type[y][ct].append(w["rating_score"])

by_type = []
for y in sorted(year_type.keys()):
    d = year_type[y]
    item = {"year": y}
    for tkey, tlabel in [("2D", "type_2d"), ("3D", "type_3d"), ("三渲二", "type_hybrid")]:
        ss = d[tkey]
        item[f"{tlabel}_count"] = len(ss)
        item[f"{tlabel}_avg"] = round(float(np.mean(ss)), 2) if ss else 0
    all_s = [s for ss in d.values() for s in ss]
    item["total_count"] = len(all_s)
    item["total_avg"] = round(float(np.mean(all_s)), 2) if all_s else 0
    by_type.append(item)

# Heatmap
comp_year_map = defaultdict(lambda: defaultdict(list))
comp_name_map = {}
for w in scored:
    y = w.get("year")
    if y:
        comp_year_map[w["company_id"]][y].append(w["rating_score"])
        comp_name_map[w["company_id"]] = w["company_name"]

comp_total = {cid: sum(len(v) for v in years.values()) for cid, years in comp_year_map.items()}
top_ids = {cid for cid, _ in sorted(comp_total.items(), key=lambda x: x[1], reverse=True)[:20]}
all_years = sorted(set(y for cid in top_ids for y in comp_year_map[cid].keys()))

heatmap_data = []
company_names = []
for cid in top_ids:
    cname = comp_name_map.get(cid, f"#{cid}")
    company_names.append(cname)
    for y in all_years:
        ss = comp_year_map[cid].get(y, [])
        if ss:
            heatmap_data.append({
                "company_name": cname, "year": y,
                "avg_score": round(float(np.mean(ss)), 2), "count": len(ss),
            })

trends = {"by_type": by_type, "heatmap_data": heatmap_data, "companies": company_names, "years": all_years}
with open(OUT / "trends.json", "w", encoding="utf-8") as f:
    json.dump(trends, f, ensure_ascii=False, indent=2)
print(f"  -> {OUT / 'trends.json'}")

# ═══════════════════════════════════════════════════════
# 5. Insights
# ═══════════════════════════════════════════════════════
print("[5/6] Generating insights.json...")

insight_items = []
for c in all_companies:
    cw = comp_works.get(c["id"], [])
    cs = [w["rating_score"] for w in cw if w["rating_score"] is not None]
    if not cs:
        continue
    avg = float(np.mean(cs))
    # Trend slope
    year_avgs = defaultdict(list)
    for w in cw:
        if w.get("year") and w.get("rating_score") is not None:
            year_avgs[w["year"]].append(w["rating_score"])
    yy = sorted(year_avgs.keys())
    ya = [float(np.mean(year_avgs[y])) for y in yy]
    slope = round(float(scipy_stats.linregress(yy, ya)[0]), 4) if len(ya) >= 2 else 0.0
    insight_items.append({
        "company_id": c["id"], "company_name": c["name"], "company_type": c["type"],
        "avg_score": round(avg, 2), "works_count": len(cw), "trend_slope": slope,
    })

if insight_items:
    s_arr = np.array([r["avg_score"] for r in insight_items])
    mean_all, std_all = np.mean(s_arr), np.std(s_arr) if np.std(s_arr) > 0 else 1
    for r in insight_items:
        r["z_score"] = round((r["avg_score"] - mean_all) / std_all, 2)
    insight_items.sort(key=lambda x: x["z_score"], reverse=True)
    for i, r in enumerate(insight_items):
        r["rank"] = i + 1

    # Risk
    slopes = np.array([r["trend_slope"] for r in insight_items])
    slope_mean, slope_std = np.mean(slopes), np.std(slopes) if np.std(slopes) > 0 else 1
    for r in insight_items:
        if r["trend_slope"] < slope_mean - slope_std:
            r["risk_level"] = "high"
        elif r["trend_slope"] < slope_mean:
            r["risk_level"] = "medium"
        else:
            r["risk_level"] = "low"

    risk_alerts = [r for r in insight_items if r["risk_level"] in ("high", "medium")]

    # Track benchmarks
    type_scores_map = defaultdict(list)
    for r in insight_items:
        type_scores_map[r["company_type"]].append(r["avg_score"])
    track_benchmarks = {t: round(float(np.percentile(ss, 65)), 2) for t, ss in type_scores_map.items()}

insights = {"top_companies": insight_items, "risk_alerts": risk_alerts, "track_benchmarks": track_benchmarks}
with open(OUT / "insights.json", "w", encoding="utf-8") as f:
    json.dump(insights, f, ensure_ascii=False, indent=2)
print(f"  -> {OUT / 'insights.json'}")

# ═══════════════════════════════════════════════════════
# 6. Pre-render chart images
# ═══════════════════════════════════════════════════════
print("[6/6] Generating chart images...")

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.font_manager as fm

    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False

    # Rating distribution bar chart
    colors_map = {"年度推荐": "#f06b4a", "佳作": "#f5a623", "还行": "#3cc9a6", "能看": "#5b8def", "不明": "#999", "拉了": "#7c5ce0", "史": "#e8405d"}
    fig, ax = plt.subplots(figsize=(10, 6))
    labels = [d["label"] for d in rating_distribution]
    values = [d["count"] for d in rating_distribution]
    bar_colors = [colors_map.get(l, "#999") for l in labels]
    bars = ax.bar(labels, values, color=bar_colors, edgecolor="white", linewidth=1.5)
    ax.set_title("作品评级分布", fontsize=16, fontweight="bold")
    for bar, val in zip(bars, values):
        if val > 0:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1, str(val), ha="center", fontsize=11)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", alpha=0.3)
    fig.savefig(OUT / "charts" / "rating_distribution.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

    # Boxplot
    fig, ax = plt.subplots(figsize=(10, 6))
    order = ["2D", "3D", "三渲二"]
    bp_data = [[w["rating_score"] for w in scored if w.get("company_type") == t] for t in order]
    bp = ax.boxplot(bp_data, tick_labels=order, patch_artist=True)
    for i, patch in enumerate(bp["boxes"]):
        patch.set_facecolor(["#5b8def", "#f06b4a", "#3cc9a6"][i])
        patch.set_alpha(0.7)
    ax.set_title("各类型公司评分分布", fontsize=16, fontweight="bold")
    ax.grid(axis="y", alpha=0.3)
    ax.axhline(y=0, color="gray", linestyle="--", alpha=0.5)
    fig.savefig(OUT / "charts" / "boxplot.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

    # Heatmap (top 20)
    fig, ax = plt.subplots(figsize=(14, 10))
    import seaborn as sns
    matrix = np.full((len(company_names), len(all_years)), np.nan)
    for hd in heatmap_data:
        ri = company_names.index(hd["company_name"])
        ci = all_years.index(hd["year"])
        matrix[ri][ci] = hd["avg_score"]
    sns.heatmap(matrix, annot=True, fmt=".1f", cmap="RdYlGn", center=0,
                xticklabels=all_years, yticklabels=company_names,
                linewidths=0.5, cbar_kws={"label": "平均评分", "shrink": 0.8}, ax=ax)
    ax.set_title("公司 x 年份 评分热力图", fontsize=16, fontweight="bold")
    plt.xticks(rotation=45, ha="right")
    fig.savefig(OUT / "charts" / "heatmap.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

    print(f"  -> {OUT / 'charts' / 'rating_distribution.png'}")
    print(f"  -> {OUT / 'charts' / 'boxplot.png'}")
    print(f"  -> {OUT / 'charts' / 'heatmap.png'}")
except Exception as e:
    print(f"  [WARN] Chart generation failed: {e}")

# ═══════════════════════════════════════════════════════
print(f"\n{'='*60}")
print(f"Done! All files in: {OUT}")
print(f"{'='*60}")
