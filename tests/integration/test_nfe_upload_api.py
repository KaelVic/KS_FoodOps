import pytest
import uuid
import hashlib
from decimal import Decimal
from datetime import datetime, timezone
from sqlalchemy.future import select
from sqlalchemy import text
from io import BytesIO

from packages.tenant.database import async_session_maker
from modules.documents.models import DocumentExtraction, DocumentExtractionLine, DocumentUpload
from modules.purchasing.models import SupplierInvoice
from modules.catalog.models import UOM
from modules.suppliers.models import Supplier, SupplierSKU, SupplierSKUAlias
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
    """Setup UOM, SKU, Supplier, SupplierSKU, Alias."""
    kg_id = uuid.uuid4()
    await session.execute(
        text("INSERT INTO uoms (id, tenant_id, name, symbol, base_type) VALUES (:id, :t_id, 'Kilogram', 'kg', 'mass')"),
        {"id": str(kg_id), "t_id": str(tenant_id)}
    )
    
    sku_id = uuid.uuid4()
    await session.execute(
        text("INSERT INTO skus (id, tenant_id, name, base_uom_id) VALUES (:id, :t_id, 'Tomato', :uom_id)"),
        {"id": str(sku_id), "t_id": str(tenant_id), "uom_id": str(kg_id)}
    )
    
    supplier_id = uuid.uuid4()
    await session.execute(
        text("INSERT INTO suppliers (id, tenant_id, name, tax_id) VALUES (:id, :t_id, 'Farm Fresh', '12345678000199')"),
        {"id": str(supplier_id), "t_id": str(tenant_id)}
    )
    
    supplier_sku_id = uuid.uuid4()
    await session.execute(
        text("INSERT INTO supplier_skus (id, tenant_id, supplier_id, sku_id, supplier_item_code) VALUES (:id, :t_id, :s_id, :sku_id, 'P-001')"),
        {"id": str(supplier_sku_id), "t_id": str(tenant_id), "s_id": str(supplier_id), "sku_id": str(sku_id)}
    )
    
    await session.execute(
        text("INSERT INTO supplier_sku_aliases (id, tenant_id, supplier_sku_id, alias_name) VALUES (:id, :t_id, :ss_id, 'TOMATE CARMEM KG')"),
        {"id": str(uuid.uuid4()), "t_id": str(tenant_id), "ss_id": str(supplier_sku_id)}
    )
    
    return supplier_id, sku_id, supplier_sku_id


async def create_tenant_and_membership(owner_session, tenant_id: uuid.UUID, user_id: str = "test-user-123"):
    """Create tenant and membership using owner session (bypasses RLS)."""
    await owner_session.execute(
        text("INSERT INTO tenants (id, name) VALUES (:id, 'Tenant API Test')"),
        {"id": str(tenant_id)}
    )
    await owner_session.execute(
        text("INSERT INTO tenant_memberships (id, tenant_id, user_id, role) VALUES (:id, :t_id, :uid, 'admin')"),
        {"id": str(uuid.uuid4()), "t_id": str(tenant_id), "uid": user_id}
    )
    await owner_session.commit()


async def get_auth_headers(tenant_id: uuid.UUID) -> dict:
    """Create auth headers with a mock token and tenant ID."""
    import jwt
    import os
    secret = os.environ.get("JWT_SECRET", "dummy_secret_for_development_32_bytes_long_min!")
    algorithm = os.environ.get("JWT_ALGORITHM", "HS256")
    
    payload = {
        "sub": "test-user-123",
        "email": "test@ksfoodops.local",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1)
    }
    token = jwt.encode(payload, secret, algorithm=algorithm)
    
    return {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": str(tenant_id)
    }


from datetime import timedelta


