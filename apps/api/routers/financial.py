import uuid
from typing import List, Optional, Any, Dict
from datetime import datetime
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from packages.security.dependencies import get_secure_session, get_tenant_id_from_header
from modules.financial.service import FinancialService

router = APIRouter(tags=["Financial"], prefix="/financial")

# --- Schemas ---
class CategoryCreate(BaseModel):
    code: Optional[str] = None
    name: str = Field(..., example="CMV / Insumos Alimentícios")
    type: str = Field("EXPENSE_OPERATIONAL", example="EXPENSE_CMV")
    parent_id: Optional[uuid.UUID] = None

class CategoryResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    code: Optional[str]
    name: str
    type: str
    parent_id: Optional[uuid.UUID]
    is_active: bool
    created_at: Optional[datetime]
    model_config = ConfigDict(from_attributes=True)

class CostCenterCreate(BaseModel):
    code: Optional[str] = None
    name: str = Field(..., example="Cozinha Principal")
    description: Optional[str] = None

class CostCenterResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    code: Optional[str]
    name: str
    description: Optional[str]
    is_active: bool
    created_at: Optional[datetime]
    model_config = ConfigDict(from_attributes=True)

class BankAccountCreate(BaseModel):
    name: str = Field(..., example="Banco Itaú - Conta Principal")
    account_type: str = Field("CHECKING", example="CHECKING") # CHECKING, SAVINGS, CASH, DIGITAL_WALLET
    bank_code: Optional[str] = None
    agency_number: Optional[str] = None
    account_number: Optional[str] = None
    pix_key: Optional[str] = None
    initial_balance: Decimal = Decimal("0.00")

class BankAccountResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    account_type: str
    bank_code: Optional[str]
    agency_number: Optional[str]
    account_number: Optional[str]
    pix_key: Optional[str]
    initial_balance: Decimal
    current_balance: Decimal
    is_active: bool
    created_at: Optional[datetime]
    model_config = ConfigDict(from_attributes=True)

class InstallmentInput(BaseModel):
    installment_number: int
    total_installments: int
    due_date: datetime
    amount: Decimal
    barcode: Optional[str] = None
    pix_code: Optional[str] = None

class PayableBillCreate(BaseModel):
    supplier_id: uuid.UUID
    category_id: Optional[uuid.UUID] = None
    cost_center_id: Optional[uuid.UUID] = None
    purchase_order_id: Optional[uuid.UUID] = None
    supplier_invoice_id: Optional[uuid.UUID] = None
    document_number: Optional[str] = None
    description: str = Field(..., example="Compra de Insumos - NF 4492")
    total_amount: Decimal = Field(..., example="1500.00")
    issue_date: Optional[datetime] = None
    first_due_date: Optional[datetime] = None
    installment_count: Optional[int] = 1
    barcode: Optional[str] = None
    pix_code: Optional[str] = None
    notes: Optional[str] = None
    installments: Optional[List[InstallmentInput]] = None

class SettleInstallmentPayload(BaseModel):
    bank_account_id: uuid.UUID
    payment_method: str = "PIX"
    settlement_date: Optional[datetime] = None
    interest_amount: Decimal = Decimal("0.00")
    fine_amount: Decimal = Decimal("0.00")
    discount_amount: Decimal = Decimal("0.00")
    receipt_url: Optional[str] = None
    transaction_reference: Optional[str] = None
    notes: Optional[str] = None


# --- Accounts Receivable Schemas ---

class AcquirerCreate(BaseModel):
    name: str = Field(..., min_length=2)
    acquirer_type: str = "CREDIT_DEBIT"
    debit_fee_percentage: Decimal = Decimal("1.50")
    credit_1x_fee_percentage: Decimal = Decimal("2.80")
    credit_inst_fee_percentage: Decimal = Decimal("3.80")
    voucher_fee_percentage: Decimal = Decimal("5.50")
    delivery_fee_percentage: Decimal = Decimal("23.00")
    pix_fee_percentage: Decimal = Decimal("0.00")
    fixed_fee: Decimal = Decimal("0.00")
    settlement_days_debit: int = 1
    settlement_days_credit: int = 30
    settlement_days_voucher: int = 30
    settlement_days_delivery: int = 7

class AcquirerResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    acquirer_type: str
    debit_fee_percentage: Decimal
    credit_1x_fee_percentage: Decimal
    credit_inst_fee_percentage: Decimal
    voucher_fee_percentage: Decimal
    delivery_fee_percentage: Decimal
    pix_fee_percentage: Decimal
    fixed_fee: Decimal
    settlement_days_debit: int
    settlement_days_credit: int
    settlement_days_voucher: int
    settlement_days_delivery: int
    is_active: bool
    created_at: Optional[datetime]
    model_config = ConfigDict(from_attributes=True)

class ReceivableInstallmentInput(BaseModel):
    installment_number: int = 1
    total_installments: int = 1
    payment_method: str = "CREDIT_CARD"
    card_brand: Optional[str] = None
    gross_amount: Decimal
    fee_percentage: Optional[Decimal] = None
    expected_settlement_date: Optional[datetime] = None
    nsu: Optional[str] = None
    authorization_code: Optional[str] = None

class ReceivableInvoiceCreate(BaseModel):
    customer_name: str = "Consumidor Final"
    customer_tax_id: Optional[str] = None
    channel: str = "POS" # POS, DELIVERY_IFOOD, DELIVERY_OWN, CORPORATE_INVOICE, CATERING_EVENT
    category_id: Optional[uuid.UUID] = None
    cost_center_id: Optional[uuid.UUID] = None
    acquirer_id: Optional[uuid.UUID] = None
    payment_method: str = "CREDIT_CARD"
    card_brand: Optional[str] = None
    document_number: Optional[str] = None
    description: str = "Venda PDV / Faturamento"
    gross_amount: Decimal
    fee_percentage: Optional[Decimal] = None
    issue_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    nsu: Optional[str] = None
    authorization_code: Optional[str] = None
    notes: Optional[str] = None
    installments: Optional[List[ReceivableInstallmentInput]] = None

class SettleReceivableInstallmentPayload(BaseModel):
    bank_account_id: uuid.UUID
    settlement_date: Optional[datetime] = None
    gross_amount: Optional[Decimal] = None
    fee_deducted: Optional[Decimal] = None
    net_received_amount: Optional[Decimal] = None
    bank_transaction_ref: Optional[str] = None
    notes: Optional[str] = None


# --- Endpoints ---

# 1. Categories / Plano de Contas
@router.get("/categories", response_model=List[CategoryResponse])
async def list_categories(
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header),
    db: AsyncSession = Depends(get_secure_session)
):
    categories = await FinancialService.list_categories(db, tenant_id)
    await db.commit()
    return categories

@router.post("/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    payload: CategoryCreate,
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header),
    db: AsyncSession = Depends(get_secure_session)
):
    category = await FinancialService.create_category(db, tenant_id, payload.model_dump())
    await db.commit()
    return category


# 2. Cost Centers / Centros de Custo
@router.get("/cost-centers", response_model=List[CostCenterResponse])
async def list_cost_centers(
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header),
    db: AsyncSession = Depends(get_secure_session)
):
    cost_centers = await FinancialService.list_cost_centers(db, tenant_id)
    await db.commit()
    return cost_centers

@router.post("/cost-centers", response_model=CostCenterResponse, status_code=status.HTTP_201_CREATED)
async def create_cost_center(
    payload: CostCenterCreate,
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header),
    db: AsyncSession = Depends(get_secure_session)
):
    cost_center = await FinancialService.create_cost_center(db, tenant_id, payload.model_dump())
    await db.commit()
    return cost_center


# 3. Bank Accounts / Contas Bancárias e Caixas
@router.get("/bank-accounts", response_model=List[BankAccountResponse])
async def list_bank_accounts(
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header),
    db: AsyncSession = Depends(get_secure_session)
):
    accounts = await FinancialService.list_bank_accounts(db, tenant_id)
    await db.commit()
    return accounts

@router.post("/bank-accounts", response_model=BankAccountResponse, status_code=status.HTTP_201_CREATED)
async def create_bank_account(
    payload: BankAccountCreate,
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header),
    db: AsyncSession = Depends(get_secure_session)
):
    account = await FinancialService.create_bank_account(db, tenant_id, payload.model_dump())
    await db.commit()
    return account


