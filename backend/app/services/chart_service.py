"""Chart generation service using matplotlib, seaborn, and plotly."""

import io
from collections import defaultdict
from typing import Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company
from app.models.work import Work

# Color palettes
LIGHT_THEME = {
    "bg": "#ffffff",
    "text": "#333333",
    "grid": "#e0e0e0",
    "palette": ["#5b8def", "#f06b4a", "#3cc9a6", "#7c5ce0", "#f5a623", "#e8405d"],
    "rating_colors": {
        "年度推荐": "#f06b4a",
        "佳作": "#f5a623",
        "还行": "#3cc9a6",
        "能看": "#5b8def",
        "不明": "#999999",
        "拉了": "#7c5ce0",
        "史": "#e8405d",
    },
}

DARK_THEME = {
    "bg": "#1a1a2e",
    "text": "#e0e0e0",
    "grid": "#333355",
    "palette": ["#6fabff", "#ff7b5a", "#4de8b6", "#9b7cf0", "#ffb833", "#f0607d"],
    "rating_colors": {
        "年度推荐": "#ff7b5a",
        "佳作": "#ffb833",
        "还行": "#4de8b6",
        "能看": "#6fabff",
        "不明": "#888888",
        "拉了": "#9b7cf0",
        "史": "#f0607d",
    },
}


def _get_theme(theme: str = "light") -> dict:
    return DARK_THEME if theme == "dark" else LIGHT_THEME


def _setup_mpl_style(theme: dict):
    """Configure matplotlib style for the given theme."""
    plt.rcParams.update({
        "figure.facecolor": theme["bg"],
        "axes.facecolor": theme["bg"],
        "axes.edgecolor": theme["text"],
        "axes.labelcolor": theme["text"],
        "text.color": theme["text"],
        "xtick.color": theme["text"],
        "ytick.color": theme["text"],
        "grid.color": theme["grid"],
        "font.sans-serif": ["Microsoft YaHei", "SimHei", "DejaVu Sans"],
        "axes.unicode_minus": False,
    })


async def _get_company_works_data(db: AsyncSession):
    """Fetch all works with company info."""
    result = await db.execute(
        select(Work, Company.name, Company.type)
        .join(Company, Work.company_id == Company.id)
        .where(Work.rating_score.isnot(None))
    )
    rows = result.all()
    data = []
    for work, comp_name, comp_type in rows:
        data.append({
            "company_name": comp_name,
            "company_type": comp_type,
            "name": work.name,
            "year": work.year,
            "rating_label": work.rating_label,
            "rating_score": float(work.rating_score) if work.rating_score else 0,
        })
    return data


