#!/usr/bin/env python3
"""
数据库初始化脚本：建表 → Excel→JSON 转换 → JSON→DB 导入

完整流水线:
    1. 创建数据库表 (通过 FastAPI 的 Base.metadata.create_all)
    2. 运行 convert_excel_to_json.py 把 Excel 转成干净 JSON
    3. 调用 data_import.import_from_json() 导入 PostgreSQL

用法:
    python scripts/init_db.py                          # 自动查找 data/ 下的 .xlsx
    python scripts/init_db.py path/to/data.xlsx        # 指定 Excel 文件
    python scripts/init_db.py --json-only              # 仅转换 JSON，不导入 DB
    python scripts/init_db.py --import-only            # 仅从已有 JSON 导入 DB

环境变量:
    DATABASE_URL  — PostgreSQL 连接字符串（Docker 内自动设置）
"""

import asyncio
import os
import sys
import subprocess
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.config import settings
from app.database import Base
from app.models import Company, Work  # Ensure models are registered with Base.metadata
from app.utils.data_import import import_from_json, import_from_excel


async def main():
    # Determine mode
    json_only = "--json-only" in sys.argv
    import_only = "--import-only" in sys.argv

    # Determine database URL
    db_url = os.getenv("DATABASE_URL", settings.DATABASE_URL)
    if "db:5432" in db_url and not os.getenv("DOCKER_RUN"):
        db_url = db_url.replace("@db:5432", "@localhost:5432")

    # Determine Excel path
    data_dir = Path(__file__).parent.parent / "data"
    xlsx_files = list(data_dir.glob("*.xlsx"))
    excel_path = None
    if len(sys.argv) > 1 and not sys.argv[-1].startswith("--"):
        excel_path = sys.argv[-1]
    elif xlsx_files:
        excel_path = str(xlsx_files[0])

    json_dir = data_dir
    companies_json = json_dir / "companies.json"
    works_json = json_dir / "works.json"

    # ==================================================═
    # Step 1: Excel → JSON
    # ==================================================═

    if not import_only:
        if excel_path:
            print(f"\n{'='*60}")
            print(f"Step 1/3: Excel → JSON 转换")
            print(f"{'='*60}")

            converter_script = Path(__file__).parent / "convert_excel_to_json.py"
            result = subprocess.run(
                [sys.executable, str(converter_script), excel_path],
                capture_output=False,
                cwd=str(Path(__file__).parent.parent),
            )
            if result.returncode != 0:
                print(f"[ERR] Excel 转换失败 (exit code {result.returncode})")
                sys.exit(1)
        else:
            print("[WARN]  未找到 .xlsx 文件，跳过 Excel→JSON 转换")
            print(f"   请将 Excel 文件放入: {data_dir}")

    if json_only:
        print("\n[OK] JSON 转换完成（--json-only 模式，跳过数据库导入）")
        return

    # ==================================================═
    # Step 2: Create tables
    # ==================================================═

    print(f"\n{'='*60}")
    print(f"Step 2/3: 创建数据库表")
    print(f"{'='*60}")

    engine = create_async_engine(db_url, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("  [OK] 数据库表创建完成")

    # ==================================================═
    # Step 3: JSON → DB
    # ==================================================═

    print(f"\n{'='*60}")
    print(f"Step 3/3: JSON → PostgreSQL 导入")
    print(f"{'='*60}")

    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    if companies_json.exists() and works_json.exists():
        # ── Primary path: import from clean JSON ──
        async with async_session() as session:
            stats = await import_from_json(session, str(companies_json), str(works_json))

        print(f"\n[==] 导入统计:")
        print(f"  公司: {stats['companies_added']} 家")
        print(f"  作品: {stats['works_added']} 新增, {stats.get('works_skipped', 0)} 跳过")
        if stats["errors"]:
            print(f"  [WARN] 错误: {len(stats['errors'])} 条")
            for err in stats["errors"][:5]:
                print(f"     - {err}")

    elif excel_path:
        # ── Fallback: direct Excel import ──
        print("  [WARN] JSON 文件不存在，使用备用 Excel 直接导入...")
        async with async_session() as session:
            stats = await import_from_excel(session, excel_path)

        print(f"\n[==] 导入统计:")
        print(f"  公司: {stats['companies_added']} 家")
        print(f"  作品: {stats['works_added']} 部")
        if stats["errors"]:
            print(f"  [WARN] 错误: {len(stats['errors'])} 条")
            for err in stats["errors"][:5]:
                print(f"     - {err}")
    else:
        print("  [ERR] 没有可导入的数据（JSON 和 Excel 都不存在）")
        print(f"     请将 Excel 文件放入: {data_dir}")
        print(f"     或运行: python scripts/convert_excel_to_json.py")

    await engine.dispose()
    print(f"\n{'='*60}")
    print("[OK] 数据库初始化完成！")
    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())
