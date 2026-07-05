import numpy as np
from collections import defaultdict
from typing import Optional

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from scipy import stats as scipy_stats

from app.models.company import Company
from app.models.work import Work


class AnalysisService:
    """Core analysis engine — computes all analytics from raw DB data."""

    RATING_ORDER = ["年度推荐", "佳作", "还行", "能看", "不明", "拉了", "史"]

    @staticmethod
    async def _get_all_data(db: AsyncSession) -> dict:
        """Fetch all raw data in one go for efficient computation.

        Returns a dict with:
          - companies: list of Company ORM objects
          - works: list of (Work, company_name, company_type) tuples
        """
        from sqlalchemy.orm import selectinload

        companies_result = await db.execute(select(Company))
        companies = companies_result.scalars().all()

        works_result = await db.execute(
            select(Work, Company.name, Company.type)
            .join(Company, Work.company_id == Company.id)
            .where(Work.rating_score.isnot(None))
        )
        works = works_result.all()

        return {"companies": companies, "works": works}

    @staticmethod
    async def calc_overview(db: AsyncSession) -> dict:
        """Calculate homepage overview statistics."""
        raw = await AnalysisService._get_all_data(db)
        companies = raw["companies"]
        work_rows = raw["works"]  # list of (Work, company_name, company_type)

        all_works_result = await db.execute(select(func.count(Work.id)))
        total_works = all_works_result.scalar() or 0

        # Unpack work data
        work_scores = []
        work_labels = []
        work_years = []
        work_types = []

        for w, comp_name, comp_type in work_rows:
            if w.rating_score is not None:
                work_scores.append(w.rating_score)
            work_labels.append(w.rating_label)
            work_years.append(w.year)
            work_types.append(comp_type)

        # Stats
        avg_score = float(np.mean(work_scores)) if work_scores else 0.0

        recommended_count = sum(1 for l in work_labels if l == "年度推荐")
        good_count = sum(1 for l in work_labels if l in ("佳作", "还行"))
        trash_count = sum(1 for l in work_labels if l in ("拉了", "史"))

        stats = {
            "total_companies": len(companies),
            "total_works": total_works,
            "avg_score": round(avg_score, 2),
            "recommended_count": recommended_count,
            "good_count": good_count,
            "trash_count": trash_count,
        }

        # Type distribution
        type_data = defaultdict(lambda: {"count": 0, "scores": []})
        for i, ct in enumerate(work_types):
            if work_scores[i] is not None:
                type_data[ct]["count"] += 1
                type_data[ct]["scores"].append(work_scores[i])

        type_distribution = []
        for t, d in type_data.items():
            type_distribution.append({
                "type": t,
                "count": d["count"],
                "avg_score": round(float(np.mean(d["scores"])), 2) if d["scores"] else 0,
            })

        # Yearly trends
        year_data = defaultdict(lambda: {"count": 0, "scores": []})
        for i, year in enumerate(work_years):
            if year and work_scores[i] is not None:
                year_data[year]["count"] += 1
                year_data[year]["scores"].append(work_scores[i])

        yearly_trends = []
        for year in sorted(year_data.keys()):
            d = year_data[year]
            yearly_trends.append({
                "year": year,
                "count": d["count"],
                "avg_score": round(float(np.mean(d["scores"])), 2) if d["scores"] else 0,
            })

        # Rating distribution
        rating_data = defaultdict(int)
        for label in work_labels:
            if label:
                rating_data[label] += 1

        total_labeled = sum(rating_data.values()) or 1
        rating_distribution = []
        for label in AnalysisService.RATING_ORDER:
            count = rating_data.get(label, 0)
            rating_distribution.append({
                "label": label,
                "count": count,
                "percentage": round(count / total_labeled * 100, 1),
            })

        # Diagnostics
        diagnostics = []
        if stats["avg_score"] <= 0:
            diagnostics.append("行业平均评分为负值，整体作品质量有待提升。")
        if trash_count > recommended_count:
            diagnostics.append(f"翻车作品({trash_count})多于推荐作品({recommended_count})，行业精品率偏低。")
        if stats["total_companies"] > 0 and stats["total_works"] / stats["total_companies"] < 5:
            diagnostics.append("平均每家公司作品数量偏少，行业集中度或作品收录完整性需关注。")
        if len(yearly_trends) >= 2:
            recent_avg = np.mean([t["avg_score"] for t in yearly_trends[-3:]])
            older_avg = np.mean([t["avg_score"] for t in yearly_trends[:3]])
            if recent_avg > older_avg:
                diagnostics.append("近年作品质量呈上升趋势，行业发展向好。")
            elif recent_avg < older_avg:
                diagnostics.append("近年作品质量有所下滑，需关注行业生态。")

        return {
            "stats": stats,
            "type_distribution": type_distribution,
            "yearly_trends": yearly_trends,
            "rating_distribution": rating_distribution,
            "diagnostics": diagnostics,
        }

    @staticmethod
    async def calc_rankings(db: AsyncSession, tab: str = "recommended") -> dict:
        """Calculate company rankings by different metrics."""
        raw = await AnalysisService._get_all_data(db)
        companies = raw["companies"]
        work_rows = raw["works"]  # list of (Work, company_name, company_type)

        # Group works by company
        comp_works = defaultdict(list)
        for w, comp_name, comp_type in work_rows:
            comp_works[w.company_id].append((w, comp_name, comp_type))

        rankings = []
        for company in companies:
            cw = comp_works.get(company.id, [])
            if not cw:
                continue

            rec_count = sum(1 for w, _, _ in cw if w.rating_label == "年度推荐")
            trash_count = sum(1 for w, _, _ in cw if w.rating_label in ("拉了", "史"))
            scores = [w.rating_score for w, _, _ in cw if w.rating_score is not None]
            avg = float(np.mean(scores)) if scores else 0.0

            rankings.append({
                "company_id": company.id,
                "company_name": company.name,
                "company_type": company.type,
                "works_count": len(cw),
                "avg_score": round(avg, 2),
                "recommended_count": rec_count,
                "trash_count": trash_count,
            })

        # Sort by tab
        if tab == "recommended":
            rankings.sort(key=lambda x: (x["recommended_count"], x["avg_score"]), reverse=True)
        elif tab == "good":
            rankings.sort(key=lambda x: x["avg_score"], reverse=True)
        elif tab == "trash":
            rankings.sort(key=lambda x: x["trash_count"], reverse=True)

        # Assign ranks
        for i, r in enumerate(rankings):
            r["rank"] = i + 1

        # Calculate Z-scores for overall ranking
        if rankings:
            scores_arr = np.array([r["avg_score"] for r in rankings])
            mean_score = np.mean(scores_arr)
            std_score = np.std(scores_arr) if np.std(scores_arr) > 0 else 1
            for r in rankings:
                r["z_score"] = round((r["avg_score"] - mean_score) / std_score, 2)

        return {"items": rankings, "tab": tab}

    @staticmethod
    async def calc_trends(db: AsyncSession) -> dict:
        """Calculate yearly trends by company type + heatmap matrix."""
        raw = await AnalysisService._get_all_data(db)
        work_rows = raw["works"]  # list of (Work, company_name, company_type)
        # Build company dict for type lookup
        comp_type_map = {}
        for w, comp_name, comp_type in work_rows:
            comp_type_map[w.company_id] = comp_type

        # Group by year and type
        year_type_data = defaultdict(lambda: {
            "2D": {"count": 0, "scores": []},
            "3D": {"count": 0, "scores": []},
            "三渲二": {"count": 0, "scores": []},
        })

        for w, comp_name, comp_type in work_rows:
            if not w.year or w.rating_score is None:
                continue
            ct = comp_type_map.get(w.company_id)
            if not ct:
                continue
            year_type_data[w.year][ct]["count"] += 1
            year_type_data[w.year][ct]["scores"].append(w.rating_score)

        by_type = []
        for year in sorted(year_type_data.keys()):
            d = year_type_data[year]
            item = {"year": year}
            for tkey in ["2D", "3D", "三渲二"]:
                td = d[tkey]
                item[f"type_{'2d' if tkey == '2D' else '3d' if tkey == '3D' else 'hybrid'}_count"] = td["count"]
                item[f"type_{'2d' if tkey == '2D' else '3d' if tkey == '3D' else 'hybrid'}_avg"] = (
                    round(float(np.mean(td["scores"])), 2) if td["scores"] else 0
                )
            total_count = sum(td["count"] for td in d.values())
            all_scores = []
            for td in d.values():
                all_scores.extend(td["scores"])
            item["total_count"] = total_count
            item["total_avg"] = round(float(np.mean(all_scores)), 2) if all_scores else 0
            by_type.append(item)

        # Heatmap: company × year matrix
        comp_year_data = defaultdict(lambda: defaultdict(list))
        comp_name_map = {}
        for w, comp_name, comp_type in work_rows:
            if not w.year or w.rating_score is None:
                continue
            comp_year_data[w.company_id][w.year].append(w.rating_score)
            comp_name_map[w.company_id] = comp_name

        # Get top N companies by total works
        comp_total = {cid: sum(len(s) for s in years.values()) for cid, years in comp_year_data.items()}
        top_companies = sorted(comp_total.items(), key=lambda x: x[1], reverse=True)[:20]
        top_company_ids = {cid for cid, _ in top_companies}

        years_set = set()
        for cid in top_company_ids:
            years_set.update(comp_year_data[cid].keys())
        years_list = sorted(years_set)

        heatmap_data = []
        company_names = []
        for cid in top_company_ids:
            cname = comp_name_map.get(cid, f"#{cid}")
            if not cname:
                continue
            company_names.append(cname)
            for year in years_list:
                scores = comp_year_data[cid].get(year, [])
                if scores:
                    heatmap_data.append({
                        "company_name": cname,
                        "year": year,
                        "avg_score": round(float(np.mean(scores)), 2),
                        "count": len(scores),
                    })

        return {
            "by_type": by_type,
            "heatmap_data": heatmap_data,
            "companies": company_names,
            "years": years_list,
        }

    @staticmethod
    async def calc_compare(db: AsyncSession, ids: list[int]) -> dict:
        """Calculate comparison metrics for multiple companies."""
        works_result = await db.execute(
            select(Work).where(
                Work.company_id.in_(ids),
                Work.rating_score.isnot(None),
            )
        )
        works = works_result.scalars().all()

        comp_result = await db.execute(
            select(Company).where(Company.id.in_(ids))
        )
        companies = {c.id: c for c in comp_result.scalars().all()}

        # Group works by company
        comp_works = defaultdict(list)
        for w in works:
            comp_works[w.company_id].append(w)

        result_companies = []
        for cid in ids:
            comp = companies.get(cid)
            if not comp:
                continue
            cw = comp_works.get(cid, [])
            scores = [w.rating_score for w in cw if w.rating_score is not None]
            avg_score = float(np.mean(scores)) if scores else 0.0
            rec_ratio = sum(1 for w in cw if w.rating_label == "年度推荐") / max(len(cw), 1)
            trash_ratio = sum(1 for w in cw if w.rating_label in ("拉了", "史")) / max(len(cw), 1)

            # Yearly averages
            year_scores = defaultdict(list)
            for w in cw:
                if w.year and w.rating_score is not None:
                    year_scores[w.year].append(w.rating_score)
            yearly_avg = [
                {"year": y, "avg_score": round(float(np.mean(s)), 2)}
                for y, s in sorted(year_scores.items())
            ]

            result_companies.append({
                "id": comp.id,
                "name": comp.name,
                "type": comp.type,
                "works_count": len(cw),
                "avg_score": round(avg_score, 2),
                "recommended_ratio": round(rec_ratio * 100, 1),
                "trash_ratio": round(trash_ratio * 100, 1),
                "yearly_avg": yearly_avg,
            })

        return {"companies": result_companies}

    @staticmethod
    async def calc_diff(db: AsyncSession, a: int, b: int) -> Optional[dict]:
        """Calculate Cohen's d and head-to-head comparison between two companies."""
        works_result = await db.execute(
            select(Work).where(
                Work.company_id.in_([a, b]),
                Work.rating_score.isnot(None),
            )
        )
        works = works_result.scalars().all()

        comp_result = await db.execute(
            select(Company).where(Company.id.in_([a, b]))
        )
        companies = {c.id: c for c in comp_result.scalars().all()}

        if not companies.get(a) or not companies.get(b):
            return None

        scores_a = np.array([w.rating_score for w in works if w.company_id == a])
        scores_b = np.array([w.rating_score for w in works if w.company_id == b])

        if len(scores_a) == 0 or len(scores_b) == 0:
            return None

        # Cohen's d
        mean_a, mean_b = np.mean(scores_a), np.mean(scores_b)
        var_a, var_b = np.var(scores_a, ddof=1), np.var(scores_b, ddof=1)
        pooled_std = np.sqrt(((len(scores_a) - 1) * var_a + (len(scores_b) - 1) * var_b) / (len(scores_a) + len(scores_b) - 2))

        cohens_d = round(float((mean_a - mean_b) / pooled_std), 3) if pooled_std > 0 else 0.0

        # Dimensions
        dimensions = []
        dims = [
            ("平均评分", float(mean_a), float(mean_b)),
            ("作品数量", float(len(scores_a)), float(len(scores_b))),
            ("标准差 (σ)", float(np.std(scores_a)), float(np.std(scores_b))),
            ("最高分", float(np.max(scores_a)), float(np.max(scores_b))),
            ("最低分", float(np.min(scores_a)), float(np.min(scores_b))),
        ]

        for name, va, vb in dims:
            diff = va - vb
            winner = "a" if diff > 0 else "b" if diff < 0 else "tie"
            dimensions.append({
                "dimension": name,
                "company_a_value": round(va, 2),
                "company_b_value": round(vb, 2),
                "diff": round(diff, 2),
                "winner": winner,
            })

        volatility_a = round(float(np.std(scores_a)), 2)
        volatility_b = round(float(np.std(scores_b)), 2)

        return {
            "cohens_d": cohens_d,
            "company_a_name": companies[a].name,
            "company_b_name": companies[b].name,
            "dimensions": dimensions,
            "volatility_a": volatility_a,
            "volatility_b": volatility_b,
        }

    @staticmethod
    async def calc_insights(db: AsyncSession) -> dict:
        """Z-Score ranking, risk alerts, and track benchmarks."""
        raw = await AnalysisService._get_all_data(db)
        companies = raw["companies"]
        work_rows = raw["works"]  # list of (Work, company_name, company_type)

        comp_works = defaultdict(list)
        comp_type_map = {}
        for w, comp_name, comp_type in work_rows:
            comp_works[w.company_id].append((w, comp_name, comp_type))
            comp_type_map[w.company_id] = comp_type

        insights = []
        for company in companies:
            cw = comp_works.get(company.id, [])
            scores = [w.rating_score for w, _, _ in cw if w.rating_score is not None]
            if not scores:
                continue

            avg_score = float(np.mean(scores))
            years = sorted([w.year for w, _, _ in cw if w.year])
            trend_slope = 0.0
            if len(years) > 2:
                # Simple linear regression on yearly averages
                year_avgs = defaultdict(list)
                for w, _, _ in cw:
                    if w.year and w.rating_score is not None:
                        year_avgs[w.year].append(w.rating_score)
                y_years = sorted(year_avgs.keys())
                y_avgs = [float(np.mean(year_avgs[y])) for y in y_years]
                if len(y_avgs) >= 2:
                    slope, _, _, _, _ = scipy_stats.linregress(y_years, y_avgs)
                    trend_slope = round(float(slope), 4)

            insights.append({
                "company_id": company.id,
                "company_name": company.name,
                "company_type": company.type,
                "avg_score": round(avg_score, 2),
                "works_count": len(cw),
                "trend_slope": trend_slope,
            })

        # Z-Score ranking
        if insights:
            scores_arr = np.array([r["avg_score"] for r in insights])
            mean_all = np.mean(scores_arr)
            std_all = np.std(scores_arr) if np.std(scores_arr) > 0 else 1
            for r in insights:
                r["z_score"] = round((r["avg_score"] - mean_all) / std_all, 2)

        # Sort by z_score
        insights.sort(key=lambda x: x["z_score"], reverse=True)
        for i, r in enumerate(insights):
            r["rank"] = i + 1

        # Track benchmarks (P65 per type)
        track_benchmarks = {}
        type_scores = defaultdict(list)
        for r in insights:
            type_scores[r["company_type"]].append(r["avg_score"])
        for t, s in type_scores.items():
            track_benchmarks[t] = round(float(np.percentile(s, 65)), 2)

        # Risk assessment
        if insights:
            slopes = np.array([r["trend_slope"] for r in insights])
            slope_std = np.std(slopes) if np.std(slopes) > 0 else 1
            slope_mean = np.mean(slopes)

            for r in insights:
                r["track_benchmark"] = track_benchmarks.get(r["company_type"], 0)
                r["track_percentile"] = round(
                    float(scipy_stats.percentileofscore(
                        [x["avg_score"] for x in insights if x["company_type"] == r["company_type"]],
                        r["avg_score"]
                    )),
                    1,
                )

                # Risk levels
                if r["trend_slope"] < slope_mean - slope_std:
                    r["risk_level"] = "high"
                elif r["trend_slope"] < slope_mean:
                    r["risk_level"] = "medium"
                else:
                    r["risk_level"] = "low"

        # Filter risk alerts
        risk_alerts = [r for r in insights if r["risk_level"] in ("high", "medium")]

        return {
            "top_companies": insights,
            "risk_alerts": risk_alerts,
            "track_benchmarks": track_benchmarks,
        }
