import pytest
from httpx import AsyncClient
from uuid import uuid4
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import text

@pytest.mark.asyncio
async def test_cash_flow_projection(
    async_client: AsyncClient, auth_headers: dict, owner_session, tenant_id: str
):
    # 1. Seed Supplier
    sup_id = uuid4()
    await owner_session.execute(
        text("INSERT INTO suppliers (id, tenant_id, name) VALUES (:id, :tid, 'Fornecedor Teste')"),
        {"id": str(sup_id), "tid": tenant_id},
    )
    await owner_session.commit()

    # 2. Create a bank account with 10,000 initial balance
    acc_payload = {
        "name": "Conta Itaú Teste Fluxo",
        "account_type": "CHECKING",
        "initial_balance": "10000.00",
        "current_balance": "10000.00"
    }
    r_acc = await async_client.post("/financial/bank-accounts", json=acc_payload, headers=auth_headers)
    assert r_acc.status_code in [200, 201], r_acc.text

    # 3. Create a Receivable of 5,000 for today (Net 4,860.50 after MDR)
    r_rec = await async_client.post("/financial/receivables", json={
        "customer_name": "Cliente PDV",
        "channel": "POS",
        "payment_method": "CREDIT_CARD",
        "gross_amount": "5000.00",
        "fee_percentage": "2.79",
        "due_date": datetime.now(timezone.utc).isoformat(),
        "description": "Vendas Salão"
    }, headers=auth_headers)
    assert r_rec.status_code in [200, 201], r_rec.text

    # 4. Create a Payable of 3,000 for today
    r_pay = await async_client.post("/financial/payables", json={
        "supplier_id": str(sup_id),
        "description": "Compra Fornecedor",
        "total_amount": "3000.00",
        "installment_count": 1,
        "first_due_date": datetime.now(timezone.utc).isoformat()
    }, headers=auth_headers)
    assert r_pay.status_code in [200, 201], r_pay.text

    # 5. Fetch Cash Flow Projection
    r_cf = await async_client.get("/financial/cash-flow", headers=auth_headers)
    assert r_cf.status_code == 200, r_cf.text
    cf_data = r_cf.json()

    assert "initial_balance" in cf_data
    assert "days" in cf_data
    assert len(cf_data["days"]) > 0


@pytest.mark.asyncio
async def test_financial_dre_calculation(
    async_client: AsyncClient, auth_headers: dict, owner_session, tenant_id: str
):
    # 1. Seed Supplier
    sup_id = uuid4()
    await owner_session.execute(
        text("INSERT INTO suppliers (id, tenant_id, name) VALUES (:id, :tid, 'Distribuidora Carnes')"),
        {"id": str(sup_id), "tid": tenant_id},
    )
    await owner_session.commit()

    # 2. Post a Receivable Invoice (Gross: 20,000, MDR: 558, Net: 19,442)
    r_rec = await async_client.post("/financial/receivables", json={
        "customer_name": "Consumidor Geral",
        "channel": "POS",
        "payment_method": "CREDIT_CARD",
        "gross_amount": "20000.00",
        "fee_percentage": "2.79",
        "due_date": datetime.now(timezone.utc).isoformat(),
        "description": "Faturamento Mensal Salão"
    }, headers=auth_headers)
    assert r_rec.status_code in [200, 201], r_rec.text

    # 3. Fetch categories to get CMV and Personnel category IDs
    r_cats = await async_client.get("/financial/categories", headers=auth_headers)
    assert r_cats.status_code == 200, r_cats.text
    cats = r_cats.json()
    cmv_cat = next((c for c in cats if c["type"] == "EXPENSE_CMV"), cats[0])
    personnel_cat = next((c for c in cats if c["type"] == "EXPENSE_PERSONNEL"), cats[0])

    # 4. Post CMV Expense of 6,000
    r_cmv = await async_client.post("/financial/payables", json={
        "supplier_id": str(sup_id),
        "description": "Carnes e Hortifruti",
        "total_amount": "6000.00",
        "category_id": cmv_cat["id"],
        "installment_count": 1,
        "first_due_date": datetime.now(timezone.utc).isoformat()
    }, headers=auth_headers)
    assert r_cmv.status_code in [200, 201], r_cmv.text

    # 5. Post Personnel Expense of 4,000
    r_pers = await async_client.post("/financial/payables", json={
        "supplier_id": str(sup_id),
        "description": "Folha de Pagamento Cozinha",
        "total_amount": "4000.00",
        "category_id": personnel_cat["id"],
        "installment_count": 1,
        "first_due_date": datetime.now(timezone.utc).isoformat()
    }, headers=auth_headers)
    assert r_pers.status_code in [200, 201], r_pers.text

    # 6. Fetch DRE
    r_dre = await async_client.get("/financial/dre?view_type=COMPETENCE", headers=auth_headers)
    assert r_dre.status_code == 200, r_dre.text
    dre_data = r_dre.json()

    assert "kpis" in dre_data
    kpis = dre_data["kpis"]
    assert kpis["gross_revenue"] >= 20000.00
    assert kpis["cmv_amount"] >= 6000.00
    assert kpis["prime_cost_amount"] >= 10000.00 # CMV + Personnel
    assert "lines" in dre_data
    assert len(dre_data["lines"]) == 12


