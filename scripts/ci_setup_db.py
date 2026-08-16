import asyncio
import os
import asyncpg

async def setup():
    owner_url = os.environ.get("OWNER_DATABASE_URL", "postgresql+asyncpg://ks_owner:ks_password@localhost:5432/ks_foodops_test")
    # Convert sqlalchemy url to raw asyncpg
    raw_url = owner_url.replace("postgresql+asyncpg://", "postgresql://")
    print(f"Connecting to database via {raw_url}...")
    
    conn = await asyncpg.connect(raw_url)
    try:
        await conn.execute("""
            DO $$ 
            BEGIN 
                IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'ksfoodops_app') THEN 
                    CREATE ROLE ksfoodops_app WITH LOGIN PASSWORD 'ks_password'; 
                END IF; 
            END $$;
        """)
        print("Role ksfoodops_app verified/created successfully!")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(setup())
