"""Test SQLite backend."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
os.chdir(os.path.join(os.path.dirname(__file__), '..', 'backend'))

import asyncio
from app.database import engine, Base
from app.models import Company, Work

async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created: OK")

    from app.utils.data_import import import_from_json
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
    sm = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with sm() as session:
        stats = await import_from_json(session, "../data/companies.json", "../data/works.json")
        print(f"Import: {stats['companies_added']} companies, {stats['works_added']} works")
        print(f"Errors: {len(stats['errors'])}")

    await engine.dispose()
    print("SQLite test: PASSED")

asyncio.run(main())