# 4. Dashboard Metrics
@router.get("/payables/dashboard")
async def get_payables_dashboard(
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header),
    db: AsyncSession = Depends(get_secure_session)
):
    dashboard = await FinancialService.get_payables_dashboard(db, tenant_id)
    await db.commit()
    return dashboard


# 5. Payable Bills / Contas a Pagar
@router.get("/payables")
async def list_payable_bills(
    status: Optional[str] = Query(None),
    supplier_id: Optional[uuid.UUID] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header),
    db: AsyncSession = Depends(get_secure_session)
):
    bills = await FinancialService.list_payable_bills(
        db, tenant_id, status=status, supplier_id=supplier_id, start_date=start_date, end_date=end_date
    )
    await db.commit()
    return bills

@router.post("/payables", status_code=status.HTTP_201_CREATED)
async def create_payable_bill(
    payload: PayableBillCreate,
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header),
    db: AsyncSession = Depends(get_secure_session)
):
    try:
        data = payload.model_dump()
        if data.get("installments"):
            data["installments"] = [
                {
                    "installment_number": inst.installment_number,
                    "total_installments": inst.total_installments,
                    "due_date": inst.due_date,
                    "amount": inst.amount,
                    "barcode": inst.barcode,
                    "pix_code": inst.pix_code,
                }
                for inst in payload.installments # type: ignore
            ]
        bill = await FinancialService.create_payable_bill(db, tenant_id, data)
        await db.commit()
        return bill
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/payables/{bill_id}")
async def get_payable_bill(
    bill_id: uuid.UUID,
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header),
    db: AsyncSession = Depends(get_secure_session)
):
    bill = await FinancialService.get_payable_bill(db, tenant_id, bill_id)
    if not bill:
        raise HTTPException(status_code=404, detail="Título a pagar não encontrado")
    await db.commit()
    return bill

@router.post("/payables/installments/{installment_id}/settle")
async def settle_installment(
    installment_id: uuid.UUID,
    payload: SettleInstallmentPayload,
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header),
    db: AsyncSession = Depends(get_secure_session)
):
    try:
        settled = await FinancialService.settle_installment(db, tenant_id, installment_id, payload.model_dump())
        await db.commit()
        return settled
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/payables/{bill_id}")
async def cancel_payable_bill(
    bill_id: uuid.UUID,
    reason: Optional[str] = Query(None),
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header),
    db: AsyncSession = Depends(get_secure_session)
):
    try:
        res = await FinancialService.cancel_payable_bill(db, tenant_id, bill_id, reason=reason)
        await db.commit()
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# =========================================================================
# ACCOUNTS RECEIVABLE / CONTAS A RECEBER & ADQUIRENTES
# =========================================================================

# 6. Payment Acquirers / Maquininhas & Plataformas
@router.get("/acquirers", response_model=List[AcquirerResponse])
async def list_acquirers(
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header),
    db: AsyncSession = Depends(get_secure_session)
):
    acquirers = await FinancialService.list_acquirers(db, tenant_id)
    await db.commit()
    return acquirers

@router.post("/acquirers", response_model=AcquirerResponse, status_code=status.HTTP_201_CREATED)
async def create_acquirer(
    payload: AcquirerCreate,
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header),
    db: AsyncSession = Depends(get_secure_session)
):
    acquirer = await FinancialService.create_acquirer(db, tenant_id, payload.model_dump())
    await db.commit()
    return acquirer


# 7. Receivables Dashboard
@router.get("/receivables/dashboard")
async def get_receivables_dashboard(
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header),
    db: AsyncSession = Depends(get_secure_session)
):
    dashboard = await FinancialService.get_receivables_dashboard(db, tenant_id)
    await db.commit()
    return dashboard


# 8. Receivable Invoices / Títulos a Receber
@router.get("/receivables")
async def list_receivable_invoices(
    status: Optional[str] = Query(None),
    channel: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header),
    db: AsyncSession = Depends(get_secure_session)
):
    invoices = await FinancialService.list_receivable_invoices(
        db, tenant_id, status=status, channel=channel, start_date=start_date, end_date=end_date
    )
    await db.commit()
    return invoices

