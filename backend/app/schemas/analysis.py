from typing import Optional

from pydantic import BaseModel


class OverviewStats(BaseModel):
    total_companies: int
    total_works: int
    avg_score: float
    recommended_count: int
    good_count: int
    trash_count: int


class TypeDistribution(BaseModel):
    type: str
    count: int
    avg_score: float


class YearlyTrend(BaseModel):
    year: int
    count: int
    avg_score: float


class RatingDistribution(BaseModel):
    label: str
    count: int
    percentage: float


class OverviewResponse(BaseModel):
    stats: OverviewStats
    type_distribution: list[TypeDistribution]
    yearly_trends: list[YearlyTrend]
    rating_distribution: list[RatingDistribution]
    diagnostics: list[str]


class RankingItem(BaseModel):
    rank: int
    company_id: int
    company_name: str
    company_type: str
    works_count: int
    avg_score: float
    recommended_count: int
    trash_count: int
    z_score: Optional[float] = None


class RankingResponse(BaseModel):
    items: list[RankingItem]
    tab: str


class TrendItem(BaseModel):
    year: int
    type_2d_count: int = 0
    type_2d_avg: float = 0
    type_3d_count: int = 0
    type_3d_avg: float = 0
    type_hybrid_count: int = 0
    type_hybrid_avg: float = 0
    total_count: int = 0
    total_avg: float = 0


class HeatmapCell(BaseModel):
    company_name: str
    year: int
    avg_score: float
    count: int


class TrendsResponse(BaseModel):
    by_type: list[TrendItem]
    heatmap_data: list[HeatmapCell]
    companies: list[str]
    years: list[int]


class CompareCompany(BaseModel):
    id: int
    name: str
    type: str
    works_count: int
    avg_score: float
    recommended_ratio: float
    trash_ratio: float
    yearly_avg: list[dict]


class CompareResponse(BaseModel):
    companies: list[CompareCompany]


class DiffDimension(BaseModel):
    dimension: str
    company_a_value: float
    company_b_value: float
    diff: float
    winner: str  # "a" | "b" | "tie"


class DiffResponse(BaseModel):
    cohens_d: float
    company_a_name: str
    company_b_name: str
    dimensions: list[DiffDimension]
    volatility_a: float
    volatility_b: float


class CompanyInsight(BaseModel):
    company_id: int
    company_name: str
    company_type: str
    z_score: float
    rank: int
    avg_score: float
    trend_slope: float
    risk_level: str  # "low" | "medium" | "high"
    track_benchmark: float
    track_percentile: float


class InsightsResponse(BaseModel):
    top_companies: list[CompanyInsight]
    risk_alerts: list[CompanyInsight]
    track_benchmarks: dict[str, float]
