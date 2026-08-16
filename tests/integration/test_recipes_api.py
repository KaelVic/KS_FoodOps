import pytest
import uuid
import hashlib
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from sqlalchemy.future import select
from sqlalchemy import text
from io import BytesIO

from packages.tenant.database import async_session_maker
from modules.recipes.models import Recipe, RecipeVersion, RecipeIngredient
from modules.catalog.models import SKU, UOM
from modules.inventory.models import StockBalanceProjection
from fastapi.testclient import TestClient
from apps.api.main import app

pytestmark = pytest.mark.asyncio

client = TestClient(app)

SAMPLE_NFE_XML = '''<?xml version="1.0" encoding="UTF-8"?>
<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00">
  <NFe>
    <infNFe versao="4.00" Id="NFe35240112345678000199550010001234561000123456">
      <ide>
        <cUF>35</cUF>
        <cNF>12345678</cNF>
        <natOp>VENDA</natOp>
        <mod>55</mod>
        <serie>1</serie>
        <nNF>123456</nNF>
        <dhEmi>2024-01-15T10:30:00-03:00</dhEmi>
        <tpNF>1</tpNF>
        <idDest>1</idDest>
        <cMunFG>3550308</cMunFG>
        <tpImp>1</tpImp>
        <tpEmis>1</tpEmis>
        <cDV>6</cDV>
        <tpAmb>2</tpAmb>
        <finNFe>1</finNFe>
        <indFinal>1</indFinal>
        <indPres>1</indPres>
        <procEmi>0</procEmi>
        <verProc>1.0</verProc>
      </ide>
      <emit>
        <CNPJ>12345678000199</CNPJ>
        <xNome>Farm Fresh</xNome>
        <xFant>Farm Fresh</xFant>
        <enderEmit>
          <xLgr>Rua das Flores</xLgr>
          <nro>123</nro>
          <xBairro>Centro</xBairro>
          <cMun>3550308</cMun>
          <xMun>Sao Paulo</xMun>
          <UF>SP</UF>
          <CEP>01000000</CEP>
          <cPais>1058</cPais>
          <xPais>BRASIL</xPais>
        </enderEmit>
        <IE>123456789</IE>
        <CRT>3</CRT>
      </emit>
      <dest>
        <CNPJ>98765432000188</CNPJ>
        <xNome>Cliente Teste</xNome>
        <enderDest>
          <xLgr>Av. Principal</xLgr>
          <nro>456</nro>
          <xBairro>Centro</xBairro>
          <cMun>3550308</cMun>
          <xMun>Sao Paulo</xMun>
          <UF>SP</UF>
          <CEP>02000000</CEP>
          <cPais>1058</cPais>
          <xPais>BRASIL</xPais>
        </enderDest>
        <indIEDest>1</indIEDest>
        <IE>987654321</IE>
      </dest>
      <det nItem="1">
        <prod>
          <cProd>P-001</cProd>
          <cEAN/>
          <xProd>TOMATE CARMEM KG</xProd>
          <NCM>07020000</NCM>
          <CEST>01.001.00</CEST>
          <CFOP>5102</CFOP>
          <uCom>KG</uCom>
          <qCom>10.000</qCom>
          <vUnCom>150.00</vUnCom>
          <vProd>1500.00</vProd>
          <cEANTrib/>
          <uTrib>KG</uTrib>
          <qTrib>10.000</qTrib>
          <vUnTrib>150.00</vUnTrib>
          <indTot>1</indTot>
        </prod>
        <imposto>
          <vTotTrib>0.00</vTotTrib>
        </imposto>
      </det>
      <total>
        <ICMSTot>
          <vBC>0.00</vBC>
          <vICMS>0.00</vICMS>
          <vICMSDeson>0.00</vICMSDeson>
          <vFCPUFDest>0.00</vFCPUFDest>
          <vICMSUFDest>0.00</vICMSUFDest>
          <vICMSUFRemet>0.00</vICMSUFRemet>
          <vFCP>0.00</vFCP>
          <vBCST>0.00</vBCST>
          <vST>0.00</vST>
          <vProd>1500.00</vProd>
          <vFrete>0.00</vFrete>
          <vSeg>0.00</vSeg>
          <vDesc>0.00</vDesc>
          <vII>0.00</vII>
          <vIPI>0.00</vIPI>
          <vIPIDevol>0.00</vIPIDevol>
          <vPIS>0.00</vPIS>
          <vCOFINS>0.00</vCOFINS>
          <vOutro>0.00</vOutro>
          <vNF>1500.00</vNF>
          <vTotTrib>0.00</vTotTrib>
        </ICMSTot>
      </total>
      <transp>
        <modFrete>0</modFrete>
      </transp>
      <pag>
        <detPag>
          <tPag>01</tPag>
          <vPag>1500.00</vPag>
        </detPag>
      </pag>
    </infNFe>
  </NFe>
  <protNFe versao="4.00">
    <infProt>
      <tpAmb>2</tpAmb>
      <verAplic>1.0</verAplic>
      <chNFe>35240112345678000199550010001234561000123456</chNFe>
      <dhRecbto>2024-01-15T10:31:00-03:00</dhRecbto>
      <nProt>135240000123456</nProt>
      <digVal>abc123</digVal>
      <cStat>100</cStat>
      <xMotivo>Autorizado o uso da NF-e</xMotivo>
    </infProt>
  </protNFe>
</nfeProc>'''


