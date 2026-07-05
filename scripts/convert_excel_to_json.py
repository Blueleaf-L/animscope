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


def classify_company_type(company_name, _work_types):
    """Determine company type — hardcoded from manual review (most reliable)."""
    MIXED = {
        "好传", "福煦影视", "福煦影视（福总）", "福总",
        "云图", "七创社", "米粒影业", "绘之刃", "声影动漫",
    }
    ONLY_2D = {
        "视美", "震雷", "彩色铅笔", "大火鸟", "画枚", "七灵石", "ASK",
        "艾尔平方", "小疯映画", "分子互动", "寒木春华", "娃娃鱼", "六道无鱼",
        "璀璨星空", "什悦文化", "糖人家", "知行合一", "崇卓", "灵参伍", "立羽",
        "心魂", "柒幺柒", "九五年", "时七羽墨", "七瞳映画", "启缘映画", "洛水花园",
        "绘梦", "哔梦", "绘梦/哔梦", "Sunflowers", "上美", "中汇影视",
    }
    ONLY_3D = {
        "幻维数码", "原力动画", "神漫", "吾立方", "伊恩", "晴祥", "初色",
        "百漫", "大呈印象", "万维猫", "筑梦", "天工艺彩", "艺画开天", "海岸线",
        "虚拟印象", "超神影业", "黑岩网络", "谜谭", "若森", "中影年年", "君艺心",
        "龙沧", "同明宣", "灵犀文化", "玄机科技", "氦闪", "凝羽动画", "美盛",
    }
    ONLY_SXS = {
        "更三", "三三而川", "更三/三三而川", "笔酷文化", "纸飞机", "元气蛙",
        "幻马群英社", "两点十分",
    }

    for m in MIXED:
        if m in company_name or company_name in m:
            return "混合型"
    for d in ONLY_2D:
        if d in company_name or company_name in d:
            return "2D"
    for d in ONLY_3D:
        if d in company_name or company_name in d:
            return "3D"
    for s in ONLY_SXS:
        if s in company_name or company_name in s:
            return "三渲二"

    # Fallback: determine from works' types
    unique = set(_work_types)
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
    # Also build fuzzy index (strip spaces + year suffix) for better matching
    type_lookup = {}
    type_lookup_fuzzy = {}
    for comp_name, works in type_data.items():
        type_lookup[comp_name] = {}
        type_lookup_fuzzy[comp_name] = {}
        for w in works:
            wname = w["name"]
            type_lookup[comp_name][wname] = w["type"]
            # Fuzzy key: strip spaces, remove trailing (YYYY) and numbers
            import re as _re
            fuzzy = _re.sub(r'\s+', '', wname)
            fuzzy = _re.sub(r'[(（]\d{4}[)）]$', '', fuzzy)
            type_lookup_fuzzy[comp_name][fuzzy] = w["type"]

    print(f"\n[*] Loaded corrected types for {len(type_data)} companies")

    # Read Excel
    print(f"[*] Reading Excel: {excel_path}")
    df = load_and_clean_data(excel_path)
    print(f"  {len(df)} rows, {df['动画公司'].nunique()} companies")

    # Fix known typo: 中国奇谭第一季 (2026) -> 中国奇谭第二季
    typo_fixed = 0
    for idx in df.index:
        name = str(df.at[idx, "动画名"])
        year = df.at[idx, "年份"]
        if "中国奇谭" in name and "第一季" in name and pd.notna(year) and int(year) >= 2026:
            df.at[idx, "动画名"] = name.replace("第一季", "第二季")
            typo_fixed += 1
    if typo_fixed:
        print(f"  Fixed typo: '中国奇谭第一季' -> '第二季' ({typo_fixed} entry)")

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

        company_type = classify_company_type(company_name, work_types_seen)

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

            # Use corrected type from the lookup — try exact first, then fuzzy
            corrected_type = lookup.get(work_name, None)
            if not corrected_type:
                fuzzy_key = re.sub(r'\s+', '', work_name)
                fuzzy_key = re.sub(r'[(（]\d{4}[)）]$', '', fuzzy_key)
                corrected_type = type_lookup_fuzzy.get(company_name, {}).get(fuzzy_key, None)
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
