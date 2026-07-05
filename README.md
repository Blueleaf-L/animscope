# 中国动画公司作品分析平台 v2.0

基于 **72 家中国动画公司、586 部作品** 数据的 Web 分析平台。前后端分离 + 数据库驱动。

## 技术栈

| 层 | 技术 |
|---|---|
| 数据库 | PostgreSQL 16 |
| 后端 | FastAPI + SQLAlchemy 2.0 (async) + asyncpg |
| 前端 | Vanilla HTML/CSS/JS + ECharts 5 (CDN) |
| Python 分析 | pandas + numpy + scipy |
| Python 可视化 | matplotlib / seaborn / plotly |
| 部署 | Docker Compose |

## 快速开始

### 前置条件

- Docker & Docker Compose
- Excel 数据文件 (`data/主流动画公司作品推荐表.xlsx`)

### 一键部署

```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑 .env 修改密码

# 2. 放置 Excel 数据文件
mkdir -p data
cp /path/to/主流动画公司作品推荐表.xlsx data/

# 3. 启动所有服务
docker compose up -d

# 4. 导入数据
docker compose exec backend python scripts/init_db.py

# 5. 访问
# 前端: http://localhost
# API文档: http://localhost:8000/docs
# 健康检查: http://localhost:8000/api/health
```

### 本地开发

```bash
# 后端
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 导入数据 (需要本地 PostgreSQL)
python scripts/init_db.py data/主流动画公司作品推荐表.xlsx

# 前端 (直接打开或使用任意静态服务器)
cd frontend
python -m http.server 3000

# 运行测试
cd backend
pytest tests/ -v
```

## 项目结构

```
├── docker-compose.yml
├── backend/                  # FastAPI 后端
│   ├── app/
│   │   ├── main.py          # 应用入口
│   │   ├── config.py        # 配置
│   │   ├── database.py      # 数据库连接
│   │   ├── models/          # SQLAlchemy 模型
│   │   ├── schemas/         # Pydantic 校验
│   │   ├── routers/         # API 路由
│   │   ├── services/        # 业务逻辑 + 分析引擎 + 图表生成
│   │   └── utils/           # 工具函数 + 数据导入
│   └── tests/               # 测试 (15+ 用例)
├── frontend/                 # 前端 (Vanilla JS)
│   ├── index.html
│   ├── css/style.css        # CSS 变量体系
│   └── js/
│       ├── config.js        # 全局配置 (颜色从 CSS 动态读取)
│       ├── api.js           # API 调用层 (超时+重试+错误态)
│       ├── charts.js        # ECharts 渲染 (响应式降级)
│       ├── views.js         # DOM 渲染
│       ├── router.js        # Hash 路由
│       ├── app.js           # 入口
│       └── pages/           # 8 个页面模块
├── nginx/                    # Nginx 配置
├── scripts/                  # 数据库初始化脚本
├── data/                     # Excel 数据
└── .github/workflows/       # CI/CD
```

## API 端点

| 分类 | 端点数 | 说明 |
|---|---|---|
| 公司 | 3 | 列表(含works_count)、详情+作品、作品筛选 |
| 作品 | 2 | 全库搜索、单作品详情 |
| 分析 | 6 | 概览、排行、趋势、对比、差异、洞察 |
| 图表 | 7 | PNG/SVG/HTML/PDF 图表 |
| 健康检查 | 1 | `/api/health` |

完整 API 文档：启动后端后访问 `http://localhost:8000/docs`

## 页面功能 (8 页)

| 页面 | Hash | 功能 |
|---|---|---|
| 首页概览 | `#overview` | 环形图 + 玫瑰图 + 双轴趋势 + 行业诊断 |
| 公司总览 | `#companies` | 气泡图 + 筛选/搜索/排序表格 |
| 公司详情 | `#company/:id` | 雷达图 + 时间线 + 年份滑块筛选 |
| 作品排行 | `#rankings` | Tab切换(推荐/综合/翻车) 卡片网格 |
| 趋势分析 | `#trends` | 类型折线 + 热力图 (点击下钻) |
| 公司对比 | `#compare` | 多雷达 + 分组柱 + Cohen's d 差异分析 |
| 作品搜索 | `#search` | 多条件筛选搜索表格 |
| 分析报告 | `#report` | Plotly 仪表盘预览 + PDF 下载 |

## 特性

- 🌓 暗色模式：CSS 变量体系，一键切换，图表实时适配
- 📱 响应式：桌面/平板/手机三级断点，图表智能降级
- 🔗 交互闭环：图表点击 → 页面跳转 → 数据联动
- ⚡ 异步高性能：FastAPI + asyncpg + 索引优化
- 📊 多种可视化：ECharts (交互) + matplotlib (报告) + plotly (仪表盘)
- 🐳 一键部署：Docker Compose 三服务编排
- 🧪 测试覆盖：15+ 测试用例，临时数据库隔离

## 许可证

数据来源：主流动画公司作品推荐表 · 仅供分析参考