async def setup_test_data(session, tenant_id: uuid.UUID):
    """Setup UOMs and SKUs for recipe testing."""
    # Create UOMs
    gram_id = uuid.uuid4()
    kg_id = uuid.uuid4()
    portion_id = uuid.uuid4()
    
    await session.execute(
        text("INSERT INTO uoms (id, tenant_id, name, symbol, base_type) VALUES (:id, :t_id, 'Gram', 'g', 'mass')"),
        {"id": str(gram_id), "t_id": str(tenant_id)}
    )
    await session.execute(
        text("INSERT INTO uoms (id, tenant_id, name, symbol, base_type) VALUES (:id, :t_id, 'Kilogram', 'kg', 'mass')"),
        {"id": str(kg_id), "t_id": str(tenant_id)}
    )
    await session.execute(
        text("INSERT INTO uoms (id, tenant_id, name, symbol, base_type) VALUES (:id, :t_id, 'Portion', 'pt', 'count')"),
        {"id": str(portion_id), "t_id": str(tenant_id)}
    )
    
    # Create a location for stock balance
    location_id = uuid.uuid4()
    business_unit_id = uuid.uuid4()
    await session.execute(
        text("INSERT INTO business_units (id, tenant_id, name) VALUES (:id, :t_id, 'Test BU')"),
        {"id": str(business_unit_id), "t_id": str(tenant_id)}
    )
    await session.execute(
        text("INSERT INTO locations (id, tenant_id, business_unit_id, name) VALUES (:id, :t_id, :bu_id, 'Test Location')"),
        {"id": str(location_id), "t_id": str(tenant_id), "bu_id": str(business_unit_id)}
    )
    
    # Create SKUs with stock balance for cost calculation
    beef_id = uuid.uuid4()
    cheese_id = uuid.uuid4()
    bun_id = uuid.uuid4()
    
    await session.execute(
        text("INSERT INTO skus (id, tenant_id, name, base_uom_id, is_active) VALUES (:id, :t_id, 'Ground Beef', :uom_id, true)"),
        {"id": str(beef_id), "t_id": str(tenant_id), "uom_id": str(gram_id)}
    )
    await session.execute(
        text("INSERT INTO skus (id, tenant_id, name, base_uom_id, is_active) VALUES (:id, :t_id, 'Cheddar Cheese', :uom_id, true)"),
        {"id": str(cheese_id), "t_id": str(tenant_id), "uom_id": str(gram_id)}
    )
    await session.execute(
        text("INSERT INTO skus (id, tenant_id, name, base_uom_id, is_active) VALUES (:id, :t_id, 'Burger Bun', :uom_id, true)"),
        {"id": str(bun_id), "t_id": str(tenant_id), "uom_id": str(portion_id)}
    )
    
    # Add stock balance projections for cost calculation
    # Ground beef: 10kg at $50/kg = $500 total
    await session.execute(
        text("""INSERT INTO stock_balance_projections (id, tenant_id, location_id, sku_id, quantity, total_value)
                VALUES (:id, :t_id, :loc_id, :sku_id, :qty, :val)"""),
        {"id": str(uuid.uuid4()), "t_id": str(tenant_id), "loc_id": str(location_id), "sku_id": str(beef_id), "qty": "10000", "val": "50000"}
    )
    # Cheese: 5kg at $80/kg = $400 total
    await session.execute(
        text("""INSERT INTO stock_balance_projections (id, tenant_id, location_id, sku_id, quantity, total_value)
                VALUES (:id, :t_id, :loc_id, :sku_id, :qty, :val)"""),
        {"id": str(uuid.uuid4()), "t_id": str(tenant_id), "loc_id": str(location_id), "sku_id": str(cheese_id), "qty": "5000", "val": "40000"}
    )
    # Buns: 100 units at $1.50 each = $150 total
    await session.execute(
        text("""INSERT INTO stock_balance_projections (id, tenant_id, location_id, sku_id, quantity, total_value)
                VALUES (:id, :t_id, :loc_id, :sku_id, :qty, :val)"""),
        {"id": str(uuid.uuid4()), "t_id": str(tenant_id), "loc_id": str(location_id), "sku_id": str(bun_id), "qty": "100", "val": "150"}
    )
    
    return gram_id, kg_id, portion_id, beef_id, cheese_id, bun_id