async def test_upload_nfe_success(owner_session):
    """Test successful NFe XML upload via API."""
    tenant_id = uuid.uuid4()
    
    # Setup tenant and membership using owner session (bypasses RLS)
    await create_tenant_and_membership(owner_session, tenant_id)
    
    async with async_session_maker() as session:
        await session.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": str(tenant_id)})
        supplier_id, sku_id, supplier_sku_id = await setup_test_data(session, tenant_id)
        await session.commit()
    
    # Compute file hash
    file_hash = hashlib.sha256(SAMPLE_NFE_XML.encode("utf-8")).hexdigest()
    
    # Upload via API
    headers = await get_auth_headers(tenant_id)
    files = {"file": ("nfe_123.xml", BytesIO(SAMPLE_NFE_XML.encode("utf-8")), "application/xml")}
    
    response = client.post("/documents/upload-nfe", headers=headers, files=files)
    
    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
    
    data = response.json()
    assert "id" in data
    assert "invoice_number" in data
    assert "status" in data
    assert "total_amount" in data
    
    assert data["invoice_number"] == "123456"
    assert data["status"] == "NEEDS_REVIEW"
    assert data["total_amount"] == 1500.00
    
    extraction_id = uuid.UUID(data["id"])
    
    # Verify in database
    async with async_session_maker() as session:
        await session.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": str(tenant_id)})
        
        # Check extraction
        stmt = select(DocumentExtraction).where(DocumentExtraction.id == extraction_id)
        extraction = (await session.execute(stmt)).scalar_one()
        
        assert extraction.invoice_number_candidate == "123456"
        assert extraction.total_amount_candidate == Decimal("1500.00")
        assert extraction.supplier_cnpj_candidate == "12345678000199"
        
        # Check DocumentUpload status
        stmt_upload = select(DocumentUpload).where(DocumentUpload.id == extraction.document_upload_id)
        upload = (await session.execute(stmt_upload)).scalar_one()
        assert upload.status == "NEEDS_REVIEW"
        
        # Check lines
        stmt_lines = select(DocumentExtractionLine).where(DocumentExtractionLine.document_extraction_id == extraction_id)
        lines = (await session.execute(stmt_lines)).scalars().all()
        
        assert len(lines) == 1
        assert lines[0].raw_description == "TOMATE CARMEM KG"
        assert lines[0].raw_code == "P-001"
        assert lines[0].raw_quantity == Decimal("10.000")
        assert lines[0].raw_uom == "KG"
        assert lines[0].raw_unit_price == Decimal("150.00")
        assert lines[0].normalized_sku_id is not None
        assert lines[0].confidence_score == Decimal("1.0")
        
        # Check document upload
        stmt = select(DocumentUpload).where(DocumentUpload.id == extraction.document_upload_id)
        upload_doc = (await session.execute(stmt)).scalar_one()
        
        assert upload_doc.file_hash == file_hash
        assert upload_doc.format == "XML"
        
        await session.commit()


async def test_upload_nfe_invalid_xml(owner_session):
    """Test upload with invalid XML returns 400."""
    tenant_id = uuid.uuid4()
    
    await create_tenant_and_membership(owner_session, tenant_id)
    
    headers = await get_auth_headers(tenant_id)
    files = {"file": ("invalid.xml", BytesIO(b"<invalid>xml</invalid>"), "application/xml")}
    
    response = client.post("/documents/upload-nfe", headers=headers, files=files)
    
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data


async def test_upload_nfe_missing_fields(owner_session):
    """Test upload with XML missing required fields returns 400."""
    tenant_id = uuid.uuid4()
    
    await create_tenant_and_membership(owner_session, tenant_id)
    
    # XML missing nNF
    invalid_xml = '''<?xml version="1.0" encoding="UTF-8"?>
    <nfeProc xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00">
      <NFe>
        <infNFe versao="4.00" Id="NFe35240112345678000199550010001234561000123456">
          <ide>
            <cUF>35</cUF>
            <dhEmi>2024-01-15T10:30:00-03:00</dhEmi>
          </ide>
          <emit>
            <CNPJ>12345678000199</CNPJ>
            <xNome>Farm Fresh</xNome>
          </emit>
          <total>
            <ICMSTot>
              <vNF>1500.00</vNF>
            </ICMSTot>
          </total>
        </infNFe>
      </NFe>
    </nfeProc>'''
    
    headers = await get_auth_headers(tenant_id)
    files = {"file": ("invalid.xml", BytesIO(invalid_xml.encode("utf-8")), "application/xml")}
    
    response = client.post("/documents/upload-nfe", headers=headers, files=files)
    
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data


