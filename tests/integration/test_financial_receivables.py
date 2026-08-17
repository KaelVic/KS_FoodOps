import pytest
from httpx import AsyncClient
from uuid import uuid4
from decimal import Decimal
from sqlalchemy import text

@pytest.mark.asyncio
async def test_acquirers_and_receivables_dashboard(
    async_client: AsyncClient, auth_headers: dict, owner_session, tenant_id: str
):
    """Test default acquirers listing, creation, and receivables dashboard."""
    # 1. List acquirers (auto-seeds defaults)
    resp = await async_client.get("/financial/acquirers", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    acquirers = resp.json()
    assert len(acquirers) >= 4
    names = [a["name"] for a in acquirers]
    assert "Stone Pagamentos" in names or "Cielo" in names or "iFood Marketplace & Entrega" in names

    # 2. Create custom acquirer
    payload = {
        "name": "PagBank / PagSeguro",
        "acquirer_type": "CREDIT_DEBIT",
        "debit_fee_percentage": "1.39",
        "credit_1x_fee_percentage": "2.69",
        "credit_inst_fee_percentage": "3.59",
        "voucher_fee_percentage": "4.99",
        "delivery_fee_percentage": "0.00",
        "pix_fee_percentage": "0.00",
        "fixed_fee": "0.00",
        "settlement_days_debit": 1,
        "settlement_days_credit": 30,
        "settlement_days_voucher": 30,
        "settlement_days_delivery": 1
    }
    resp = await async_client.post("/financial/acquirers", json=payload, headers=auth_headers)
    assert resp.status_code == 201, resp.text
    created = resp.json()
    assert created["name"] == "PagBank / PagSeguro"

    # 3. Get Receivables Dashboard
    dash_resp = await async_client.get("/financial/receivables/dashboard", headers=auth_headers)
    assert dash_resp.status_code == 200, dash_resp.text
    dash = dash_resp.json()
    assert "total_expected_today" in dash
    assert "total_received_month" in dash
    assert "total_fees_deducted_month" in dash
    assert "total_bank_balance" in dash


@pytest.mark.asyncio
async def test_create_and_settle_receivable_invoice(
    async_client: AsyncClient, auth_headers: dict, owner_session, tenant_id: str
):
    """Test full cycle: create receivable with MDR fee calculation, settle into bank account, verify balance."""
    # 1. Create a bank account
    ba_payload = {
        "name": "Banco Inter - Recebimentos",
        "account_type": "CHECKING",
        "bank_code": "077",
        "agency_number": "0001",
        "account_number": "123456-7",
        "initial_balance": "500.00"
    }
    ba_resp = await async_client.post("/financial/bank-accounts", json=ba_payload, headers=auth_headers)
    assert ba_resp.status_code == 201, ba_resp.text
    bank_account = ba_resp.json()
    bank_account_id = bank_account["id"]

    # 2. Get acquirer
    acq_resp = await async_client.get("/financial/acquirers", headers=auth_headers)
    acquirers = acq_resp.json()
    stone = next((a for a in acquirers if "Stone" in a["name"]), acquirers[0])

    # 3. Create receivable invoice for Credit Card R$ 1000.00 with 2.79% MDR fee
    invoice_payload = {
        "customer_name": "Cliente VIP - Jantar",
        "channel": "POS",
        "payment_method": "CREDIT_CARD",
        "card_brand": "MASTERCARD",
        "acquirer_id": stone["id"],
        "document_number": "CUPOM-7890",
        "description": "Venda Salão - Mesa 12",
        "gross_amount": "1000.00",
        "nsu": "123456789",
        "authorization_code": "AUTH9988"
    }
    inv_resp = await async_client.post("/financial/receivables", json=invoice_payload, headers=auth_headers)
    assert inv_resp.status_code == 201, inv_resp.text
    invoice = inv_resp.json()

    assert invoice["customer_name"] == "Cliente VIP - Jantar"
    assert invoice["gross_amount"] == 1000.00
    assert invoice["status"] == "PENDING"
    assert len(invoice["installments"]) == 1

    installment = invoice["installments"][0]
    installment_id = installment["id"]
    # Net amount should be 1000.00 - fee (approx 27.90) = 972.10
    assert installment["gross_amount"] == 1000.00
    assert installment["net_amount"] < 1000.00
    assert installment["status"] == "PENDING"

    # 4. Settle / Baixa of the receivable into Bank Account
    settle_payload = {
        "bank_account_id": bank_account_id,
        "gross_amount": "1000.00",
        "fee_deducted": str(installment["fee_amount"]),
        "net_received_amount": str(installment["net_amount"]),
        "bank_transaction_ref": "DEP-STONE-8833",
        "notes": "Repasse Stone confirmado em extrato"
    }
    settle_resp = await async_client.post(
        f"/financial/receivables/installments/{installment_id}/settle",
        json=settle_payload,
        headers=auth_headers
    )
    assert settle_resp.status_code == 200, settle_resp.text
    settle_data = settle_resp.json()
    assert settle_data["invoice_status"] == "RECEIVED"
    # Bank balance was 500.00 + net_received_amount
    expected_balance = 500.00 + float(installment["net_amount"])
    assert round(settle_data["new_bank_balance"], 2) == round(expected_balance, 2)

    # 5. Verify invoice detail
    get_resp = await async_client.get(f"/financial/receivables/{invoice['id']}", headers=auth_headers)
    assert get_resp.status_code == 200, get_resp.text
    updated_inv = get_resp.json()
    assert updated_inv["status"] == "RECEIVED"
    assert updated_inv["installments"][0]["status"] == "RECEIVED"
    assert updated_inv["installments"][0]["settlement"] is not None


@pytest.mark.asyncio
async def test_cross_tenant_isolation_receivables(
    async_client: AsyncClient, auth_headers: dict, owner_session, tenant_id: str
):
    """Ensure Tenant A cannot view or settle Tenant B's receivable invoices."""
    other_tenant_id = uuid4()
    await owner_session.execute(
        text("INSERT INTO tenants (id, name) VALUES (:id, 'Tenant B Food')"),
        {"id": str(other_tenant_id)},
    )
    other_inv_id = uuid4()
    await owner_session.execute(
        text(
            "INSERT INTO receivable_invoices (id, tenant_id, customer_name, description, gross_amount, net_amount, issue_date, due_date, status) "
            "VALUES (:id, :tid, 'Cliente Secreto B', 'Faturamento Confidencial B', 5000.00, 4850.00, NOW(), NOW(), 'PENDING')"
        ),
        {"id": str(other_inv_id), "tid": str(other_tenant_id)},
    )
    other_inst_id = uuid4()
    await owner_session.execute(
        text(
            "INSERT INTO receivable_installments (id, tenant_id, invoice_id, gross_amount, net_amount, expected_settlement_date, status) "
            "VALUES (:id, :tid, :iid, 5000.00, 4850.00, NOW(), 'PENDING')"
        ),
        {"id": str(other_inst_id), "tid": str(other_tenant_id), "iid": str(other_inv_id)},
    )
    await owner_session.commit()

    # Tenant A attempts to read Tenant B's invoice
    get_resp = await async_client.get(f"/financial/receivables/{other_inv_id}", headers=auth_headers)
    assert get_resp.status_code == 404

    # Tenant A attempts to list receivables -> Tenant B's invoice must NOT appear
    list_resp = await async_client.get("/financial/receivables", headers=auth_headers)
    assert list_resp.status_code == 200
    invoices = list_resp.json()
    invoice_ids = [inv["id"] for inv in invoices]
    assert str(other_inv_id) not in invoice_ids