@router.post("/receivables", status_code=status.HTTP_201_CREATED)
async def create_receivable_invoice(
    payload: ReceivableInvoiceCreate,
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header),
    db: AsyncSession = Depends(get_secure_session)
):
    try:
        data = payload.model_dump()
        if data.get("installments"):
            data["installments"] = [
                {
                    "installment_number": inst.installment_number,
                    "total_installments": inst.total_installments,
                    "payment_method": inst.payment_method,
                    "card_brand": inst.card_brand,
                    "gross_amount": inst.gross_amount,
                    "fee_percentage": inst.fee_percentage,
                    "expected_settlement_date": inst.expected_settlement_date,
                    "nsu": inst.nsu,
                    "authorization_code": inst.authorization_code,
                }
                for inst in payload.installments # type: ignore
            ]
        invoice = await FinancialService.create_receivable_invoice(db, tenant_id, data)
        await db.commit()
        return invoice
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/receivables/{invoice_id}")
async def get_receivable_invoice(
    invoice_id: uuid.UUID,
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header),
    db: AsyncSession = Depends(get_secure_session)
):
    invoice = await FinancialService.get_receivable_invoice(db, tenant_id, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Título a receber não encontrado")
    await db.commit()
    return invoice

@router.post("/receivables/installments/{installment_id}/settle")
async def settle_receivable_installment(
    installment_id: uuid.UUID,
    payload: SettleReceivableInstallmentPayload,
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header),
    db: AsyncSession = Depends(get_secure_session)
):
    try:
        settled = await FinancialService.settle_receivable_installment(
            db, tenant_id, installment_id, payload.model_dump()
        )
        await db.commit()
        return settled
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/receivables/{invoice_id}")
async def cancel_receivable_invoice(
    invoice_id: uuid.UUID,
    reason: Optional[str] = Query(None),
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header),
    db: AsyncSession = Depends(get_secure_session)
):
    try:
        res = await FinancialService.cancel_receivable_invoice(db, tenant_id, invoice_id, reason=reason)
        await db.commit()
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# --- PHASE 3: CASH FLOW, FINANCIAL DRE & BANK STATEMENTS ---

class UploadOFXPayload(BaseModel):
    bank_account_id: uuid.UUID
    ofx_content: str

class ReconcileBankTransactionPayload(BaseModel):
    settlement_type: str # PAYABLE, RECEIVABLE, TRANSFER, MANUAL_EXPENSE, MANUAL_INCOME
    settlement_id: Optional[uuid.UUID] = None
    notes: Optional[str] = None


@router.get("/cash-flow")
async def get_cash_flow(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header),
    db: AsyncSession = Depends(get_secure_session)
):
    try:
        res = await FinancialService.get_cash_flow_projection(
            db, tenant_id, start_date=start_date, end_date=end_date
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/dre")
async def get_financial_dre(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    view_type: str = Query("COMPETENCE"), # COMPETENCE ou CASH
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header),
    db: AsyncSession = Depends(get_secure_session)
):
    try:
        res = await FinancialService.get_financial_dre(
            db, tenant_id, start_date=start_date, end_date=end_date, view_type=view_type
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/bank-statements/upload")
async def upload_bank_statement_ofx(
    payload: UploadOFXPayload,
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header),
    db: AsyncSession = Depends(get_secure_session)
):
    try:
        res = await FinancialService.import_bank_statement_ofx(
            db, tenant_id, payload.bank_account_id, payload.ofx_content
        )
        await db.commit()
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bank-statements")
async def list_bank_statement_transactions(
    bank_account_id: Optional[uuid.UUID] = Query(None),
    is_reconciled: Optional[bool] = Query(None),
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header),
    db: AsyncSession = Depends(get_secure_session)
):
    try:
        res = await FinancialService.list_bank_statement_transactions(
            db, tenant_id, bank_account_id=bank_account_id, is_reconciled=is_reconciled
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/bank-statements/{tx_id}/reconcile")
async def reconcile_bank_statement_transaction(
    tx_id: uuid.UUID,
    payload: ReconcileBankTransactionPayload,
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header),
    db: AsyncSession = Depends(get_secure_session)
):
    try:
        res = await FinancialService.reconcile_bank_transaction(
            db, tenant_id, tx_id,
            settlement_type=payload.settlement_type,
            settlement_id=payload.settlement_id,
            notes=payload.notes
        )
        await db.commit()
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