async def test_list_extractions(owner_session):
    """Test listing document extractions."""
    tenant_id = uuid.uuid4()
    
    await create_tenant_and_membership(owner_session, tenant_id)
    
    async with async_session_maker() as session:
        await session.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": str(tenant_id)})
        supplier_id, sku_id, supplier_sku_id = await setup_test_data(session, tenant_id)
        
        # Create an extraction via pipeline
        from modules.documents.service import IngestionPipeline
        pipeline = IngestionPipeline(session)
        extraction = await pipeline.ingest_nfe_xml(tenant_id, "s3://docs/test.xml", "hash1", SAMPLE_NFE_XML)
        await session.commit()
    
    headers = await get_auth_headers(tenant_id)
    response = client.get("/documents/extractions", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    
    # Check structure
    item = data[0]
    assert "id" in item
    assert "invoice_number" in item
    assert "issue_date" in item
    assert "total_amount" in item
    assert "status" in item
    assert "created_at" in item
    assert "supplier_name" in item
    
    assert item["invoice_number"] == "123456"
    assert item["total_amount"] == 1500.00
    assert item["status"] == "NEEDS_REVIEW"
    assert item["supplier_name"] == "Farm Fresh"


async def test_get_extraction_detail(owner_session):
    """Test getting extraction detail with lines."""
    tenant_id = uuid.uuid4()
    
    await create_tenant_and_membership(owner_session, tenant_id)
    
    async with async_session_maker() as session:
        await session.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": str(tenant_id)})
        supplier_id, sku_id, supplier_sku_id = await setup_test_data(session, tenant_id)
        
        from modules.documents.service import IngestionPipeline
        pipeline = IngestionPipeline(session)
        extraction = await pipeline.ingest_nfe_xml(tenant_id, "s3://docs/test.xml", "hash1", SAMPLE_NFE_XML)
        extraction_id = extraction.id
        await session.commit()
    
    headers = await get_auth_headers(tenant_id)
    response = client.get(f"/documents/extractions/{extraction_id}", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    
    assert "id" in data
    assert "invoice_number" in data
    assert "issue_date" in data
    assert "total_amount" in data
    assert "status" in data
    assert "created_at" in data
    assert "supplier_name" in data
    assert "lines" in data
    assert isinstance(data["lines"], list)
    assert len(data["lines"]) == 1
    
    line = data["lines"][0]
    assert "id" in line
    assert "raw_description" in line
    assert "raw_code" in line
    assert "raw_quantity" in line
    assert "raw_uom" in line
    assert "raw_unit_price" in line
    assert "match_status" in line
    
    assert line["raw_description"] == "TOMATE CARMEM KG"
    assert line["raw_code"] == "P-001"
    assert line["raw_quantity"] == 10.0
    assert line["raw_uom"] == "KG"
    assert line["raw_unit_price"] == 150.0
    assert line["match_status"] == "MATCHED"


async def test_approve_extraction(owner_session):
    """Test approving an extraction."""
    tenant_id = uuid.uuid4()
    
    await create_tenant_and_membership(owner_session, tenant_id)
    
    async with async_session_maker() as session:
        await session.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": str(tenant_id)})
        supplier_id, sku_id, supplier_sku_id = await setup_test_data(session, tenant_id)
        
        from modules.documents.service import IngestionPipeline
        pipeline = IngestionPipeline(session)
        extraction = await pipeline.ingest_nfe_xml(tenant_id, "s3://docs/test.xml", "hash1", SAMPLE_NFE_XML)
        extraction_id = extraction.id
        await session.commit()
    
    headers = await get_auth_headers(tenant_id)
    response = client.post(f"/documents/extractions/{extraction_id}/approve", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert "invoice_id" in data
    
    invoice_id = uuid.UUID(data["invoice_id"])
    
    # Verify in database
    async with async_session_maker() as session:
        await session.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": str(tenant_id)})
        
        # Check DocumentUpload is APPROVED
        stmt = select(DocumentExtraction).where(DocumentExtraction.id == extraction_id)
        extraction = (await session.execute(stmt)).scalar_one()
        
        stmt_upload = select(DocumentUpload).where(DocumentUpload.id == extraction.document_upload_id)
        upload = (await session.execute(stmt_upload)).scalar_one()
        assert upload.status == "APPROVED"
        
        # Check invoice created
        stmt = select(SupplierInvoice).where(SupplierInvoice.id == invoice_id)
        invoice = (await session.execute(stmt)).scalar_one()
        
        assert invoice.supplier_id == supplier_id
        assert invoice.invoice_number == "123456"
        assert invoice.total_amount == Decimal("1500.00")
        
        await session.commit()


async def test_approve_extraction_not_ready(owner_session):
    """Test approving an extraction that is not ready fails."""
    tenant_id = uuid.uuid4()
    
    await create_tenant_and_membership(owner_session, tenant_id)
    
    async with async_session_maker() as session:
        await session.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": str(tenant_id)})
        supplier_id, sku_id, supplier_sku_id = await setup_test_data(session, tenant_id)
        
        from modules.documents.service import IngestionPipeline
        pipeline = IngestionPipeline(session)
        # Create extraction but with unmatched line (no supplier)
        xml_no_supplier = SAMPLE_NFE_XML.replace("12345678000199", "99999999000199")
        extraction = await pipeline.ingest_nfe_xml(tenant_id, "s3://docs/test.xml", "hash2", xml_no_supplier)
        extraction_id = extraction.id
        await session.commit()
    
    headers = await get_auth_headers(tenant_id)
    response = client.post(f"/documents/extractions/{extraction_id}/approve", headers=headers)
    
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "supplier" in data["detail"].lower() or "ready" in data["detail"].lower()


async def test_upload_nfe_requires_auth(owner_session):
    """Test that upload requires authentication."""
    tenant_id = uuid.uuid4()
    
    await create_tenant_and_membership(owner_session, tenant_id)
    
    files = {"file": ("nfe.xml", BytesIO(SAMPLE_NFE_XML.encode("utf-8")), "application/xml")}
    
    # No auth header
    response = client.post("/documents/upload-nfe", files=files)
    assert response.status_code in (401, 422)
    
    # No tenant header
    import jwt
    import os
    secret = os.environ.get("JWT_SECRET", "dummy_secret_for_development_32_bytes_long_min!")
    algorithm = os.environ.get("JWT_ALGORITHM", "HS256")
    token = jwt.encode({"sub": "test-user", "exp": datetime.now(timezone.utc) + timedelta(hours=1)}, secret, algorithm=algorithm)
    
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/documents/upload-nfe", headers=headers, files=files)
    assert response.status_code in (401, 403, 422)