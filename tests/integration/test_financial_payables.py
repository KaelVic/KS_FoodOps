import pytest
from httpx import AsyncClient
from uuid import uuid4
from datetime import datetime, timezone, timedelta
from sqlalchemy import text

pytestmark = pytest.mark.asyncio

async def test_financial_categories_and_bank_accounts(
    async_client: AsyncClient, auth_headers: dict, owner_session, tenant_id: str
):
    """Test category and bank account listing and creation."""
    # List categories (should auto seed default categories)
    res = await async_client.get("/financial/categories", headers=auth_headers)
    assert res.status_code == 200, res.text
    categories = res.json()
    assert len(categories) > 0

    # List cost centers
    res_cc = await async_client.get("/financial/cost-centers", headers=auth_headers)
    assert res_cc.status_code == 200, res_cc.text
    cost_centers = res_cc.json()
    assert len(cost_centers) > 0

    # Create new Bank Account
    ba_payload = {
        "name": "Banco Itaú - Conta Teste",
        "account_type": "CHECKING",
        "bank_code": "341",
        "agency_number": "1234",
        "account_number": "56789-0",
        "pix_key": "financeiro@restaurante.com",
        "initial_balance": "10000.00"
    }
    res_ba = await async_client.post("/financial/bank-accounts", json=ba_payload, headers=auth_headers)
    assert res_ba.status_code == 201, res_ba.text
    ba_data = res_ba.json()
    assert ba_data["name"] == "Banco Itaú - Conta Teste"
    assert float(ba_data["current_balance"]) == 10000.00


async def test_create_and_settle_payable_bill(
    async_client: AsyncClient, auth_headers: dict, owner_session, tenant_id: str
):
    """Test full cycle: create bill with 2 installments, pay 1st with discount, check balance."""
    # 1. Seed Supplier
    sup_id = uuid4()
    await owner_session.execute(
        text("INSERT INTO suppliers (id, tenant_id, name) VALUES (:id, :tid, 'Fornecedor Hortifruti')"),
        {"id": str(sup_id), "tid": tenant_id},
    )

    # 2. Seed Bank Account
    ba_id = uuid4()
    await owner_session.execute(
        text(
            "INSERT INTO bank_accounts (id, tenant_id, name, account_type, initial_balance, current_balance) "
            "VALUES (:id, :tid, 'Banco Bradesco', 'CHECKING', 5000.00, 5000.00)"
        ),
        {"id": str(ba_id), "tid": tenant_id},
    )
    await owner_session.commit()

    # 3. Create Payable Bill with 2 installments (Total: R$ 1.500,00)
    now = datetime.now(timezone.utc)
    due_1 = (now + timedelta(days=5)).isoformat()
    due_2 = (now + timedelta(days=35)).isoformat()

    bill_payload = {
        "supplier_id": str(sup_id),
        "document_number": "NF-9988",
        "description": "Compra Semanal Hortifruti",
        "total_amount": "1500.00",
        "issue_date": now.isoformat(),
        "first_due_date": due_1,
        "installments": [
            {
                "installment_number": 1,
                "total_installments": 2,
                "due_date": due_1,
                "amount": "750.00",
                "pix_code": "00020126580014br.gov.bcb.pix..."
            },
            {
                "installment_number": 2,
                "total_installments": 2,
                "due_date": due_2,
                "amount": "750.00",
                "barcode": "34191.79001 01043.510047 91020.150008 5 89210000075000"
            }
        ]
    }

    res_bill = await async_client.post("/financial/payables", json=bill_payload, headers=auth_headers)
    assert res_bill.status_code == 201, res_bill.text
    bill_data = res_bill.json()
    assert bill_data["document_number"] == "NF-9988"
    assert len(bill_data["installments"]) == 2
    assert bill_data["status"] == "PENDING"

    inst_1_id = bill_data["installments"][0]["id"]

    # 4. Settle 1st installment with R$ 50.00 discount
    settle_payload = {
        "bank_account_id": str(ba_id),
        "payment_method": "PIX",
        "discount_amount": "50.00",
        "interest_amount": "0.00",
        "fine_amount": "0.00",
        "transaction_reference": "PIX-AUTH-12345678",
        "notes": "Pago com desconto concedido pelo fornecedor"
    }

    res_settle = await async_client.post(
        f"/financial/payables/installments/{inst_1_id}/settle",
        json=settle_payload,
        headers=auth_headers
    )
    assert res_settle.status_code == 200, res_settle.text
    settled_bill = res_settle.json()
    
    # Bill status should be PARTIALLY_PAID
    assert settled_bill["status"] == "PARTIALLY_PAID"
    assert settled_bill["installments"][0]["status"] == "PAID"
    assert settled_bill["installments"][1]["status"] == "PENDING"

    # Check bank account balance debited: 5000 - (750 - 50) = 4300
    res_ba = await async_client.get("/financial/bank-accounts", headers=auth_headers)
    accounts = res_ba.json()
    target_ba = next((a for a in accounts if str(a["id"]) == str(ba_id)), None)
    assert target_ba is not None
    assert float(target_ba["current_balance"]) == 4300.00

    # 5. Check Dashboard Metrics
    res_dash = await async_client.get("/financial/payables/dashboard", headers=auth_headers)
    assert res_dash.status_code == 200, res_dash.text
    dash = res_dash.json()
    assert dash["total_paid_month"] >= 700.00
    assert len(dash["upcoming_installments"]) > 0


async def test_cross_tenant_isolation_payables(
    async_client: AsyncClient, auth_headers: dict, owner_session, tenant_id: str
):
    """Ensure Tenant A cannot see or settle Tenant B's payable bills."""
    other_tenant_id = uuid4()
    await owner_session.execute(
        text("INSERT INTO tenants (id, name) VALUES (:id, 'Tenant B Food')"),
        {"id": str(other_tenant_id)},
    )
    other_sup_id = uuid4()
    await owner_session.execute(
        text("INSERT INTO suppliers (id, tenant_id, name) VALUES (:id, :tid, 'Fornecedor B')"),
        {"id": str(other_sup_id), "tid": str(other_tenant_id)},
    )
    other_bill_id = uuid4()
    await owner_session.execute(
        text(
            "INSERT INTO payable_bills (id, tenant_id, supplier_id, description, total_amount, first_due_date, status) "
            "VALUES (:id, :tid, :sid, 'Conta Secreta Tenant B', 9999.00, NOW(), 'PENDING')"
        ),
        {"id": str(other_bill_id), "tid": str(other_tenant_id), "sid": str(other_sup_id)},
    )
    await owner_session.commit()

    # Querying from Tenant A should NOT return Tenant B's bill
    res = await async_client.get("/financial/payables", headers=auth_headers)
    assert res.status_code == 200
    bills = res.json()
    assert all(b["id"] != str(other_bill_id) for b in bills)

    # Directly requesting Tenant B's bill must 404
    res_single = await async_client.get(f"/financial/payables/{other_bill_id}", headers=auth_headers)
    assert res_single.status_code == 404