async def create_tenant_and_membership(tenant_id: uuid.UUID, user_id: str = "test-user-123"):
    """Create tenant and membership using owner engine (bypasses RLS)."""
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
    from packages.tenant.database import OWNER_DATABASE_URL
    from sqlalchemy.pool import NullPool
    from sqlalchemy import text
    
    test_owner_engine = create_async_engine(OWNER_DATABASE_URL, echo=False, poolclass=NullPool)
    OwnerSessionLocal = async_sessionmaker(
        autocommit=False, autoflush=False, bind=test_owner_engine, class_=AsyncSession
    )
    
    async with OwnerSessionLocal() as session:
        await session.execute(
            text("INSERT INTO tenants (id, name) VALUES (:id, 'Tenant Recipe Test')"),
            {"id": str(tenant_id)}
        )
        await session.execute(
            text("INSERT INTO tenant_memberships (id, tenant_id, user_id, role) VALUES (:id, :t_id, :uid, 'admin')"),
            {"id": str(uuid.uuid4()), "t_id": str(tenant_id), "uid": user_id}
        )
        await session.commit()


async def get_auth_headers(tenant_id: uuid.UUID, user_id: str = "test-user-123") -> dict:
    """Create auth headers with a mock token and tenant ID."""
    import jwt
    import os
    secret = os.environ.get("JWT_SECRET", "dummy_secret_for_development_32_bytes_long_min!")
    algorithm = os.environ.get("JWT_ALGORITHM", "HS256")
    
    payload = {
        "sub": user_id,
        "email": "test@ksfoodops.local",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1)
    }
    token = jwt.encode(payload, secret, algorithm=algorithm)
    
    return {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": str(tenant_id)
    }


async def test_create_recipe():
    """Test creating a recipe."""
    tenant_id = uuid.uuid4()
    await create_tenant_and_membership(tenant_id)
    
    async with async_session_maker() as session:
        await session.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": str(tenant_id)})
        await setup_test_data(session, tenant_id)
        await session.commit()
    
    headers = await get_auth_headers(tenant_id)
    response = client.post("/recipes", headers=headers, json={
        "name": "Classic Burger",
        "type": "MENU_ITEM",
        "pos_code": "POS-BURGER-01"
    })
    
    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
    data = response.json()
    assert data["name"] == "Classic Burger"
    assert data["type"] == "MENU_ITEM"
    assert data["pos_code"] == "POS-BURGER-01"
    assert "id" in data
    
    return data["id"]


