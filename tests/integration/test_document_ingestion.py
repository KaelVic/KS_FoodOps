import pytest
import uuid
from decimal import Decimal
from datetime import datetime, timezone
from sqlalchemy import text
from sqlalchemy.future import select

from modules.documents.models import DocumentUpload, DocumentExtraction, DocumentExtractionLine
from modules.documents.service import DocumentService
from modules.suppliers.models import Supplier, SupplierSKU, SupplierSKUAlias
from modules.catalog.models import SKU, UOM, Category
from packages.tenant.models import Tenant

# Minimal NFe XML for testing
TEST_XML = """<?xml version="1.0" encoding="UTF-8"?>
<nfeProc versao="4.00" xmlns="http://www.portalfiscal.inf.br/nfe">
    <NFe>
        <infNFe Id="NFe1234567890" versao="4.00">
            <ide>
                <nNF>12345</nNF>
                <dhEmi>2026-08-15T12:00:00-03:00</dhEmi>
            </ide>
            <emit>
                <CNPJ>12345678000199</CNPJ>
                <xNome>Fornecedor Teste LTDA</xNome>
            </emit>
            <det nItem="1">
                <prod>
                    <cProd>COD001</cProd>
                    <xProd>TOMATE CARMEM KG</xProd>
                    <qCom>10.5</qCom>
                    <uCom>KG</uCom>
                    <vUnCom>4.50</vUnCom>
                </prod>
            </det>
            <total>
                <ICMSTot>
                    <vNF>47.25</vNF>
                </ICMSTot>
            </total>
        </infNFe>
    </NFe>
</nfeProc>
"""

@pytest.mark.asyncio
async def test_document_ingestion_pipeline(test_db, tenant_id):
    await test_db.execute(text("SELECT set_config('app.current_tenant_id', :t, false)"), {"t": str(tenant_id)})
    
    t_id = uuid.UUID(tenant_id)
    
    # 1. Setup Master Data (Supplier, SKU, SupplierSKU, Alias)
    cat = Category(tenant_id=t_id, name="Vegetables")
    test_db.add(cat)
    uom = UOM(tenant_id=t_id, name="Kilogram", symbol="KG", base_type="mass")
    test_db.add(uom)
    await test_db.flush()
    
    sku = SKU(tenant_id=t_id, category_id=cat.id, base_uom_id=uom.id, name="Tomate Carmem")
    test_db.add(sku)
    
    supplier = Supplier(tenant_id=t_id, name="Fornecedor Teste LTDA", tax_id="12345678000199")
    test_db.add(supplier)
    await test_db.flush()
    
    # Map the Supplier's item code directly to the SKU
    supplier_sku = SupplierSKU(
        tenant_id=t_id,
        supplier_id=supplier.id,
        sku_id=sku.id,
        supplier_item_code="COD001"
    )
    test_db.add(supplier_sku)
    await test_db.flush()
    
    # 2. Upload Document
    doc = await DocumentService.upload_document(
        session=test_db,
        tenant_id=t_id,
        file_path=TEST_XML, # Injecting XML content directly via path for test mock
        file_hash="mockhash123",
        format="XML"
    )
    assert doc.id is not None
    assert doc.status == "PENDING"
    
    # 3. Process Document
    ext = await DocumentService.process_document(test_db, doc.id)
    
    assert ext.supplier_cnpj_candidate == "12345678000199"
    assert ext.supplier_name_candidate == "Fornecedor Teste LTDA"
    assert ext.total_amount_candidate == Decimal("47.25")
    assert ext.invoice_number_candidate == "12345"
    
    # 4. Check Lines and Matching
    lines_stmt = select(DocumentExtractionLine).where(DocumentExtractionLine.document_extraction_id == ext.id)
    lines_res = await test_db.execute(lines_stmt)
    lines = lines_res.scalars().all()
    
    assert len(lines) == 1
    line = lines[0]
    assert line.raw_code == "COD001"
    assert line.raw_description == "TOMATE CARMEM KG"
    assert line.raw_quantity == Decimal("10.5")
    
    # It should have matched because COD001 is mapped to the supplier
    assert line.normalized_sku_id == sku.id
    assert line.confidence_score == 1.0
    
    # 5. Check idempotency of upload
    doc_dup = await DocumentService.upload_document(
        session=test_db,
        tenant_id=t_id,
        file_path="different_path.xml",
        file_hash="mockhash123", # same hash
        format="XML"
    )
    assert doc_dup.id == doc.id # Returned the existing one

