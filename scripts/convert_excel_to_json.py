#!/usr/bin/env python3
"""
Excel -> JSON 转换器。
使用「公司的完整作品及对应制作类型.json」中的类型数据（人工校对过的），
覆盖 Excel 中的类型。自动识别混合型公司。

用法: python scripts/convert_excel_to_json.py
"""

import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

CST = timezone(timedelta(hours=8))

# ============================================================
# V2 评分体系
# ============================================================

RATING_SCORE_MAP = {
    "年度推荐 强推荐": 5.0,
    "年度推荐 中推荐": 4.0,
    "年度推荐 普通推荐": 3.0,
    "佳作": 3.0,
    "佳作 弱推荐": 2.5,
    "还行": 1.5,
    "能看": -0.5,
    "不明": 0.0,
    "拉了": -1.0,
    "史": -2.0,
}

RATING_LABEL_MAP = {
    "年度推荐 强推荐": "年度推荐",
    "年度推荐 中推荐": "年度推荐",
    "年度推荐 普通推荐": "年度推荐",
    "佳作": "佳作",
    "佳作 弱推荐": "佳作",
    "还行": "还行",
    "能看": "能看",
    "不明": "不明",
    "拉了": "拉了",
    "史": "史",
}


def load_and_clean_data(excel_path):
    """Read Excel and clean data."""
    xls = pd.ExcelFile(excel_path)
    sheet_name = xls.sheet_names[0]
    print(f"  Reading Sheet: '{sheet_name}'")

    df = pd.read_excel(excel_path, sheet_name=sheet_name)
    col_map = _detect_columns(df.columns.tolist())
    df = df.rename(columns=col_map)

    df["动画公司"] = df["动画公司"].ffill()
    df["评级"] = df["评级"].fillna("不明")
    df["动画名"] = df["动画名"].fillna("未知作品")
    df["年份"] = pd.to_numeric(df["年份"], errors="coerce")

    rating_scores = df["评级"].map(RATING_SCORE_MAP).fillna(0.0).values.astype(np.float64)
    rating_labels = df["评级"].map(RATING_LABEL_MAP).fillna("不明").values
    df["rating_score"] = rating_scores
    df["rating_label"] = rating_labels

    return df


def _detect_columns(columns):
    mapping = {}
    patterns = {
        "动画公司": [r"动画公司", r"公司$", r"公司名称"],
        "制作": [r"制作", r"类型$", r"^类型"],
        "动画名": [r"动画名", r"作品名", r"作品名称", r"动画作品"],
        "年份": [r"年份", r"播出年份", r"首播年份"],
        "评级": [r"评级", r"评价", r"作品评价"],
        "数量": [r"数量", r"作品数量"],
    }
    for col in columns:
        for target, pats in patterns.items():
            if any(re.search(p, str(col)) for p in pats):
                mapping[col] = target
                break
    return mapping


def classify_company_type(work_types):
    """Determine company type from its works' types.
    If a company produces more than one type, it's '混合型'.
    """
    unique = set(work_types)
    if len(unique) >= 2:
        return "混合型"
    return unique.pop() if unique else "3D"


def convert(excel_path, type_data_path, output_dir="data"):
    """Main: Excel -> companies.json + works.json, with corrected types."""
    os.makedirs(output_dir, exist_ok=True)

    # Load corrected types
    with open(type_data_path, "r", encoding="utf-8") as f:
        type_data = json.load(f)

    # Build lookup: company_name -> work_name -> type
    type_lookup = {}
    for comp_name, works in type_data.items():
        type_lookup[comp_name] = {}
        for w in works:
            type_lookup[comp_name][w["name"]] = w["type"]

    print(f"\n[*] Loaded corrected types for {len(type_data)} companies")

    # Read Excel
    print(f"[*] Reading Excel: {excel_path}")
    df = load_and_clean_data(excel_path)
    print(f"  {len(df)} rows, {df['动画公司'].nunique()} companies")

    # Generate companies and works
    companies = []
    works_all = []
    corrected_count = 0

    for company_name, group in df.groupby("动画公司", sort=False):
        # Determine company type from corrected data
        lookup = type_lookup.get(company_name, {})
        work_types_seen = []
        for _, row in group.iterrows():
            wname = str(row["动画名"]).strip()
            corrected_type = lookup.get(wname, None)
            if corrected_type:
                work_types_seen.append(corrected_type)

        company_type = classify_company_type(work_types_seen)

        companies.append({
            "name": str(company_name).strip(),
            "type": company_type,
        })

        # Works
        for _, row in group.iterrows():
            work_name = str(row["动画名"]).strip()
            if not work_name or work_name == "nan" or work_name == "未知作品":
                continue

            year_val = row["年份"]
            year = int(year_val) if pd.notna(year_val) else None

            raw_rating = str(row["评级"]) if pd.notna(row["评级"]) else None
            rating_label = row["rating_label"] if pd.notna(row["rating_label"]) else None
            rating_score = float(row["rating_score"]) if pd.notna(row["rating_score"]) else None

            # Use corrected type from the lookup, fall back to Excel
            corrected_type = lookup.get(work_name, None)
            if corrected_type:
                corrected_count += 1

            works_all.append({
                "company_name": str(company_name).strip(),
                "name": work_name,
                "year": year,
                "work_type": corrected_type or "3D",  # Per-work type from corrected data
                "rating_raw": raw_rating[:50] if raw_rating else None,
                "rating_label": rating_label,
                "rating_score": rating_score,
            })

    print(f"  {len(companies)} companies, {len(works_all)} works")
    print(f"  Types corrected for {corrected_count} works")

    # Save
    metadata = {
        "generated_at": datetime.now(CST).isoformat(),
        "source_file": os.path.basename(excel_path),
        "total_companies": len(companies),
        "total_works": len(works_all),
    }

    companies_path = os.path.join(output_dir, "companies.json")
    with open(companies_path, "w", encoding="utf-8") as f:
        json.dump({"_metadata": metadata, "companies": companies}, f, ensure_ascii=False, indent=2)
    print(f"  [OK] {companies_path}")

    works_path = os.path.join(output_dir, "works.json")
    with open(works_path, "w", encoding="utf-8") as f:
        json.dump({"_metadata": metadata, "works": works_all}, f, ensure_ascii=False, indent=2)
    print(f"  [OK] {works_path}")

    # Summary
    print(f"\n[==] Data Quality Report:")
    print(f"  Companies: {len(companies)}")
    print(f"  Works: {len(works_all)}")
    type_counts = defaultdict(int)
    for c in companies:
        type_counts[c["type"]] += 1
    for t, c in sorted(type_counts.items()):
        print(f"  {t}: {c}")
    label_counts = defaultdict(int)
    for w in works_all:
        if w["rating_label"]:
            label_counts[w["rating_label"]] += 1
    print(f"  Rating distribution: {dict(label_counts)}")

    return companies, works_all


if __name__ == "__main__":
    data_dir = Path(__file__).parent.parent / "data"
    xlsx_files = list(data_dir.glob("*.xlsx"))
    if not xlsx_files:
        print("[ERR] No .xlsx file found in data/")
        sys.exit(1)

    type_data_path = data_dir / "公司的完整作品及对应制作类型.json"
    if not type_data_path.exists():
        print(f"[ERR] Type data file not found: {type_data_path}")
        sys.exit(1)

    convert(str(xlsx_files[0]), str(type_data_path), str(data_dir))
    print("\n[OK] Excel -> JSON conversion complete!")
