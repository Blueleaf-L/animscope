# 中国主流网络动画公司作品分析平台 v2

> 基于 72 家中国动画公司、586 部作品数据的 Web 分析平台
>
> **在线访问**: https://blueleaf-l.github.io/animscope/

## 项目简介

纯静态网站，托管于 GitHub Pages。所有分析数据通过 Python 脚本预计算为 JSON 文件，前端直接加载渲染，无需服务器和数据库。

## 功能页面

| 页面 | 说明 |
|------|------|
| 首页概览 | 行业统计卡片 + 评级环形图 + 类型分布 + 年度趋势 |
| 公司总览 | 搜索/筛选/排序 + 气泡图（支持全部/当前页切换） |
| 公司详情 | 雷达图 + 作品时间线 + 年份滑块筛选 |
| 作品排行 | 推荐/评分/翻车 三Tab 排行卡片 |
| 趋势分析 | 类型年度折线 + 公司评分热力图（点击下钻） |
| 公司对比 | 多选对比 + 雷达图 + Cohen's d 差异分析 |
| 作品搜索 | 关键词/年份/评级/类型 多条件搜索 |
| 分析报告 | 预生成图表 PNG + 评级体系说明 |

## 项目结构

```
├── index.html              # 网站入口
├── css/                    # 样式（CSS 变量体系，支持暗色模式）
├── js/                     # JavaScript 模块
│   ├── config.js           # 全局配置（颜色从 CSS 动态读取）
│   ├── api.js              # 静态数据加载器
│   ├── charts.js           # ECharts 渲染引擎
│   ├── views.js            # DOM 渲染工具
│   ├── router.js           # Hash 路由
│   ├── app.js              # 入口
│   └── pages/              # 8 个页面模块
├── data/static/            # 预计算的静态 JSON 数据
│   ├── overview.json       # 首页数据
│   ├── companies_full.json # 全部公司含作品
│   ├── rankings_*.json     # 排行数据
│   ├── trends.json         # 趋势数据
│   ├── insights.json       # 深度分析数据
│   └── charts/             # 预渲染图表 PNG
├── scripts/
│   ├── convert_excel_to_json.py  # Excel → JSON 转换器
│   └── build_static.py           # 生成所有静态数据文件
├── data/
│   ├── companies.json      # 公司数据（JSON）
│   └── works.json          # 作品数据（JSON）
└── docs/                   # GitHub Pages 部署目录（= frontend/ 镜像）
```

## 数据更新流程

当 Excel 数据文件更新后：

```bash
# 1. 转换 Excel → JSON
python scripts/convert_excel_to_json.py

# 2. 生成静态数据 + 图表
python scripts/build_static.py

# 3. 同步到部署目录并推送
rm -rf docs/* && cp -r frontend/* docs/
git add -A && git commit -m "Update data" && git push
```

## 技术栈

| 层 | 技术 |
|---|---|
| 数据预处理 | Python (pandas, numpy, scipy) |
| 图表预渲染 | matplotlib + seaborn |
| 交互式图表 | ECharts 5 (CDN) |
| 前端 | Vanilla HTML/CSS/JS |
| 部署 | GitHub Pages |

## 许可证

数据来源：主流动画公司作品推荐表 · 仅供分析参考