async def test_list_recipes():
    """Test listing recipes."""
    tenant_id = uuid.uuid4()
    await create_tenant_and_membership(tenant_id)
    
    async with async_session_maker() as session:
        await session.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": str(tenant_id)})
        await setup_test_data(session, tenant_id)
        
        # Create a recipe directly via service
        from modules.recipes.service import RecipeService
        service = RecipeService(session)
        recipe = await service.create_recipe(tenant_id, "Test Recipe", "MENU_ITEM", "POS-TEST-01")
        await session.commit()
    
    headers = await get_auth_headers(tenant_id)
    response = client.get("/recipes", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    
    # Check structure
    item = data[0]
    assert "id" in item
    assert "name" in item
    assert "type" in item
    assert "pos_code" in item
    assert "version_number" in item
    assert "yield_quantity" in item
    assert "portion_size" in item
    assert "portion_cost" in item
    assert "ingredients_count" in item
    
    assert item["name"] == "Test Recipe"
    assert item["type"] == "MENU_ITEM"
    assert item["pos_code"] == "POS-TEST-01"


async def test_get_recipe_detail():
    """Test getting recipe detail."""
    tenant_id = uuid.uuid4()
    await create_tenant_and_membership(tenant_id)
    
    async with async_session_maker() as session:
        await session.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": str(tenant_id)})
        gram_id, kg_id, portion_id, beef_id, cheese_id, bun_id = await setup_test_data(session, tenant_id)
        
        from modules.recipes.service import RecipeService
        service = RecipeService(session)
        recipe = await service.create_recipe(tenant_id, "Classic Burger", "MENU_ITEM", "POS-BURGER-01")
        
        # Publish a version
        version_data = {
            'yield_quantity': '1.0',
            'yield_uom_id': str(portion_id),
            'portion_size': '1.0',
            'portion_uom_id': str(portion_id)
        }
        ingredients = [
            {'sku_id': str(beef_id), 'quantity': '150.0', 'uom_id': str(gram_id), 'loss_percentage': '10.0'},
            {'sku_id': str(cheese_id), 'quantity': '30.0', 'uom_id': str(gram_id), 'loss_percentage': '5.0'},
            {'sku_id': str(bun_id), 'quantity': '1.0', 'uom_id': str(portion_id), 'loss_percentage': '0.0'},
        ]
        version = await service.publish_recipe_version(recipe.id, tenant_id, version_data, ingredients)
        await session.commit()
        
        recipe_id = recipe.id
    
    headers = await get_auth_headers(tenant_id)
    response = client.get(f"/recipes/{recipe_id}", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["id"] == str(recipe_id)
    assert data["name"] == "Classic Burger"
    assert data["type"] == "MENU_ITEM"
    assert data["pos_code"] == "POS-BURGER-01"
    assert data["version_number"] == 1
    assert "ingredients" in data
    assert len(data["ingredients"]) == 3
    
    # Check ingredient structure
    ing = data["ingredients"][0]
    assert "sku_id" in ing
    assert "sku_name" in ing
    assert "quantity" in ing
    assert "uom_symbol" in ing
    assert "loss_percentage" in ing
    assert "unit_cost" in ing
    assert "total_cost" in ing


async def test_create_recipe_version():
    """Test creating a recipe version."""
    tenant_id = uuid.uuid4()
    await create_tenant_and_membership(tenant_id)
    
    async with async_session_maker() as session:
        await session.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": str(tenant_id)})
        gram_id, kg_id, portion_id, beef_id, cheese_id, bun_id = await setup_test_data(session, tenant_id)
        
        from modules.recipes.service import RecipeService
        service = RecipeService(session)
        recipe = await service.create_recipe(tenant_id, "Classic Burger", "MENU_ITEM", "POS-BURGER-01")
        await session.commit()
        
        recipe_id = recipe.id
    
    headers = await get_auth_headers(tenant_id)
    response = client.post(f"/recipes/{recipe_id}/versions", headers=headers, json={
        "yield_quantity": 1.0,
        "yield_uom_id": str(portion_id),
        "portion_size": 1.0,
        "portion_uom_id": str(portion_id),
        "ingredients": [
            {"sku_id": str(beef_id), "quantity": 150.0, "uom_id": str(gram_id), "loss_percentage": 10.0},
            {"sku_id": str(cheese_id), "quantity": 30.0, "uom_id": str(gram_id), "loss_percentage": 5.0},
            {"sku_id": str(bun_id), "quantity": 1.0, "uom_id": str(portion_id), "loss_percentage": 0.0},
        ]
    })
    
    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
    data = response.json()
    
    assert data["version_number"] == 1
    assert data["yield_quantity"] == 1.0
    assert data["portion_size"] == 1.0
    assert len(data["ingredients"]) == 3
    
    # Check cost calculation: beef 150g * 1.10 * $5.00/g = $825.00
    # Wait: 150g * 1.10 = 165g * $5.00/g = $825? No, unit cost is $50000/10000g = $5.00/g
    # 150 * 1.10 * 5.00 = 825
    # cheese: 30g * 1.05 * $8.00/g = $252.00
    # bun: 1 * 1.0 * $1.50 = $1.50
    # total = $1078.50


async def test_catalog_skus_and_uoms():
    """Test getting catalog SKUs and UOMs."""
    tenant_id = uuid.uuid4()
    await create_tenant_and_membership(tenant_id)
    
    async with async_session_maker() as session:
        await session.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": str(tenant_id)})
        await setup_test_data(session, tenant_id)
        await session.commit()
    
    headers = await get_auth_headers(tenant_id)
    response = client.get("/recipes/catalog/skus-and-uoms", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    
    assert "skus" in data
    assert "uoms" in data
    assert isinstance(data["skus"], list)
    assert isinstance(data["uoms"], list)
    assert len(data["skus"]) >= 3
    assert len(data["uoms"]) >= 3
    
    # Check structure
    sku = data["skus"][0]
    assert "id" in sku
    assert "name" in sku
    
    uom = data["uoms"][0]
    assert "id" in uom
    assert "name" in uom
    assert "symbol" in uom


async def test_recipes_requires_auth():
    """Test that recipes endpoints require authentication."""
    # No auth header
    response = client.get("/recipes")
    assert response.status_code in (401, 422)
    
    # No tenant header
    import jwt
    import os
    secret = os.environ.get("JWT_SECRET", "dummy_secret_for_development_32_bytes_long_min!")
    algorithm = os.environ.get("JWT_ALGORITHM", "HS256")
    token = jwt.encode({"sub": "test-user", "exp": datetime.now(timezone.utc) + timedelta(hours=1)}, secret, algorithm=algorithm)
    
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/recipes", headers=headers)
    assert response.status_code in (401, 403, 422)


async def test_recipe_tenant_isolation():
    """Test that recipes are isolated by tenant."""
    tenant_a = uuid.uuid4()
    tenant_b = uuid.uuid4()
    
    await create_tenant_and_membership(tenant_a, "user-a")
    await create_tenant_and_membership(tenant_b, "user-b")
    
    async with async_session_maker() as session:
        await session.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": str(tenant_a)})
        await setup_test_data(session, tenant_a)
    
    async with async_session_maker() as session:
        await session.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": str(tenant_b)})
        await setup_test_data(session, tenant_b)
    
    async with async_session_maker() as session:
        await session.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": str(tenant_a)})
        from modules.recipes.service import RecipeService
        service = RecipeService(session)
        recipe_a = await service.create_recipe(tenant_a, "Tenant A Recipe", "MENU_ITEM", "POS-A-01")
        await session.commit()
    
    async with async_session_maker() as session:
        await session.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": str(tenant_b)})
        service = RecipeService(session)
        recipe_b = await service.create_recipe(tenant_b, "Tenant B Recipe", "MENU_ITEM", "POS-B-01")
        await session.commit()
    
    # Tenant A should only see their recipe
    headers_a = await get_auth_headers(tenant_a, "user-a")
    response_a = client.get("/recipes", headers=headers_a)
    assert response_a.status_code == 200
    data_a = response_a.json()
    assert len(data_a) == 1
    assert data_a[0]["name"] == "Tenant A Recipe"
    
    # Tenant B should only see their recipe
    headers_b = await get_auth_headers(tenant_b, "user-b")
    response_b = client.get("/recipes", headers=headers_b)
    assert response_b.status_code == 200
    data_b = response_b.json()
    assert len(data_b) == 1
    assert data_b[0]["name"] == "Tenant B Recipe"