"""Quick test: can we connect to local PostgreSQL?"""
import asyncio
import asyncpg

async def main():
    # Try different auth methods
    attempts = [
        ("postgres", None),
        ("postgres", "postgres"),
        ("postgres", "admin"),
        ("postgres", "123456"),
        ("lijingye", None),
    ]
    for user, pwd in attempts:
        try:
            conn = await asyncio.wait_for(
                asyncpg.connect(user=user, password=pwd, host='localhost', timeout=3),
                timeout=5
            )
            ver = await conn.fetchval('SELECT version()')
            print(f"SUCCESS: user={user}, password={'****' if pwd else '(none)'}")
            print(f"  {ver}")

            # Check if our DB exists
            dbs = await conn.fetch("SELECT datname FROM pg_database")
            db_names = [d['datname'] for d in dbs]
            print(f"  Databases: {db_names}")

            if 'animation_analysis' not in db_names:
                await conn.execute('CREATE DATABASE animation_analysis')
                print("  Created database: animation_analysis")

            await conn.close()
            return user, pwd
        except Exception as e:
            print(f"FAIL: user={user}, password={'****' if pwd else '(none)'}: {type(e).__name__}")

    print("\nNo valid connection found!")
    return None, None

if __name__ == '__main__':
    asyncio.run(main())