@pytest.mark.asyncio
async def test_bank_statement_ofx_import_and_reconciliation(
    async_client: AsyncClient, auth_headers: dict, owner_session, tenant_id: str
):
    # 1. Create a bank account
    r_acc = await async_client.post("/financial/bank-accounts", json={
        "name": "Banco Santander OFX",
        "account_type": "CHECKING",
        "initial_balance": "5000.00",
        "current_balance": "5000.00"
    }, headers=auth_headers)
    assert r_acc.status_code in [200, 201], r_acc.text
    bank_acc_id = r_acc.json()["id"]

    # 2. Mock OFX Content
    ofx_sample = """OFXHEADER:100
DATA:OFXSGML
<OFX>
<BANKMSGSRSV1>
<STMTTRNRS>
<STMTRS>
<BANKTRANLIST>
<STMTTRN>
<TRNTYPE>CREDIT</TRNTYPE>
<DTPOSTED>20260816120000</DTPOSTED>
<TRNAMT>1500.00</TRNAMT>
<FITID>TX-OFX-99881122</FITID>
<MEMO>IFOOD REPASSE SEMANAL</MEMO>
</STMTTRN>
<STMTTRN>
<TRNTYPE>DEBIT</TRNTYPE>
<DTPOSTED>20260816130000</DTPOSTED>
<TRNAMT>-350.00</TRNAMT>
<FITID>TX-OFX-33445566</FITID>
<MEMO>PAGTO ENERGIA ELETRICA</MEMO>
</STMTTRN>
</BANKTRANLIST>
</STMTRS>
</STMTTRNRS>
</BANKMSGSRSV1>
</OFX>"""

    # 3. Upload OFX
    r_upload = await async_client.post("/financial/bank-statements/upload", json={
        "bank_account_id": bank_acc_id,
        "ofx_content": ofx_sample
    }, headers=auth_headers)
    assert r_upload.status_code in [200, 201], r_upload.text
    assert r_upload.json()["imported_count"] == 2

    # 4. List Bank Statement Transactions
    r_list = await async_client.get(f"/financial/bank-statements?bank_account_id={bank_acc_id}", headers=auth_headers)
    assert r_list.status_code == 200, r_list.text
    txs = r_list.json()
    assert len(txs) == 2

    # 5. Reconcile transaction
    tx_id = txs[0]["id"]
    r_rec = await async_client.post(f"/financial/bank-statements/{tx_id}/reconcile", json={
        "settlement_type": "RECEIVABLE",
        "notes": "Conciliado com repasse iFood"
    }, headers=auth_headers)
    assert r_rec.status_code == 200, r_rec.text
    assert r_rec.json()["is_reconciled"] is True
