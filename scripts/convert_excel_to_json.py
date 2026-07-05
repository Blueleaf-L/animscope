#!/usr/bin/env python3
"""
Excel → JSON 转换器
复用 v1 经过实战验证的数据清洗逻辑，处理：
- 合并单元格 (ffill)
- 评分映射（含 "15+2" 格式的数量解析）
- 评级模糊匹配（"年度推荐 强推荐" → "年度推荐"）
- 数据类型强转

输出: data/companies.json + data/works.json（干净的结构化数据，供 DB 导入）

用法:
    python scripts/convert_excel_to_json.py [path/to/data.xlsx]
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
# 评级映射体系（与 v1 保持一致）
# ============================================================

# V2 评分体系：-2.0 ~ 6.0，以"不明"为 0 基线
# "能看"为负分（勉强可看，低于平均），"不明"为中性 0
RATING_SCORE_MAP = {
    "年度推荐 强推荐": 5.0,
    "年度推荐 中推荐": 4.0,
    "年度推荐 普通推荐": 3.0,
    "佳作": 2.0,
    "佳作 弱推荐": 1.5,
    "还行": 0.5,
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

# 公司制作类型识别
TYPE_PATTERNS = {
    "2D": re.compile(r"2D|二维|2d"),
    "3D": re.compile(r"3D|三维|3d"),
    "三渲二": re.compile(r"三渲二|三转二|3D.*2D|2D.*3D|卡通渲染"),
}


def classify_company_type(raw: str) -> str:
    """从原始制作类型字符串识别为 2D / 3D / 三渲二"""
    if not raw or pd.isna(raw):
        return "3D"
    raw = str(raw).strip()
    for ctype, pattern in TYPE_PATTERNS.items():
        if pattern.search(raw):
            return ctype
    return "3D"


def parse_quantity(val) -> int:
    """解析数量列，处理 "15+2" 这种格式"""
    if pd.isna(val):
        return 0
    if isinstance(val, (int, float)):
        return int(val)
    if isinstance(val, str) and "+" in val:
        parts = val.split("+")
        return sum(int(p.strip()) for p in parts if p.strip().isdigit())
    try:
        return int(val)
    except (ValueError, TypeError):
        return 0


def load_and_clean_data(excel_path: str) -> pd.DataFrame:
    """读取 Excel 并清洗数据（核心逻辑复用 v1）"""
    xls = pd.ExcelFile(excel_path)
    # 自动检测 sheet 名（兼容不同 Excel 版本）
    sheet_name = xls.sheet_names[0]
    print(f"  读取 Sheet: '{sheet_name}'")

    df = pd.read_excel(excel_path, sheet_name=sheet_name)

    # 自动检测列名映射
    col_map = _detect_columns(df.columns.tolist())
    df = df.rename(columns=col_map)
    print(f"  列名映射: {col_map}")

    # 前向填充合并单元格
    df["动画公司"] = df["动画公司"].ffill()
    df["制作"] = df["制作"].ffill()
    df["数量"] = df["数量"].ffill()

    # 解析数量
    df["作品数"] = np.array([parse_quantity(v) for v in df["数量"].tolist()], dtype=int)

    # 处理空值
    df["评级"] = df["评级"].fillna("不明")
    df["动画名"] = df["动画名"].fillna("未知作品")
    df["年份"] = pd.to_numeric(df["年份"], errors="coerce")

    # numpy 向量化映射评级 → 评分 / 标签
    rating_scores = df["评级"].map(RATING_SCORE_MAP).fillna(-1).values.astype(np.float64)
    rating_labels = df["评级"].map(RATING_LABEL_MAP).fillna("不明").values
    df["rating_score"] = rating_scores
    df["rating_label"] = rating_labels

    return df


def _detect_columns(columns: list) -> dict:
    """自动检测 Excel 列名，映射到标准名称。

    支持多种变体：
      - 动画公司 / 公司 / 公司名称 → 动画公司
      - 制作 / 制作技术 / 类型 → 制作
      - 动画名 / 作品名 / 作品名称 / 动画作品 → 动画名
      - 年份 / 播出年份 / 首播年份 → 年份
      - 评级 / 评价 / 作品评价 → 评级
      - 数量 / 作品数量 → 数量
    """
    mapping = {}
    patterns = {
        "动画公司": [r"动画公司", r"公司$", r"公司名称", r"^公司"],
        "制作": [r"制作", r"类型$", r"^类型"],
        "动画名": [r"动画名", r"作品名", r"作品名称", r"动画作品", r"^作品"],
        "年份": [r"年份", r"播出年份", r"首播年份", r"^年"],
        "评级": [r"评级", r"评价", r"作品评价", r"^评"],
        "数量": [r"数量", r"作品数量", r"^数"],
    }

    for col in columns:
        matched = False
        for target, pats in patterns.items():
            for pat in pats:
                if re.search(pat, str(col)):
                    mapping[col] = target
                    matched = True
                    break
            if matched:
                break
    return mapping


def convert(excel_path: str, output_dir: str = "data"):
    """主转换函数：Excel → companies.json + works.json"""
    os.makedirs(output_dir, exist_ok=True)

    print(f"\n[*] 读取 Excel: {excel_path}")
    df = load_and_clean_data(excel_path)
    print(f"  共 {len(df)} 行，{df['动画公司'].nunique()} 家公司")

    # ── 生成公司列表 ──
    companies = []
    works_all = []
    company_names_seen = set()

    for company_name, group in df.groupby("动画公司", sort=False):
        # 分类公司类型
        raw_type = str(group["制作"].iloc[0])
        company_type = classify_company_type(raw_type)

        # 去重（同一公司名只保留第一次出现的类型）
        if company_name in company_names_seen:
            # 用之前已经添加的类型
            continue
        company_names_seen.add(company_name)

        companies.append({
            "name": str(company_name).strip(),
            "type": company_type,
            "total_works": int(group["作品数"].iloc[0]),
        })

        # ── 生成作品列表 ──
        for _, row in group.iterrows():
            work_name = str(row["动画名"]).strip()
            if not work_name or work_name == "nan" or work_name == "未知作品":
                continue

            year_val = row["年份"]
            year = int(year_val) if pd.notna(year_val) else None

            raw_rating = str(row["评级"]) if pd.notna(row["评级"]) else None
            rating_label = row["rating_label"] if pd.notna(row["rating_label"]) else None
            rating_score = float(row["rating_score"]) if pd.notna(row["rating_score"]) else None

            works_all.append({
                "company_name": str(company_name).strip(),
                "name": work_name,
                "year": year,
                "rating_raw": raw_rating[:50] if raw_rating else None,
                "rating_label": rating_label,
                "rating_score": rating_score,
            })

    print(f"  生成 {len(companies)} 家公司，{len(works_all)} 部作品")

    # ── 保存 JSON ──
    metadata = {
        "generated_at": datetime.now(CST).isoformat(),
        "source_file": os.path.basename(excel_path),
        "total_companies": len(companies),
        "total_works": len(works_all),
    }

    # companies.json
    companies_path = os.path.join(output_dir, "companies.json")
    with open(companies_path, "w", encoding="utf-8") as f:
        json.dump({"_metadata": metadata, "companies": companies}, f, ensure_ascii=False, indent=2)
    print(f"  [OK] {companies_path}")

    # works.json
    works_path = os.path.join(output_dir, "works.json")
    with open(works_path, "w", encoding="utf-8") as f:
        json.dump({"_metadata": metadata, "works": works_all}, f, ensure_ascii=False, indent=2)
    print(f"  [OK] {works_path}")

    # ── 数据质量摘要 ──
    print(f"\n[==] 数据质量报告:")
    print(f"  公司总数: {len(companies)}")
    print(f"  作品总数: {len(works_all)}")
    print(f"  有年份: {sum(1 for w in works_all if w['year'])} 部")
    print(f"  有评分: {sum(1 for w in works_all if w['rating_score'] is not None)} 部")
    print(f"  2D 公司: {sum(1 for c in companies if c['type'] == '2D')}")
    print(f"  3D 公司: {sum(1 for c in companies if c['type'] == '3D')}")
    print(f"  三渲二: {sum(1 for c in companies if c['type'] == '三渲二')}")

    # 评级分布
    label_counts = defaultdict(int)
    for w in works_all:
        if w["rating_label"]:
            label_counts[w["rating_label"]] += 1
    print(f"  评级分布: {dict(label_counts)}")

    return companies, works_all


if __name__ == "__main__":
    # 解析参数
    if len(sys.argv) > 1:
        excel_path = sys.argv[1]
    else:
        # 自动查找 data/ 下的 .xlsx 文件
        data_dir = Path(__file__).parent.parent / "data"
        xlsx_files = list(data_dir.glob("*.xlsx"))
        if not xlsx_files:
            print("[ERR] 未找到 .xlsx 文件，请将 Excel 文件放入 data/ 目录")
            print("   用法: python scripts/convert_excel_to_json.py [path/to/data.xlsx]")
            sys.exit(1)
        excel_path = str(xlsx_files[0])

    output_dir = Path(__file__).parent.parent / "data"
    convert(str(excel_path), str(output_dir))
    print("\n[OK] Excel → JSON 转换完成！")
