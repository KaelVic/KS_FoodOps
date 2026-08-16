import asyncio
import argparse
import sys
from sqlalchemy import select
from packages.tenant.database import async_session_maker
from packages.security.models import AppUser
from packages.security.password import hash_password
from packages.tenant.service import TenantService

async def main():
    parser = argparse.ArgumentParser(description="Create a user and default restaurant tenant")
    parser.add_argument("--email", required=True, help="User email")
    parser.add_argument("--password", required=True, help="User password")
    parser.add_argument("--name", default="Administrador", help="Full name")
    parser.add_argument("--restaurant", default="Meu Restaurante", help="Restaurant name")

    args = parser.parse_args()

    async with async_session_maker() as session:
        # Check existing
        result = await session.execute(select(AppUser).where(AppUser.email == args.email))
        existing = result.scalar_one_or_none()
        if existing:
            print(f"[ERRO] Usuário com email '{args.email}' já existe no sistema.")
            sys.exit(1)

        # Create user
        hashed = hash_password(args.password)
        user = AppUser(
            email=args.email,
            password_hash=hashed,
            full_name=args.name,
            is_active=True
        )
        session.add(user)
        await session.flush()

        # Create Tenant & Membership
        res = await TenantService.create_tenant_onboarding(
            session, str(user.id), args.restaurant
        )
        await session.commit()

        print("==================================================")
        print(" Usuário e Restaurante criados com sucesso!")
        print("==================================================")
        print(f" Email:       {args.email}")
        print(f" Nome:        {args.name}")
        print(f" Restaurante: {res['tenant_name']} (ID: {res['tenant_id']})")
        print(f" Role:        admin")
        print("==================================================")

if __name__ == "__main__":
    asyncio.run(main())
