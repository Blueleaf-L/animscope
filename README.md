# 中国主流网络动画公司作品分析平台 v2

> 基于 72 家中国动画公司、586 部作品数据的 Web 分析平台
>
> **在线访问**: https://blueleaf-l.github.io/animscope/

## 项目简介

纯静态网站，托管于 GitHub Pages。所有分析数据通过 Python 脚本预计算为 JSON 文件，前端直接加载渲染。

## 功能页面

| 页面 | 说明 |
|------|------|
| 首页概览 | 行业统计卡片 + 评级环形图 + 类型分布 + 年度趋势 |
| 公司总览 | 搜索/筛选/排序 + 气泡图（支持全部/当前页切换） |
| 公司详情 | 雷达图（中英双语）+ 作品时间线 + 年份滑块筛选 |
| 公司排行 | 推荐/评分/翻车 三Tab 排行卡片（含 Z-Score 指标） |
| 趋势分析 | 类型年度折线 + 公司评分热力图（点击下钻） |
| 公司对比 | 多选对比 + 雷达图 + Cohen's d 差异分析 |
| 作品搜索 | 关键词/年份/评级/类型 多条件搜索 + 智能分页 |
| 分析报告 | 预生成图表 PNG + 评级体系说明 |

## 评分体系 (V2)

| 评级 | 分值 | 说明 |
|------|------|------|
| 年度推荐 | 3.0 ~ 5.0 | 推荐作品 |
| 佳作 | 1.5 ~ 2.5 | 优秀作品 |
| 还行 | 0.5 | 中规中矩 |
| 能看 | -0.5 | 勉强可看 |
| 不明 | 0.0 | 基线（未知质量） |
| 拉了 | -1.0 | 质量差 |
| 史 | -2.0 | 极差 |

## 公司类型

| 类型 | 数量 | 说明 |
|------|------|------|
| 2D | 31 家 | 全部作品均为 2D |
| 3D | 28 家 | 全部作品均为 3D |
| 三渲二 | 6 家 | 全部作品均为三渲二 |
| 混合型 | 7 家 | 制作了不止一种类型的作品 |

## 项目结构

```
├── index.html / css / js/        # 网站文件
├── data/static/                   # 预计算静态数据（JSON + PNG）
├── scripts/
│   ├── convert_excel_to_json.py   # Excel -> JSON
│   └── build_static.py           # JSON -> 分析数据 + 图表
├── frontend/                      # 前端源文件（编辑用）
├── data/
│   ├── companies.json / works.json
│   └── 公司的完整作品及对应制作类型.json  # 人工校对类型
├── README.md
└── 项目规划.md
```

## 数据更新流程

当 Excel 数据更新后：

```powershell
cd "d:/dev/Project/主流国产动画公司作品评价网站"

# 1. Excel -> JSON
python scripts/convert_excel_to_json.py

# 2. JSON -> 静态数据 + 图表
python scripts/build_static.py

# 3. 同步到网站根目录
Copy-Item -Path frontend/* -Destination . -Recurse -Force

# 4. 推送
git add -A; git commit -m "Update data"; git push
```

## 技术栈

| 层 | 技术 |
|---|---|
| 数据预处理 | Python (pandas, numpy, scipy) |
| 图表预渲染 | matplotlib + seaborn |
| 交互式图表 | ECharts 5 |
| 前端 | Vanilla HTML/CSS/JS |
| 部署 | GitHub Pages (免费) |