class ChartService:
    """Generates static charts (PNG/SVG) using matplotlib/seaborn and interactive HTML using plotly."""

    @staticmethod
    async def chart_rating_distribution(db: AsyncSession, theme: str = "light") -> tuple[bytes, str]:
        """Generate rating distribution bar chart."""
        t = _get_theme(theme)
        _setup_mpl_style(t)

        data = await _get_company_works_data(db)
        rating_counts = defaultdict(int)
        rating_order = ["年度推荐", "佳作", "还行", "能看", "不明", "拉了", "史"]
        for d in data:
            if d["rating_label"]:
                rating_counts[d["rating_label"]] += 1

        labels = rating_order
        values = [rating_counts.get(l, 0) for l in labels]
        colors = [t["rating_colors"].get(l, "#999") for l in labels]

        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.bar(labels, values, color=colors, edgecolor=t["bg"], linewidth=1.5)
        ax.set_title("作品评级分布", fontsize=16, fontweight="bold", pad=15)
        ax.set_ylabel("作品数量", fontsize=12)
        ax.set_xlabel("评级", fontsize=12)

        for bar, val in zip(bars, values):
            if val > 0:
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(values) * 0.02,
                        str(val), ha="center", va="bottom", fontsize=11, color=t["text"])

        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.grid(axis="y", alpha=0.3)

        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor=t["bg"], transparent=False)
        plt.close(fig)
        buf.seek(0)
        return buf.getvalue(), "image/png"

    @staticmethod
    async def chart_company_radar(db: AsyncSession, company_id: int, theme: str = "light") -> tuple[bytes, str]:
        """Generate company radar chart as SVG."""
        t = _get_theme(theme)
        _setup_mpl_style(t)

        # Get company data
        comp_result = await db.execute(select(Company).where(Company.id == company_id))
        company = comp_result.scalar_one_or_none()
        if not company:
            return b"", "image/svg+xml"

        works_result = await db.execute(
            select(Work).where(Work.company_id == company_id, Work.rating_score.isnot(None))
        )
        works = works_result.scalars().all()

        if not works:
            return b"", "image/svg+xml"

        scores = [float(w.rating_score) for w in works if w.rating_score is not None]
        rec_ratio = sum(1 for w in works if w.rating_label == "年度推荐") / max(len(works), 1)
        trash_ratio = sum(1 for w in works if w.rating_label in ("拉了", "史")) / max(len(works), 1)
        good_ratio = sum(1 for w in works if w.rating_label in ("佳作", "还行")) / max(len(works), 1)

        # Radar categories
        categories = ["平均评分\n(标准化)", "作品数量\n(标准化)", "推荐率", "良品率", "翻车率\n(反向)", "稳定性"]
        n = len(categories)

        # Normalize values to [0, 1] roughly
        avg_score_norm = min(max((np.mean(scores) + 2) / 8, 0), 1)  # -2 to 6 → 0 to 1
        count_norm = min(len(works) / 30, 1)
        stability_norm = 1 - min(np.std(scores) / 4, 1)
        trash_inv = 1 - trash_ratio

        values = [avg_score_norm, count_norm, rec_ratio, good_ratio, trash_inv, stability_norm]
        values.append(values[0])  # Close the loop

        angles = np.linspace(0, 2 * np.pi, n, endpoint=False).tolist()
        angles += angles[:1]

        fig, ax = plt.subplots(figsize=(6, 6), subplot_kw={"projection": "polar"})
        ax.set_theta_offset(np.pi / 2)
        ax.set_theta_direction(-1)

        ax.fill(angles, values, color=t["palette"][0], alpha=0.25)
        ax.plot(angles, values, color=t["palette"][0], linewidth=2)
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories, fontsize=10)
        ax.set_ylim(0, 1)
        ax.set_yticks([0.2, 0.4, 0.6, 0.8])
        ax.set_yticklabels(["20%", "40%", "60%", "80%"], fontsize=8, color=t["text"])
        ax.set_title(f"{company.name} — 综合雷达图", fontsize=14, fontweight="bold", pad=20, color=t["text"])

        buf = io.BytesIO()
        fig.savefig(buf, format="svg", dpi=150, bbox_inches="tight", facecolor=t["bg"], transparent=False)
        plt.close(fig)
        buf.seek(0)
        return buf.getvalue(), "image/svg+xml"

    @staticmethod
    async def chart_heatmap(db: AsyncSession, top_n: int = 20, theme: str = "light") -> tuple[bytes, str]:
        """Generate company × year heatmap using seaborn."""
        t = _get_theme(theme)
        _setup_mpl_style(t)

        data = await _get_company_works_data(db)

        # Group company × year
        comp_year = defaultdict(lambda: defaultdict(list))
        for d in data:
            if d["year"]:
                comp_year[d["company_name"]][d["year"]].append(d["rating_score"])

        # Top N companies by work count
        comp_counts = {name: sum(len(s) for s in years.values()) for name, years in comp_year.items()}
        top_companies = sorted(comp_counts.items(), key=lambda x: x[1], reverse=True)[:top_n]
        top_names = [name for name, _ in top_companies]

        years_set = set()
        for name in top_names:
            years_set.update(comp_year[name].keys())
        years_sorted = sorted(years_set)

        # Build matrix
        matrix = []
        for name in top_names:
            row = []
            for y in years_sorted:
                scores = comp_year[name].get(y, [])
                row.append(np.mean(scores) if scores else np.nan)
            matrix.append(row)

        fig, ax = plt.subplots(figsize=(max(12, len(years_sorted) * 0.5), max(8, top_n * 0.35)))
        mask = np.isnan(matrix)
        sns.heatmap(
            matrix, annot=True, fmt=".1f", cmap="RdYlGn", center=0,
            xticklabels=years_sorted, yticklabels=top_names,
            mask=mask, ax=ax, linewidths=0.5, linecolor=t["grid"],
            cbar_kws={"label": "平均评分", "shrink": 0.8},
        )
        ax.set_title("公司 × 年份 评分热力图", fontsize=16, fontweight="bold", pad=15)
        ax.set_xlabel("年份", fontsize=12)
        ax.set_ylabel("公司", fontsize=12)
        plt.xticks(rotation=45, ha="right")
        plt.yticks(rotation=0)

        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor=t["bg"])
        plt.close(fig)
        buf.seek(0)
        return buf.getvalue(), "image/png"

    @staticmethod
    async def chart_boxplot(db: AsyncSession, type_filter: Optional[str] = None, theme: str = "light") -> tuple[bytes, str]:
        """Generate box plot by rating label or company type."""
        t = _get_theme(theme)
        _setup_mpl_style(t)

        data = await _get_company_works_data(db)

        if type_filter:
            data = [d for d in data if d["company_type"] == type_filter]
            group_key = "rating_label"
            title = f"{type_filter} 动画公司 — 评级分布箱线图"
        else:
            group_key = "company_type"
            title = "各类型公司 — 评分分布箱线图"

        order = ["2D", "3D", "三渲二"] if group_key == "company_type" else ["年度推荐", "佳作", "还行", "能看", "不明", "拉了", "史"]

        fig, ax = plt.subplots(figsize=(10, 6))
        plot_data = defaultdict(list)
        for d in data:
            plot_data[d[group_key]].append(d["rating_score"])

        # Filter to ordered keys that have data
        ordered_data = []
        ordered_labels = []
        for key in order:
            if key in plot_data and plot_data[key]:
                ordered_data.append(plot_data[key])
                ordered_labels.append(key)

        bp = ax.boxplot(ordered_data, labels=ordered_labels, patch_artist=True,
                        medianprops={"color": t["text"], "linewidth": 2})

        for i, patch in enumerate(bp["boxes"]):
            color = t["palette"][i % len(t["palette"])]
            patch.set_facecolor(color)
            patch.set_alpha(0.7)

        ax.set_title(title, fontsize=16, fontweight="bold", pad=15)
        ax.set_ylabel("评分", fontsize=12)
        ax.grid(axis="y", alpha=0.3)
        ax.axhline(y=0, color=t["text"], linestyle="--", alpha=0.5, linewidth=1)

        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor=t["bg"])
        plt.close(fig)
        buf.seek(0)
        return buf.getvalue(), "image/png"

    @staticmethod
    async def chart_compare_radar(db: AsyncSession, ids: list[int], theme: str = "light") -> tuple[bytes, str]:
        """Generate multi-company comparison radar chart."""
        t = _get_theme(theme)
        _setup_mpl_style(t)

        comp_result = await db.execute(select(Company).where(Company.id.in_(ids)))
        companies = {c.id: c for c in comp_result.scalars().all()}

        works_result = await db.execute(
            select(Work).where(
                Work.company_id.in_(ids),
                Work.rating_score.isnot(None),
            )
        )
        works = works_result.scalars().all()

        comp_works = defaultdict(list)
        for w in works:
            comp_works[w.company_id].append(w)

        categories = ["平均评分", "作品数量", "推荐率", "良品率", "稳定性", "最高分"]
        n = len(categories)
        angles = np.linspace(0, 2 * np.pi, n, endpoint=False).tolist()
        angles += angles[:1]

        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw={"projection": "polar"})
        ax.set_theta_offset(np.pi / 2)
        ax.set_theta_direction(-1)

        for i, cid in enumerate(ids):
            comp = companies.get(cid)
            if not comp:
                continue
            cw = comp_works.get(cid, [])
            if not cw:
                continue

            scores = [float(w.rating_score) for w in cw if w.rating_score is not None]
            avg_s = np.mean(scores)
            rec_r = sum(1 for w in cw if w.rating_label == "年度推荐") / max(len(cw), 1)
            good_r = sum(1 for w in cw if w.rating_label in ("佳作", "还行")) / max(len(cw), 1)
            stability = 1 - min(np.std(scores) / 4, 1) if len(scores) > 1 else 0.5

            vals = [
                min(max((avg_s + 2) / 8, 0), 1),
                min(len(cw) / 30, 1),
                rec_r,
                good_r,
                stability,
                min(max((max(scores) + 2) / 8, 0), 1),
            ]
            vals.append(vals[0])

            color = t["palette"][i % len(t["palette"])]
            ax.fill(angles, vals, color=color, alpha=0.15)
            ax.plot(angles, vals, color=color, linewidth=2, label=comp.name)

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories, fontsize=10)
        ax.set_ylim(0, 1)
        ax.set_title("多公司对比雷达图", fontsize=14, fontweight="bold", pad=20, color=t["text"])
        ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1), fontsize=9)

        buf = io.BytesIO()
        fig.savefig(buf, format="svg", dpi=150, bbox_inches="tight", facecolor=t["bg"])
        plt.close(fig)
        buf.seek(0)
        return buf.getvalue(), "image/svg+xml"

    @staticmethod
    async def chart_dashboard_html(db: AsyncSession) -> str:
        """Generate interactive Plotly dashboard HTML snippet."""
        data = await _get_company_works_data(db)

        # Prepare data
        df_works = []
        for d in data:
            df_works.append(d)
        if not df_works:
            return "<div>暂无数据</div>"

        # Subplot grid
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=("年度评分趋势", "公司类型评分分布", "评级数量对比", "Top10 公司平均分"),
            specs=[[{"type": "scatter"}, {"type": "box"}],
                   [{"type": "bar"}, {"type": "bar"}]],
        )

        # 1. Yearly trend
        year_data = defaultdict(list)
        for d in data:
            if d["year"]:
                year_data[d["year"]].append(d["rating_score"])
        years = sorted(year_data.keys())
        avgs = [np.mean(year_data[y]) for y in years]
        fig.add_trace(go.Scatter(x=years, y=avgs, mode="lines+markers", name="年平均分",
                                 line=dict(color="#5b8def", width=2)), row=1, col=1)

        # 2. Box plot by type
        for i, ct in enumerate(["2D", "3D", "三渲二"]):
            type_scores = [d["rating_score"] for d in data if d["company_type"] == ct]
            if type_scores:
                fig.add_trace(go.Box(y=type_scores, name=ct, marker_color=["#5b8def", "#f06b4a", "#3cc9a6"][i]),
                              row=1, col=2)

        # 3. Rating count bar
        rating_order = ["年度推荐", "佳作", "还行", "能看", "不明", "拉了", "史"]
        rating_colors = {"年度推荐": "#f06b4a", "佳作": "#f5a623", "还行": "#3cc9a6", "能看": "#5b8def", "不明": "#999", "拉了": "#7c5ce0", "史": "#e8405d"}
        rating_counts = defaultdict(int)
        for d in data:
            if d["rating_label"]:
                rating_counts[d["rating_label"]] += 1
        fig.add_trace(go.Bar(
            x=rating_order, y=[rating_counts.get(l, 0) for l in rating_order],
            marker_color=[rating_colors[l] for l in rating_order], name="评级数量"
        ), row=2, col=1)

        # 4. Top 10 companies
        comp_avgs = defaultdict(list)
        for d in data:
            comp_avgs[d["company_name"]].append(d["rating_score"])
        top10 = sorted(comp_avgs.items(), key=lambda x: np.mean(x[1]), reverse=True)[:10]
        fig.add_trace(go.Bar(
            x=[name for name, _ in top10], y=[float(np.mean(s)) for _, s in top10],
            marker_color="#7c5ce0", name="平均评分"
        ), row=2, col=2)

        fig.update_layout(
            height=800,
            showlegend=False,
            template="plotly_white",
            title_text="行业仪表盘",
            title_font_size=20,
        )
        fig.update_xaxes(tickangle=45)

        return fig.to_html(full_html=False, include_plotlyjs="cdn")

    @staticmethod
    async def chart_report_pdf(db: AsyncSession) -> tuple[bytes, str]:
        """Generate multi-page PDF report."""
        data = await _get_company_works_data(db)
        if not data:
            return b"", "application/pdf"

        buf = io.BytesIO()

        # Use PdfPages for multi-page report
        from matplotlib.backends.backend_pdf import PdfPages

        with PdfPages(buf) as pdf:
            # Page 1: Overview statistics
            _setup_mpl_style(LIGHT_THEME)

            fig, axes = plt.subplots(2, 2, figsize=(11, 8.5))
            fig.suptitle("中国动画公司作品分析报告", fontsize=18, fontweight="bold", y=0.98)

            # Yearly trend
            year_data = defaultdict(list)
            for d in data:
                if d["year"]:
                    year_data[d["year"]].append(d["rating_score"])
            years = sorted(year_data.keys())
            avgs = [np.mean(year_data[y]) for y in years]
            axes[0, 0].plot(years, avgs, "o-", color="#5b8def", linewidth=2)
            axes[0, 0].set_title("年度平均评分趋势")
            axes[0, 0].axhline(y=0, color="gray", linestyle="--", alpha=0.5)

            # Rating distribution pie
            rating_counts = defaultdict(int)
            for d in data:
                if d["rating_label"]:
                    rating_counts[d["rating_label"]] += 1
            labels = ["年度推荐", "佳作", "还行", "能看", "不明", "拉了", "史"]
            vals = [rating_counts.get(l, 0) for l in labels]
            colors = ["#f06b4a", "#f5a623", "#3cc9a6", "#5b8def", "#999", "#7c5ce0", "#e8405d"]
            axes[0, 1].pie(vals, labels=labels, colors=colors, autopct="%1.1f%%")
            axes[0, 1].set_title("评级分布")

            # Type distribution
            type_counts = defaultdict(int)
            for d in data:
                type_counts[d["company_type"]] += 1
            axes[1, 0].bar(type_counts.keys(), type_counts.values(), color=["#5b8def", "#f06b4a", "#3cc9a6"])
            axes[1, 0].set_title("公司类型分布")

            # Score histogram
            all_scores = [d["rating_score"] for d in data]
            axes[1, 1].hist(all_scores, bins=20, color="#7c5ce0", alpha=0.7, edgecolor="white")
            axes[1, 1].set_title("评分直方图")
            axes[1, 1].axvline(x=0, color="red", linestyle="--", alpha=0.5)

            plt.tight_layout()
            pdf.savefig(fig)
            plt.close(fig)

            # Page 2: Top companies table
            fig, ax = plt.subplots(figsize=(11, 8.5))
            ax.axis("off")
            comp_avgs = defaultdict(list)
            for d in data:
                comp_avgs[d["company_name"]].append(d["rating_score"])
            top15 = sorted(comp_avgs.items(), key=lambda x: np.mean(x[1]), reverse=True)[:15]

            table_data = []
            for i, (name, scores) in enumerate(top15):
                table_data.append([str(i + 1), name, f"{np.mean(scores):.2f}", str(len(scores)),
                                   f"{np.std(scores):.2f}" if len(scores) > 1 else "N/A"])

            table = ax.table(
                cellText=table_data,
                colLabels=["排名", "公司名称", "平均评分", "作品数", "标准差"],
                cellLoc="center",
                loc="center",
            )
            table.auto_set_font_size(False)
            table.set_fontsize(10)
            table.scale(1, 1.8)
            ax.set_title("Top 15 公司排名", fontsize=16, fontweight="bold", y=1.02)

            pdf.savefig(fig)
            plt.close(fig)

        buf.seek(0)
        return buf.getvalue(), "application/pdf"
