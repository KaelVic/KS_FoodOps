import uuid
from decimal import Decimal
from datetime import datetime, timezone, date, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, and_, or_, desc, asc

from modules.financial.models import (
    FinancialCategory,
    CostCenter,
    BankAccount,
    PaymentMethod,
    PayableBill,
    PayableInstallment,
    PayableSettlement,
    PaymentAcquirer,
    ReceivableInvoice,
    ReceivableInstallment,
    ReceivableSettlement,
    BankStatementTransaction,
    BankReconciliationRule
)
from modules.suppliers.models import Supplier

DEFAULT_ACQUIRERS = [
    {
        "name": "Stone Pagamentos",
        "acquirer_type": "CREDIT_DEBIT",
        "debit_fee_percentage": Decimal("1.49"),
        "credit_1x_fee_percentage": Decimal("2.79"),
        "credit_inst_fee_percentage": Decimal("3.69"),
        "voucher_fee_percentage": Decimal("5.50"),
        "delivery_fee_percentage": Decimal("0.00"),
        "pix_fee_percentage": Decimal("0.00"),
        "settlement_days_debit": 1,
        "settlement_days_credit": 30,
        "settlement_days_voucher": 30,
        "settlement_days_delivery": 1,
    },
    {
        "name": "Cielo",
        "acquirer_type": "CREDIT_DEBIT",
        "debit_fee_percentage": Decimal("1.59"),
        "credit_1x_fee_percentage": Decimal("2.99"),
        "credit_inst_fee_percentage": Decimal("3.99"),
        "voucher_fee_percentage": Decimal("5.80"),
        "delivery_fee_percentage": Decimal("0.00"),
        "pix_fee_percentage": Decimal("0.00"),
        "settlement_days_debit": 1,
        "settlement_days_credit": 30,
        "settlement_days_voucher": 30,
        "settlement_days_delivery": 1,
    },
    {
        "name": "iFood Marketplace & Entrega",
        "acquirer_type": "DELIVERY_PLATFORM",
        "debit_fee_percentage": Decimal("0.00"),
        "credit_1x_fee_percentage": Decimal("0.00"),
        "credit_inst_fee_percentage": Decimal("0.00"),
        "voucher_fee_percentage": Decimal("0.00"),
        "delivery_fee_percentage": Decimal("23.00"),
        "pix_fee_percentage": Decimal("0.00"),
        "settlement_days_debit": 7,
        "settlement_days_credit": 7,
        "settlement_days_voucher": 7,
        "settlement_days_delivery": 7,
    },
    {
        "name": "VR Benefícios / Vale Refeição",
        "acquirer_type": "MEAL_VOUCHER",
        "debit_fee_percentage": Decimal("0.00"),
        "credit_1x_fee_percentage": Decimal("0.00"),
        "credit_inst_fee_percentage": Decimal("0.00"),
        "voucher_fee_percentage": Decimal("5.20"),
        "delivery_fee_percentage": Decimal("0.00"),
        "pix_fee_percentage": Decimal("0.00"),
        "settlement_days_debit": 30,
        "settlement_days_credit": 30,
        "settlement_days_voucher": 30,
        "settlement_days_delivery": 30,
    },
    {
        "name": "PIX Direto / Banco",
        "acquirer_type": "PIX_GATEWAY",
        "debit_fee_percentage": Decimal("0.00"),
        "credit_1x_fee_percentage": Decimal("0.00"),
        "credit_inst_fee_percentage": Decimal("0.00"),
        "voucher_fee_percentage": Decimal("0.00"),
        "delivery_fee_percentage": Decimal("0.00"),
        "pix_fee_percentage": Decimal("0.00"),
        "settlement_days_debit": 0,
        "settlement_days_credit": 0,
        "settlement_days_voucher": 0,
        "settlement_days_delivery": 0,
    }
]

DEFAULT_CATEGORIES = [
    {"code": "1.01", "name": "CMV / Insumos Alimentícios", "type": "EXPENSE_CMV"},
    {"code": "1.02", "name": "Bebidas & Bar", "type": "EXPENSE_CMV"},
    {"code": "1.03", "name": "Embalagens & Descartáveis", "type": "EXPENSE_OPERATIONAL"},
    {"code": "2.01", "name": "Aluguel & Condomínio", "type": "EXPENSE_ADMIN"},
    {"code": "2.02", "name": "Energia Elétrica & Gás", "type": "EXPENSE_OPERATIONAL"},
    {"code": "2.03", "name": "Água & Saneamento", "type": "EXPENSE_OPERATIONAL"},
    {"code": "2.04", "name": "Internet & Telefonia", "type": "EXPENSE_ADMIN"},
    {"code": "3.01", "name": "Folha de Pagamento / Salários", "type": "EXPENSE_PERSONNEL"},
    {"code": "3.02", "name": "Encargos & Benefícios", "type": "EXPENSE_PERSONNEL"},
    {"code": "4.01", "name": "Manutenção & Equipamentos", "type": "EXPENSE_OPERATIONAL"},
    {"code": "4.02", "name": "Marketing & Publicidade", "type": "EXPENSE_OPERATIONAL"},
    {"code": "5.01", "name": "Impostos & Tributos (Simples/ICMS)", "type": "EXPENSE_TAX"},
    {"code": "5.02", "name": "Taxas Bancárias & Maquininhas", "type": "EXPENSE_FINANCIAL"},
]

DEFAULT_COST_CENTERS = [
    {"code": "CC-COZ", "name": "Cozinha Principal", "description": "Produção e manipulação de alimentos"},
    {"code": "CC-BAR", "name": "Bar & Salão", "description": "Atendimento ao cliente e bebidas"},
    {"code": "CC-DEL", "name": "Delivery & Embalagem", "description": "Operação de entregas e despacho"},
    {"code": "CC-ADM", "name": "Administrativo & Diretoria", "description": "Gestão geral e escritório"},
]

class FinancialService:
    @staticmethod
    async def seed_defaults_if_empty(session: AsyncSession, tenant_id: uuid.UUID) -> None:
        cat_stmt = select(func.count(FinancialCategory.id)).where(FinancialCategory.tenant_id == tenant_id)
        cat_count = (await session.execute(cat_stmt)).scalar() or 0
        if cat_count == 0:
            for cat in DEFAULT_CATEGORIES:
                session.add(FinancialCategory(
                    tenant_id=tenant_id,
                    code=cat["code"],
                    name=cat["name"],
                    type=cat["type"],
                    is_active=True
                ))

        cc_stmt = select(func.count(CostCenter.id)).where(CostCenter.tenant_id == tenant_id)
        cc_count = (await session.execute(cc_stmt)).scalar() or 0
        if cc_count == 0:
            for cc in DEFAULT_COST_CENTERS:
                session.add(CostCenter(
                    tenant_id=tenant_id,
                    code=cc["code"],
                    name=cc["name"],
                    description=cc["description"],
                    is_active=True
                ))

        ba_stmt = select(func.count(BankAccount.id)).where(BankAccount.tenant_id == tenant_id)
        ba_count = (await session.execute(ba_stmt)).scalar() or 0
        if ba_count == 0:
            session.add(BankAccount(
                tenant_id=tenant_id,
                name="Conta Principal (Banco)",
                account_type="CHECKING",
                initial_balance=Decimal("0.00"),
                current_balance=Decimal("0.00"),
                is_active=True
            ))
            session.add(BankAccount(
                tenant_id=tenant_id,
                name="Caixa Gaveta (Físico)",
                account_type="CASH",
                initial_balance=Decimal("0.00"),
                current_balance=Decimal("0.00"),
                is_active=True
            ))

        acq_stmt = select(func.count(PaymentAcquirer.id)).where(PaymentAcquirer.tenant_id == tenant_id)
        acq_count = (await session.execute(acq_stmt)).scalar() or 0
        if acq_count == 0:
            for acq in DEFAULT_ACQUIRERS:
                session.add(PaymentAcquirer(
                    tenant_id=tenant_id,
                    name=acq["name"],
                    acquirer_type=acq["acquirer_type"],
                    debit_fee_percentage=acq["debit_fee_percentage"],
                    credit_1x_fee_percentage=acq["credit_1x_fee_percentage"],
                    credit_inst_fee_percentage=acq["credit_inst_fee_percentage"],
                    voucher_fee_percentage=acq["voucher_fee_percentage"],
                    delivery_fee_percentage=acq["delivery_fee_percentage"],
                    pix_fee_percentage=acq["pix_fee_percentage"],
                    settlement_days_debit=acq["settlement_days_debit"],
                    settlement_days_credit=acq["settlement_days_credit"],
                    settlement_days_voucher=acq["settlement_days_voucher"],
                    settlement_days_delivery=acq["settlement_days_delivery"],
                    is_active=True
                ))

        if cat_count == 0 or cc_count == 0 or ba_count == 0 or acq_count == 0:
            await session.flush()

    # --- Categories ---
    @staticmethod
    async def list_categories(session: AsyncSession, tenant_id: uuid.UUID) -> List[FinancialCategory]:
        await FinancialService.seed_defaults_if_empty(session, tenant_id)
        stmt = select(FinancialCategory).where(
            FinancialCategory.tenant_id == tenant_id,
            FinancialCategory.is_active == True
        ).order_by(FinancialCategory.code.asc(), FinancialCategory.name.asc())
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def create_category(session: AsyncSession, tenant_id: uuid.UUID, data: Dict[str, Any]) -> FinancialCategory:
        category = FinancialCategory(
            tenant_id=tenant_id,
            code=data.get("code"),
            name=data["name"],
            type=data.get("type", "EXPENSE_OPERATIONAL"),
            parent_id=uuid.UUID(str(data["parent_id"])) if data.get("parent_id") else None,
            is_active=True
        )
        session.add(category)
        await session.flush()
        return category

    # --- Cost Centers ---
    @staticmethod
    async def list_cost_centers(session: AsyncSession, tenant_id: uuid.UUID) -> List[CostCenter]:
        await FinancialService.seed_defaults_if_empty(session, tenant_id)
        stmt = select(CostCenter).where(
            CostCenter.tenant_id == tenant_id,
            CostCenter.is_active == True
        ).order_by(CostCenter.code.asc(), CostCenter.name.asc())
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def create_cost_center(session: AsyncSession, tenant_id: uuid.UUID, data: Dict[str, Any]) -> CostCenter:
        cost_center = CostCenter(
            tenant_id=tenant_id,
            code=data.get("code"),
            name=data["name"],
            description=data.get("description"),
            is_active=True
        )
        session.add(cost_center)
        await session.flush()
        return cost_center

    # --- Bank Accounts ---
    @staticmethod
    async def list_bank_accounts(session: AsyncSession, tenant_id: uuid.UUID) -> List[BankAccount]:
        await FinancialService.seed_defaults_if_empty(session, tenant_id)
        stmt = select(BankAccount).where(
            BankAccount.tenant_id == tenant_id,
            BankAccount.is_active == True
        ).order_by(BankAccount.name.asc())
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def create_bank_account(session: AsyncSession, tenant_id: uuid.UUID, data: Dict[str, Any]) -> BankAccount:
        initial_balance = Decimal(str(data.get("initial_balance", "0.00")))
        account = BankAccount(
            tenant_id=tenant_id,
            name=data["name"],
            account_type=data.get("account_type", "CHECKING"),
            bank_code=data.get("bank_code"),
            agency_number=data.get("agency_number"),
            account_number=data.get("account_number"),
            pix_key=data.get("pix_key"),
            initial_balance=initial_balance,
            current_balance=initial_balance,
            is_active=True
        )
        session.add(account)
        await session.flush()
        return account

    # --- Payable Bills ---
    @staticmethod
    async def list_payable_bills(
        session: AsyncSession,
        tenant_id: uuid.UUID,
        status: Optional[str] = None,
        supplier_id: Optional[uuid.UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        stmt = select(PayableBill).where(PayableBill.tenant_id == tenant_id)

        if status:
            stmt = stmt.where(PayableBill.status == status)
        if supplier_id:
            stmt = stmt.where(PayableBill.supplier_id == supplier_id)
        if start_date:
            stmt = stmt.where(PayableBill.first_due_date >= start_date)
        if end_date:
            stmt = stmt.where(PayableBill.first_due_date <= end_date)

        stmt = stmt.order_by(PayableBill.first_due_date.asc(), PayableBill.created_at.desc())
        bills = (await session.execute(stmt)).scalars().all()

        results = []
        now = datetime.now(timezone.utc)

        for bill in bills:
            sup_stmt = select(Supplier).where(Supplier.id == bill.supplier_id)
            supplier = (await session.execute(sup_stmt)).scalar_one_or_none()

            category = None
            if bill.category_id:
                cat_stmt = select(FinancialCategory).where(FinancialCategory.id == bill.category_id)
                category = (await session.execute(cat_stmt)).scalar_one_or_none()

            cost_center = None
            if bill.cost_center_id:
                cc_stmt = select(CostCenter).where(CostCenter.id == bill.cost_center_id)
                cost_center = (await session.execute(cc_stmt)).scalar_one_or_none()

            inst_stmt = select(PayableInstallment).where(
                PayableInstallment.payable_bill_id == bill.id
            ).order_by(PayableInstallment.installment_number.asc())
            installments = (await session.execute(inst_stmt)).scalars().all()

            paid_amount = Decimal("0")
            for inst in installments:
                if inst.status in ("PENDING", "SCHEDULED") and inst.due_date < now:
                    inst.status = "OVERDUE"
                if inst.status == "PAID":
                    paid_amount += inst.amount

            remaining_amount = bill.total_amount - paid_amount

            results.append({
                "id": str(bill.id),
                "supplier_id": str(bill.supplier_id),
                "supplier_name": supplier.name if supplier else "Fornecedor",
                "category_id": str(bill.category_id) if bill.category_id else None,
                "category_name": category.name if category else None,
                "cost_center_id": str(bill.cost_center_id) if bill.cost_center_id else None,
                "cost_center_name": cost_center.name if cost_center else None,
                "document_number": bill.document_number,
                "description": bill.description,
                "total_amount": float(bill.total_amount),
                "paid_amount": float(paid_amount),
                "remaining_amount": float(remaining_amount),
                "issue_date": bill.issue_date.isoformat(),
                "first_due_date": bill.first_due_date.isoformat(),
                "status": bill.status,
                "notes": bill.notes,
                "installments_count": len(installments),
                "installments": [
                    {
                        "id": str(inst.id),
                        "installment_number": inst.installment_number,
                        "total_installments": inst.total_installments,
                        "due_date": inst.due_date.isoformat(),
                        "amount": float(inst.amount),
                        "barcode": inst.barcode,
                        "pix_code": inst.pix_code,
                        "status": inst.status,
                    }
                    for inst in installments
                ]
            })

        return results

    @staticmethod
    async def get_payable_bill(session: AsyncSession, tenant_id: uuid.UUID, bill_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        stmt = select(PayableBill).where(
            PayableBill.tenant_id == tenant_id,
            PayableBill.id == bill_id
        )
        bill = (await session.execute(stmt)).scalar_one_or_none()
        if not bill:
            return None

        sup_stmt = select(Supplier).where(Supplier.id == bill.supplier_id)
        supplier = (await session.execute(sup_stmt)).scalar_one_or_none()

        category = None
        if bill.category_id:
            cat_stmt = select(FinancialCategory).where(FinancialCategory.id == bill.category_id)
            category = (await session.execute(cat_stmt)).scalar_one_or_none()

        cost_center = None
        if bill.cost_center_id:
            cc_stmt = select(CostCenter).where(CostCenter.id == bill.cost_center_id)
            cost_center = (await session.execute(cc_stmt)).scalar_one_or_none()

        inst_stmt = select(PayableInstallment).where(
            PayableInstallment.payable_bill_id == bill.id
        ).order_by(PayableInstallment.installment_number.asc())
        installments = (await session.execute(inst_stmt)).scalars().all()

        now = datetime.now(timezone.utc)
        installments_data = []

        for inst in installments:
            if inst.status in ("PENDING", "SCHEDULED") and inst.due_date < now:
                inst.status = "OVERDUE"

            settle_stmt = select(PayableSettlement).where(PayableSettlement.installment_id == inst.id)
            settlements = (await session.execute(settle_stmt)).scalars().all()

            installments_data.append({
                "id": str(inst.id),
                "installment_number": inst.installment_number,
                "total_installments": inst.total_installments,
                "due_date": inst.due_date.isoformat(),
                "amount": float(inst.amount),
                "barcode": inst.barcode,
                "pix_code": inst.pix_code,
                "status": inst.status,
                "settlements": [
                    {
                        "id": str(s.id),
                        "bank_account_id": str(s.bank_account_id),
                        "payment_method": s.payment_method,
                        "settlement_date": s.settlement_date.isoformat(),
                        "principal_amount": float(s.principal_amount),
                        "interest_amount": float(s.interest_amount),
                        "fine_amount": float(s.fine_amount),
                        "discount_amount": float(s.discount_amount),
                        "total_paid": float(s.total_paid),
                        "transaction_reference": s.transaction_reference,
                        "notes": s.notes,
                    }
                    for s in settlements
                ]
            })

        return {
            "id": str(bill.id),
            "supplier_id": str(bill.supplier_id),
            "supplier_name": supplier.name if supplier else "Fornecedor",
            "category_id": str(bill.category_id) if bill.category_id else None,
            "category_name": category.name if category else None,
            "cost_center_id": str(bill.cost_center_id) if bill.cost_center_id else None,
            "cost_center_name": cost_center.name if cost_center else None,
            "document_number": bill.document_number,
            "description": bill.description,
            "total_amount": float(bill.total_amount),
            "issue_date": bill.issue_date.isoformat(),
            "first_due_date": bill.first_due_date.isoformat(),
            "status": bill.status,
            "notes": bill.notes,
            "installments": installments_data
        }

    @staticmethod
    async def create_payable_bill(session: AsyncSession, tenant_id: uuid.UUID, data: Dict[str, Any]) -> Dict[str, Any]:
        total_amount = Decimal(str(data["total_amount"]))
        installments_data = data.get("installments", [])

        if not installments_data:
            installment_count = int(data.get("installment_count", 1))
            first_due_date_raw = data.get("first_due_date")
            first_due_date = datetime.fromisoformat(first_due_date_raw) if isinstance(first_due_date_raw, str) else (first_due_date_raw or datetime.now(timezone.utc))
            
            installment_val = (total_amount / installment_count).quantize(Decimal("0.01"))
            remainder = total_amount - (installment_val * installment_count)

            installments_data = []
            for i in range(installment_count):
                due = first_due_date + timedelta(days=30 * i)
                amt = installment_val if i < installment_count - 1 else installment_val + remainder
                installments_data.append({
                    "installment_number": i + 1,
                    "total_installments": installment_count,
                    "due_date": due,
                    "amount": amt,
                    "barcode": data.get("barcode"),
                    "pix_code": data.get("pix_code"),
                })
        else:
            sum_installments = sum((Decimal(str(item["amount"])) for item in installments_data), Decimal("0"))
            if abs(sum_installments - total_amount) > Decimal("0.01"):
                raise ValueError(f"A soma das parcelas ({sum_installments}) não confere com o valor total ({total_amount}).")

        issue_date_raw = data.get("issue_date")
        issue_date = datetime.fromisoformat(issue_date_raw) if isinstance(issue_date_raw, str) else (issue_date_raw or datetime.now(timezone.utc))

        first_due = installments_data[0]["due_date"]
        if isinstance(first_due, str):
            first_due = datetime.fromisoformat(first_due)

        bill = PayableBill(
            tenant_id=tenant_id,
            supplier_id=uuid.UUID(str(data["supplier_id"])),
            category_id=uuid.UUID(str(data["category_id"])) if data.get("category_id") else None,
            cost_center_id=uuid.UUID(str(data["cost_center_id"])) if data.get("cost_center_id") else None,
            purchase_order_id=uuid.UUID(str(data["purchase_order_id"])) if data.get("purchase_order_id") else None,
            supplier_invoice_id=uuid.UUID(str(data["supplier_invoice_id"])) if data.get("supplier_invoice_id") else None,
            document_number=data.get("document_number"),
            description=data["description"],
            total_amount=total_amount,
            issue_date=issue_date,
            first_due_date=first_due,
            status="PENDING",
            notes=data.get("notes")
        )
        session.add(bill)
        await session.flush()

        total_inst = len(installments_data)
        for idx, item in enumerate(installments_data):
            due = item["due_date"]
            if isinstance(due, str):
                due = datetime.fromisoformat(due)

            inst = PayableInstallment(
                tenant_id=tenant_id,
                payable_bill_id=bill.id,
                installment_number=item.get("installment_number", idx + 1),
                total_installments=total_inst,
                due_date=due,
                amount=Decimal(str(item["amount"])),
                barcode=item.get("barcode") or data.get("barcode"),
                pix_code=item.get("pix_code") or data.get("pix_code"),
                status="PENDING"
            )
            session.add(inst)

        await session.flush()
        return await FinancialService.get_payable_bill(session, tenant_id, bill.id) # type: ignore

    @staticmethod
    async def settle_installment(session: AsyncSession, tenant_id: uuid.UUID, installment_id: uuid.UUID, settlement_data: Dict[str, Any]) -> Dict[str, Any]:
        stmt = select(PayableInstallment).where(
            PayableInstallment.tenant_id == tenant_id,
            PayableInstallment.id == installment_id
        )
        installment = (await session.execute(stmt)).scalar_one_or_none()
        if not installment:
            raise ValueError("Parcela não encontrada.")

        if installment.status == "PAID":
            raise ValueError("Esta parcela já foi liquidada/paga.")

        bank_account_id = uuid.UUID(str(settlement_data["bank_account_id"]))
        ba_stmt = select(BankAccount).where(
            BankAccount.tenant_id == tenant_id,
            BankAccount.id == bank_account_id
        )
        bank_account = (await session.execute(ba_stmt)).scalar_one_or_none()
        if not bank_account:
            raise ValueError("Conta bancária de liquidação não encontrada.")

        principal_amount = installment.amount
        interest_amount = Decimal(str(settlement_data.get("interest_amount", "0.00")))
        fine_amount = Decimal(str(settlement_data.get("fine_amount", "0.00")))
        discount_amount = Decimal(str(settlement_data.get("discount_amount", "0.00")))
        
        total_paid = principal_amount + interest_amount + fine_amount - discount_amount

        settlement_date_raw = settlement_data.get("settlement_date")
        settlement_date = datetime.fromisoformat(settlement_date_raw) if isinstance(settlement_date_raw, str) else (settlement_date_raw or datetime.now(timezone.utc))

        settlement = PayableSettlement(
            tenant_id=tenant_id,
            installment_id=installment.id,
            bank_account_id=bank_account.id,
            payment_method=settlement_data.get("payment_method", "PIX"),
            settlement_date=settlement_date,
            principal_amount=principal_amount,
            interest_amount=interest_amount,
            fine_amount=fine_amount,
            discount_amount=discount_amount,
            total_paid=total_paid,
            receipt_url=settlement_data.get("receipt_url"),
            transaction_reference=settlement_data.get("transaction_reference"),
            notes=settlement_data.get("notes")
        )
        session.add(settlement)

        # Debit from bank account balance
        bank_account.current_balance = bank_account.current_balance - total_paid

        # Update installment status
        installment.status = "PAID"
        await session.flush()

        # Update parent bill status
        all_inst_stmt = select(PayableInstallment).where(PayableInstallment.payable_bill_id == installment.payable_bill_id)
        all_installments = (await session.execute(all_inst_stmt)).scalars().all()

        bill_stmt = select(PayableBill).where(PayableBill.id == installment.payable_bill_id)
        bill = (await session.execute(bill_stmt)).scalar_one_or_none()
        if bill:
            if all(inst.status == "PAID" for inst in all_installments):
                bill.status = "PAID"
            else:
                bill.status = "PARTIALLY_PAID"

        await session.flush()
        return await FinancialService.get_payable_bill(session, tenant_id, installment.payable_bill_id) # type: ignore

    @staticmethod
    async def cancel_payable_bill(session: AsyncSession, tenant_id: uuid.UUID, bill_id: uuid.UUID, reason: Optional[str] = None) -> Dict[str, Any]:
        stmt = select(PayableBill).where(
            PayableBill.tenant_id == tenant_id,
            PayableBill.id == bill_id
        )
        bill = (await session.execute(stmt)).scalar_one_or_none()
        if not bill:
            raise ValueError("Título a pagar não encontrado.")

        inst_stmt = select(PayableInstallment).where(PayableInstallment.payable_bill_id == bill.id)
        installments = (await session.execute(inst_stmt)).scalars().all()

        if any(inst.status == "PAID" for inst in installments):
            raise ValueError("Não é possível cancelar um título com parcelas já pagas. Estorne os pagamentos primeiro.")

        bill.status = "CANCELLED"
        if reason:
            bill.notes = f"{bill.notes or ''}\n[Cancelado]: {reason}".strip()

        for inst in installments:
            inst.status = "CANCELLED"

        await session.flush()
        return {"message": "Título a pagar cancelado com sucesso."}

    @staticmethod
    async def get_payables_dashboard(session: AsyncSession, tenant_id: uuid.UUID) -> Dict[str, Any]:
        await FinancialService.seed_defaults_if_empty(session, tenant_id)
        now = datetime.now(timezone.utc)
        today_start = datetime(now.year, now.month, now.day, 0, 0, 0, tzinfo=timezone.utc)
        today_end = datetime(now.year, now.month, now.day, 23, 59, 59, tzinfo=timezone.utc)
        next_7_days = today_end + timedelta(days=7)

        month_start = datetime(now.year, now.month, 1, 0, 0, 0, tzinfo=timezone.utc)
        if now.month == 12:
            month_end = datetime(now.year + 1, 1, 1, 0, 0, 0, tzinfo=timezone.utc) - timedelta(seconds=1)
        else:
            month_end = datetime(now.year, now.month + 1, 1, 0, 0, 0, tzinfo=timezone.utc) - timedelta(seconds=1)

        # 1. Total due today
        due_today_stmt = select(PayableInstallment).where(
            PayableInstallment.tenant_id == tenant_id,
            PayableInstallment.status.in_(["PENDING", "SCHEDULED", "OVERDUE"]),
            PayableInstallment.due_date >= today_start,
            PayableInstallment.due_date <= today_end
        )
        due_today_rows = (await session.execute(due_today_stmt)).scalars().all()
        total_due_today = sum((inst.amount for inst in due_today_rows), Decimal("0"))

        # 2. Total overdue
        overdue_stmt = select(PayableInstallment).where(
            PayableInstallment.tenant_id == tenant_id,
            PayableInstallment.status.in_(["PENDING", "SCHEDULED", "OVERDUE"]),
            PayableInstallment.due_date < today_start
        )
        overdue_rows = (await session.execute(overdue_stmt)).scalars().all()
        total_overdue = sum((inst.amount for inst in overdue_rows), Decimal("0"))

        # 3. Total next 7 days
        next_7_stmt = select(PayableInstallment).where(
            PayableInstallment.tenant_id == tenant_id,
            PayableInstallment.status.in_(["PENDING", "SCHEDULED", "OVERDUE"]),
            PayableInstallment.due_date >= today_start,
            PayableInstallment.due_date <= next_7_days
        )
        next_7_rows = (await session.execute(next_7_stmt)).scalars().all()
        total_next_7_days = sum((inst.amount for inst in next_7_rows), Decimal("0"))

        # 4. Total due month
        month_stmt = select(PayableInstallment).where(
            PayableInstallment.tenant_id == tenant_id,
            PayableInstallment.status.in_(["PENDING", "SCHEDULED", "OVERDUE"]),
            PayableInstallment.due_date >= month_start,
            PayableInstallment.due_date <= month_end
        )
        month_due_rows = (await session.execute(month_stmt)).scalars().all()
        total_due_month = sum((inst.amount for inst in month_due_rows), Decimal("0"))

        # 5. Total paid month
        settle_stmt = select(PayableSettlement).where(
            PayableSettlement.tenant_id == tenant_id,
            PayableSettlement.settlement_date >= month_start,
            PayableSettlement.settlement_date <= month_end
        )
        settlements_month = (await session.execute(settle_stmt)).scalars().all()
        total_paid_month = sum((s.total_paid for s in settlements_month), Decimal("0"))

        # 6. Upcoming installments
        upcoming_stmt = select(PayableInstallment).where(
            PayableInstallment.tenant_id == tenant_id,
            PayableInstallment.status.in_(["PENDING", "SCHEDULED", "OVERDUE"])
        ).order_by(PayableInstallment.due_date.asc()).limit(10)
        upcoming = (await session.execute(upcoming_stmt)).scalars().all()

        upcoming_list = []
        for inst in upcoming:
            bill_stmt = select(PayableBill).where(PayableBill.id == inst.payable_bill_id)
            bill = (await session.execute(bill_stmt)).scalar_one_or_none()
            
            supplier = None
            if bill:
                sup_stmt = select(Supplier).where(Supplier.id == bill.supplier_id)
                supplier = (await session.execute(sup_stmt)).scalar_one_or_none()

            status = "OVERDUE" if inst.due_date < now else inst.status

            upcoming_list.append({
                "installment_id": str(inst.id),
                "bill_id": str(bill.id) if bill else "",
                "document_number": bill.document_number if bill else "",
                "description": bill.description if bill else "",
                "supplier_name": supplier.name if supplier else "Fornecedor",
                "installment_number": inst.installment_number,
                "total_installments": inst.total_installments,
                "due_date": inst.due_date.isoformat(),
                "amount": float(inst.amount),
                "barcode": inst.barcode,
                "pix_code": inst.pix_code,
                "status": status
            })

        # 7. Bank accounts balance
        ba_stmt = select(BankAccount).where(
            BankAccount.tenant_id == tenant_id,
            BankAccount.is_active == True
        )
        bank_accounts = (await session.execute(ba_stmt)).scalars().all()
        total_bank_balance = sum((acc.current_balance for acc in bank_accounts), Decimal("0"))

        return {
            "total_due_today": float(total_due_today),
            "total_overdue": float(total_overdue),
            "total_next_7_days": float(total_next_7_days),
            "total_due_month": float(total_due_month),
            "total_paid_month": float(total_paid_month),
            "total_bank_balance": float(total_bank_balance),
            "count_overdue": len(overdue_rows),
            "count_due_today": len(due_today_rows),
            "upcoming_installments": upcoming_list
        }

    # =========================================================================
    # ACCOUNTS RECEIVABLE / CONTAS A RECEBER & CONCILIAÇÃO
    # =========================================================================

    # --- Acquirers / Maquininhas & Plataformas ---
    @staticmethod
    async def list_acquirers(session: AsyncSession, tenant_id: uuid.UUID) -> List[PaymentAcquirer]:
        await FinancialService.seed_defaults_if_empty(session, tenant_id)
        stmt = select(PaymentAcquirer).where(
            PaymentAcquirer.tenant_id == tenant_id,
            PaymentAcquirer.is_active == True
        ).order_by(PaymentAcquirer.name.asc())
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def create_acquirer(session: AsyncSession, tenant_id: uuid.UUID, data: Dict[str, Any]) -> PaymentAcquirer:
        acquirer = PaymentAcquirer(
            tenant_id=tenant_id,
            name=data["name"],
            acquirer_type=data.get("acquirer_type", "CREDIT_DEBIT"),
            debit_fee_percentage=Decimal(str(data.get("debit_fee_percentage", "1.50"))),
            credit_1x_fee_percentage=Decimal(str(data.get("credit_1x_fee_percentage", "2.80"))),
            credit_inst_fee_percentage=Decimal(str(data.get("credit_inst_fee_percentage", "3.80"))),
            voucher_fee_percentage=Decimal(str(data.get("voucher_fee_percentage", "5.50"))),
            delivery_fee_percentage=Decimal(str(data.get("delivery_fee_percentage", "23.00"))),
            pix_fee_percentage=Decimal(str(data.get("pix_fee_percentage", "0.00"))),
            fixed_fee=Decimal(str(data.get("fixed_fee", "0.00"))),
            settlement_days_debit=data.get("settlement_days_debit", 1),
            settlement_days_credit=data.get("settlement_days_credit", 30),
            settlement_days_voucher=data.get("settlement_days_voucher", 30),
            settlement_days_delivery=data.get("settlement_days_delivery", 7),
            is_active=True
        )
        session.add(acquirer)
        await session.flush()
        return acquirer

    # --- Receivable Invoices / Títulos a Receber ---
    @staticmethod
    async def list_receivable_invoices(
        session: AsyncSession,
        tenant_id: uuid.UUID,
        status: Optional[str] = None,
        channel: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        query = select(ReceivableInvoice).where(ReceivableInvoice.tenant_id == tenant_id)

        if status:
            query = query.where(ReceivableInvoice.status == status)
        if channel:
            query = query.where(ReceivableInvoice.channel == channel)
        if start_date:
            query = query.where(ReceivableInvoice.due_date >= start_date)
        if end_date:
            query = query.where(ReceivableInvoice.due_date <= end_date)

        query = query.order_by(ReceivableInvoice.due_date.asc(), ReceivableInvoice.created_at.desc())
        result = await session.execute(query)
        invoices = result.scalars().all()

        output = []
        for inv in invoices:
            inst_stmt = select(ReceivableInstallment).where(
                ReceivableInstallment.invoice_id == inv.id
            ).order_by(ReceivableInstallment.installment_number.asc())
            installments = (await session.execute(inst_stmt)).scalars().all()

            cat_name = None
            if inv.category_id:
                cat_stmt = select(FinancialCategory.name).where(FinancialCategory.id == inv.category_id)
                cat_name = (await session.execute(cat_stmt)).scalar_one_or_none()

            cc_name = None
            if inv.cost_center_id:
                cc_stmt = select(CostCenter.name).where(CostCenter.id == inv.cost_center_id)
                cc_name = (await session.execute(cc_stmt)).scalar_one_or_none()

            inst_list = []
            for inst in installments:
                acq_name = None
                if inst.acquirer_id:
                    acq_stmt = select(PaymentAcquirer.name).where(PaymentAcquirer.id == inst.acquirer_id)
                    acq_name = (await session.execute(acq_stmt)).scalar_one_or_none()

                settle_stmt = select(ReceivableSettlement).where(ReceivableSettlement.installment_id == inst.id)
                settlement = (await session.execute(settle_stmt)).scalar_one_or_none()

                inst_list.append({
                    "id": str(inst.id),
                    "installment_number": inst.installment_number,
                    "total_installments": inst.total_installments,
                    "payment_method": inst.payment_method,
                    "card_brand": inst.card_brand,
                    "acquirer_id": str(inst.acquirer_id) if inst.acquirer_id else None,
                    "acquirer_name": acq_name,
                    "gross_amount": float(inst.gross_amount),
                    "fee_percentage": float(inst.fee_percentage),
                    "fee_amount": float(inst.fee_amount),
                    "net_amount": float(inst.net_amount),
                    "expected_settlement_date": inst.expected_settlement_date.isoformat(),
                    "status": inst.status,
                    "nsu": inst.nsu,
                    "authorization_code": inst.authorization_code,
                    "settlement": {
                        "id": str(settlement.id),
                        "bank_account_id": str(settlement.bank_account_id),
                        "settlement_date": settlement.settlement_date.isoformat(),
                        "gross_amount": float(settlement.gross_amount),
                        "fee_deducted": float(settlement.fee_deducted),
                        "net_received_amount": float(settlement.net_received_amount),
                        "bank_transaction_ref": settlement.bank_transaction_ref
                    } if settlement else None
                })

            output.append({
                "id": str(inv.id),
                "customer_name": inv.customer_name,
                "customer_tax_id": inv.customer_tax_id,
                "channel": inv.channel,
                "document_number": inv.document_number,
                "description": inv.description,
                "category_id": str(inv.category_id) if inv.category_id else None,
                "category_name": cat_name,
                "cost_center_id": str(inv.cost_center_id) if inv.cost_center_id else None,
                "cost_center_name": cc_name,
                "gross_amount": float(inv.gross_amount),
                "deductions_amount": float(inv.deductions_amount),
                "net_amount": float(inv.net_amount),
                "issue_date": inv.issue_date.isoformat(),
                "due_date": inv.due_date.isoformat(),
                "status": inv.status,
                "notes": inv.notes,
                "installments": inst_list,
                "created_at": inv.created_at.isoformat() if inv.created_at else None
            })

        return output

    @staticmethod
    async def create_receivable_invoice(
        session: AsyncSession,
        tenant_id: uuid.UUID,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        gross_amount = Decimal(str(data["gross_amount"]))
        customer_name = data.get("customer_name", "Consumidor Final")
        channel = data.get("channel", "POS")
        description = data.get("description", "Vendas do Dia / Faturamento")
        issue_date = data.get("issue_date") or datetime.now(timezone.utc)
        if isinstance(issue_date, str):
            issue_date = datetime.fromisoformat(issue_date)

        due_date = data.get("due_date") or issue_date
        if isinstance(due_date, str):
            due_date = datetime.fromisoformat(due_date)

        acquirer_id = data.get("acquirer_id")
        acquirer = None
        if acquirer_id:
            acq_stmt = select(PaymentAcquirer).where(
                PaymentAcquirer.id == uuid.UUID(str(acquirer_id)),
                PaymentAcquirer.tenant_id == tenant_id
            )
            acquirer = (await session.execute(acq_stmt)).scalar_one_or_none()

        payment_method = data.get("payment_method", "CREDIT_CARD")
        card_brand = data.get("card_brand")

        # Determine MDR rate & settlement days
        fee_pct = Decimal("0.00")
        settlement_days = 0

        if acquirer:
            if payment_method == "DEBIT_CARD":
                fee_pct = acquirer.debit_fee_percentage
                settlement_days = acquirer.settlement_days_debit
            elif payment_method == "CREDIT_CARD":
                fee_pct = acquirer.credit_1x_fee_percentage
                settlement_days = acquirer.settlement_days_credit
            elif payment_method == "MEAL_VOUCHER":
                fee_pct = acquirer.voucher_fee_percentage
                settlement_days = acquirer.settlement_days_voucher
            elif payment_method == "DELIVERY_ONLINE" or channel == "DELIVERY_IFOOD":
                fee_pct = acquirer.delivery_fee_percentage
                settlement_days = acquirer.settlement_days_delivery
            elif payment_method == "PIX":
                fee_pct = acquirer.pix_fee_percentage
                settlement_days = 0
            elif payment_method == "CASH":
                fee_pct = Decimal("0.00")
                settlement_days = 0
        else:
            if payment_method == "DEBIT_CARD":
                fee_pct = Decimal("1.50")
                settlement_days = 1
            elif payment_method == "CREDIT_CARD":
                fee_pct = Decimal("2.80")
                settlement_days = 30
            elif payment_method == "MEAL_VOUCHER":
                fee_pct = Decimal("5.50")
                settlement_days = 30
            elif channel == "DELIVERY_IFOOD":
                fee_pct = Decimal("23.00")
                settlement_days = 7

        custom_fee_pct = data.get("fee_percentage")
        if custom_fee_pct is not None:
            fee_pct = Decimal(str(custom_fee_pct))

        fee_amount = (gross_amount * fee_pct / Decimal("100")).quantize(Decimal("0.01"))
        net_amount = gross_amount - fee_amount

        invoice = ReceivableInvoice(
            tenant_id=tenant_id,
            customer_name=customer_name,
            customer_tax_id=data.get("customer_tax_id"),
            channel=channel,
            category_id=uuid.UUID(str(data["category_id"])) if data.get("category_id") else None,
            cost_center_id=uuid.UUID(str(data["cost_center_id"])) if data.get("cost_center_id") else None,
            document_number=data.get("document_number"),
            description=description,
            gross_amount=gross_amount,
            deductions_amount=fee_amount,
            net_amount=net_amount,
            issue_date=issue_date,
            due_date=due_date,
            status="PENDING",
            notes=data.get("notes")
        )
        session.add(invoice)
        await session.flush()

        # Installments
        installments_data = data.get("installments")
        if installments_data and len(installments_data) > 0:
            for inst_d in installments_data:
                inst_gross = Decimal(str(inst_d["gross_amount"]))
                inst_fee_pct = Decimal(str(inst_d.get("fee_percentage", fee_pct)))
                inst_fee = (inst_gross * inst_fee_pct / Decimal("100")).quantize(Decimal("0.01"))
                inst_net = inst_gross - inst_fee
                
                exp_date = inst_d.get("expected_settlement_date")
                if isinstance(exp_date, str):
                    exp_date = datetime.fromisoformat(exp_date)
                elif not exp_date:
                    exp_date = issue_date + timedelta(days=settlement_days)

                inst = ReceivableInstallment(
                    tenant_id=tenant_id,
                    invoice_id=invoice.id,
                    acquirer_id=acquirer.id if acquirer else None,
                    installment_number=inst_d.get("installment_number", 1),
                    total_installments=inst_d.get("total_installments", len(installments_data)),
                    payment_method=inst_d.get("payment_method", payment_method),
                    card_brand=inst_d.get("card_brand", card_brand),
                    gross_amount=inst_gross,
                    fee_percentage=inst_fee_pct,
                    fee_amount=inst_fee,
                    net_amount=inst_net,
                    expected_settlement_date=exp_date,
                    status="PENDING",
                    nsu=inst_d.get("nsu"),
                    authorization_code=inst_d.get("authorization_code")
                )
                session.add(inst)
        else:
            exp_date = issue_date + timedelta(days=settlement_days)
            inst = ReceivableInstallment(
                tenant_id=tenant_id,
                invoice_id=invoice.id,
                acquirer_id=acquirer.id if acquirer else None,
                installment_number=1,
                total_installments=1,
                payment_method=payment_method,
                card_brand=card_brand,
                gross_amount=gross_amount,
                fee_percentage=fee_pct,
                fee_amount=fee_amount,
                net_amount=net_amount,
                expected_settlement_date=exp_date,
                status="PENDING",
                nsu=data.get("nsu"),
                authorization_code=data.get("authorization_code")
            )
            session.add(inst)

        await session.flush()
        return await FinancialService.get_receivable_invoice(session, tenant_id, invoice.id) # type: ignore

    @staticmethod
    async def get_receivable_invoice(session: AsyncSession, tenant_id: uuid.UUID, invoice_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        stmt = select(ReceivableInvoice).where(
            ReceivableInvoice.id == uuid.UUID(str(invoice_id)),
            ReceivableInvoice.tenant_id == tenant_id
        )
        invoice = (await session.execute(stmt)).scalar_one_or_none()
        if not invoice:
            return None

        inst_stmt = select(ReceivableInstallment).where(
            ReceivableInstallment.invoice_id == invoice.id
        ).order_by(ReceivableInstallment.installment_number.asc())
        installments = (await session.execute(inst_stmt)).scalars().all()

        cat_name = None
        if invoice.category_id:
            cat_stmt = select(FinancialCategory.name).where(FinancialCategory.id == invoice.category_id)
            cat_name = (await session.execute(cat_stmt)).scalar_one_or_none()

        cc_name = None
        if invoice.cost_center_id:
            cc_stmt = select(CostCenter.name).where(CostCenter.id == invoice.cost_center_id)
            cc_name = (await session.execute(cc_stmt)).scalar_one_or_none()

        inst_list = []
        for inst in installments:
            acq_name = None
            if inst.acquirer_id:
                acq_stmt = select(PaymentAcquirer.name).where(PaymentAcquirer.id == inst.acquirer_id)
                acq_name = (await session.execute(acq_stmt)).scalar_one_or_none()

            settle_stmt = select(ReceivableSettlement).where(ReceivableSettlement.installment_id == inst.id)
            settlement = (await session.execute(settle_stmt)).scalar_one_or_none()

            inst_list.append({
                "id": str(inst.id),
                "installment_number": inst.installment_number,
                "total_installments": inst.total_installments,
                "payment_method": inst.payment_method,
                "card_brand": inst.card_brand,
                "acquirer_id": str(inst.acquirer_id) if inst.acquirer_id else None,
                "acquirer_name": acq_name,
                "gross_amount": float(inst.gross_amount),
                "fee_percentage": float(inst.fee_percentage),
                "fee_amount": float(inst.fee_amount),
                "net_amount": float(inst.net_amount),
                "expected_settlement_date": inst.expected_settlement_date.isoformat(),
                "status": inst.status,
                "nsu": inst.nsu,
                "authorization_code": inst.authorization_code,
                "settlement": {
                    "id": str(settlement.id),
                    "bank_account_id": str(settlement.bank_account_id),
                    "settlement_date": settlement.settlement_date.isoformat(),
                    "gross_amount": float(settlement.gross_amount),
                    "fee_deducted": float(settlement.fee_deducted),
                    "net_received_amount": float(settlement.net_received_amount),
                    "bank_transaction_ref": settlement.bank_transaction_ref
                } if settlement else None
            })

        return {
            "id": str(invoice.id),
            "customer_name": invoice.customer_name,
            "customer_tax_id": invoice.customer_tax_id,
            "channel": invoice.channel,
            "document_number": invoice.document_number,
            "description": invoice.description,
            "category_id": str(invoice.category_id) if invoice.category_id else None,
            "category_name": cat_name,
            "cost_center_id": str(invoice.cost_center_id) if invoice.cost_center_id else None,
            "cost_center_name": cc_name,
            "gross_amount": float(invoice.gross_amount),
            "deductions_amount": float(invoice.deductions_amount),
            "net_amount": float(invoice.net_amount),
            "issue_date": invoice.issue_date.isoformat(),
            "due_date": invoice.due_date.isoformat(),
            "status": invoice.status,
            "notes": invoice.notes,
            "installments": inst_list,
            "created_at": invoice.created_at.isoformat() if invoice.created_at else None
        }

    # --- Settle Receivable Installment / Baixa de Recebível ---
    @staticmethod
    async def settle_receivable_installment(
        session: AsyncSession,
        tenant_id: uuid.UUID,
        installment_id: uuid.UUID,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        inst_stmt = select(ReceivableInstallment).where(
            ReceivableInstallment.id == uuid.UUID(str(installment_id)),
            ReceivableInstallment.tenant_id == tenant_id
        )
        installment = (await session.execute(inst_stmt)).scalar_one_or_none()
        if not installment:
            raise ValueError("Lançamento de recebível não encontrado.")

        if installment.status == "RECEIVED":
            raise ValueError("Este lançamento já foi liquidado/recebido.")

        bank_account_id = uuid.UUID(str(data["bank_account_id"]))
        ba_stmt = select(BankAccount).where(
            BankAccount.id == bank_account_id,
            BankAccount.tenant_id == tenant_id
        )
        bank_account = (await session.execute(ba_stmt)).scalar_one_or_none()
        if not bank_account:
            raise ValueError("Conta bancária de destino não encontrada.")

        gross_amount = Decimal(str(data.get("gross_amount", installment.gross_amount)))
        fee_deducted = Decimal(str(data.get("fee_deducted", installment.fee_amount)))
        net_received_amount = Decimal(str(data.get("net_received_amount", gross_amount - fee_deducted)))

        settlement_date = data.get("settlement_date") or datetime.now(timezone.utc)
        if isinstance(settlement_date, str):
            settlement_date = datetime.fromisoformat(settlement_date)

        settlement = ReceivableSettlement(
            tenant_id=tenant_id,
            installment_id=installment.id,
            bank_account_id=bank_account.id,
            settlement_date=settlement_date,
            gross_amount=gross_amount,
            fee_deducted=fee_deducted,
            net_received_amount=net_received_amount,
            bank_transaction_ref=data.get("bank_transaction_ref"),
            notes=data.get("notes")
        )
        session.add(settlement)

        # Credit bank balance
        bank_account.current_balance += net_received_amount

        # Update installment status
        installment.status = "RECEIVED"
        installment.fee_amount = fee_deducted
        installment.net_amount = net_received_amount

        # Update parent invoice status
        inv_stmt = select(ReceivableInvoice).where(ReceivableInvoice.id == installment.invoice_id)
        invoice = (await session.execute(inv_stmt)).scalar_one()

        all_inst_stmt = select(ReceivableInstallment).where(ReceivableInstallment.invoice_id == invoice.id)
        all_installments = (await session.execute(all_inst_stmt)).scalars().all()

        received_count = sum(1 for inst in all_installments if inst.id != installment.id and inst.status == "RECEIVED") + 1
        if received_count >= len(all_installments):
            invoice.status = "RECEIVED"
        else:
            invoice.status = "PARTIALLY_RECEIVED"

        await session.flush()
        return {
            "settlement_id": str(settlement.id),
            "installment_id": str(installment.id),
            "invoice_id": str(invoice.id),
            "bank_account_id": str(bank_account.id),
            "bank_account_name": bank_account.name,
            "net_received_amount": float(net_received_amount),
            "fee_deducted": float(fee_deducted),
            "new_bank_balance": float(bank_account.current_balance),
            "invoice_status": invoice.status
        }

    # --- Cancel Receivable Invoice ---
    @staticmethod
    async def cancel_receivable_invoice(
        session: AsyncSession,
        tenant_id: uuid.UUID,
        invoice_id: uuid.UUID,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        stmt = select(ReceivableInvoice).where(
            ReceivableInvoice.id == uuid.UUID(str(invoice_id)),
            ReceivableInvoice.tenant_id == tenant_id
        )
        invoice = (await session.execute(stmt)).scalar_one_or_none()
        if not invoice:
            raise ValueError("Título a receber não encontrado.")

        if invoice.status == "RECEIVED":
            raise ValueError("Não é possível cancelar um título totalmente recebido.")

        invoice.status = "CANCELLED"
        if reason:
            invoice.notes = f"{invoice.notes or ''}\n[Cancelado]: {reason}".strip()

        inst_stmt = select(ReceivableInstallment).where(
            ReceivableInstallment.invoice_id == invoice.id,
            ReceivableInstallment.status != "RECEIVED"
        )
        pending_installments = (await session.execute(inst_stmt)).scalars().all()
        for inst in pending_installments:
            inst.status = "CANCELLED"

        await session.flush()
        return {"invoice_id": str(invoice.id), "status": "CANCELLED"}

    # --- Receivables Dashboard Metrics ---
    @staticmethod
    async def get_receivables_dashboard(session: AsyncSession, tenant_id: uuid.UUID) -> Dict[str, Any]:
        await FinancialService.seed_defaults_if_empty(session, tenant_id)
        now = datetime.now(timezone.utc)
        today_start = datetime(now.year, now.month, now.day, 0, 0, 0, tzinfo=timezone.utc)
        today_end = today_start + timedelta(days=1)
        next_7_days_end = today_start + timedelta(days=7)
        month_start = datetime(now.year, now.month, 1, 0, 0, 0, tzinfo=timezone.utc)

        # 1. Due / Expected today
        today_stmt = select(ReceivableInstallment).where(
            ReceivableInstallment.tenant_id == tenant_id,
            ReceivableInstallment.status.in_(["PENDING", "OVERDUE"]),
            ReceivableInstallment.expected_settlement_date >= today_start,
            ReceivableInstallment.expected_settlement_date < today_end
        )
        today_rows = (await session.execute(today_stmt)).scalars().all()
        total_expected_today = sum((r.net_amount for r in today_rows), Decimal("0"))

        # 2. Overdue
        overdue_stmt = select(ReceivableInstallment).where(
            ReceivableInstallment.tenant_id == tenant_id,
            ReceivableInstallment.status == "PENDING",
            ReceivableInstallment.expected_settlement_date < today_start
        )
        overdue_rows = (await session.execute(overdue_stmt)).scalars().all()
        total_overdue = sum((r.net_amount for r in overdue_rows), Decimal("0"))

        # 3. Next 7 days
        next_7_stmt = select(ReceivableInstallment).where(
            ReceivableInstallment.tenant_id == tenant_id,
            ReceivableInstallment.status.in_(["PENDING", "OVERDUE"]),
            ReceivableInstallment.expected_settlement_date >= today_start,
            ReceivableInstallment.expected_settlement_date <= next_7_days_end
        )
        next_7_rows = (await session.execute(next_7_stmt)).scalars().all()
        total_next_7_days = sum((r.net_amount for r in next_7_rows), Decimal("0"))

        # 4. Received this month
        settled_month_stmt = select(ReceivableSettlement).where(
            ReceivableSettlement.tenant_id == tenant_id,
            ReceivableSettlement.settlement_date >= month_start
        )
        settled_month_rows = (await session.execute(settled_month_stmt)).scalars().all()
        total_received_month = sum((r.net_received_amount for r in settled_month_rows), Decimal("0"))
        total_fees_deducted_month = sum((r.fee_deducted for r in settled_month_rows), Decimal("0"))

        # 5. Bank Accounts total balance
        ba_stmt = select(BankAccount).where(
            BankAccount.tenant_id == tenant_id,
            BankAccount.is_active == True
        )
        bank_accounts = (await session.execute(ba_stmt)).scalars().all()
        total_bank_balance = sum((acc.current_balance for acc in bank_accounts), Decimal("0"))

        # 6. Upcoming transfers list
        upcoming_stmt = select(ReceivableInstallment).where(
            ReceivableInstallment.tenant_id == tenant_id,
            ReceivableInstallment.status.in_(["PENDING", "OVERDUE"])
        ).order_by(ReceivableInstallment.expected_settlement_date.asc()).limit(10)
        upcoming_rows = (await session.execute(upcoming_stmt)).scalars().all()

        upcoming_list = []
        for inst in upcoming_rows:
            inv_stmt = select(ReceivableInvoice).where(ReceivableInvoice.id == inst.invoice_id)
            inv = (await session.execute(inv_stmt)).scalar_one_or_none()

            acq_name = None
            if inst.acquirer_id:
                acq_stmt = select(PaymentAcquirer.name).where(PaymentAcquirer.id == inst.acquirer_id)
                acq_name = (await session.execute(acq_stmt)).scalar_one_or_none()

            upcoming_list.append({
                "installment_id": str(inst.id),
                "invoice_id": str(inv.id) if inv else "",
                "customer_name": inv.customer_name if inv else "Cliente",
                "channel": inv.channel if inv else "POS",
                "payment_method": inst.payment_method,
                "card_brand": inst.card_brand,
                "acquirer_name": acq_name or "Direto / Balcão",
                "gross_amount": float(inst.gross_amount),
                "fee_amount": float(inst.fee_amount),
                "net_amount": float(inst.net_amount),
                "expected_settlement_date": inst.expected_settlement_date.isoformat(),
                "status": "OVERDUE" if inst.expected_settlement_date < now else inst.status
            })

        return {
            "total_expected_today": float(total_expected_today),
            "total_overdue": float(total_overdue),
            "total_next_7_days": float(total_next_7_days),
            "total_received_month": float(total_received_month),
            "total_fees_deducted_month": float(total_fees_deducted_month),
            "total_bank_balance": float(total_bank_balance),
            "count_overdue": len(overdue_rows),
            "count_expected_today": len(today_rows),
            "upcoming_transfers": upcoming_list
        }

    # =========================================================================
    # CASH FLOW PROJECTION (FLUXO DE CAIXA PREVISTO VS REALIZADO)
    # =========================================================================

    @staticmethod
    async def get_cash_flow_projection(
        session: AsyncSession,
        tenant_id: uuid.UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        await FinancialService.seed_defaults_if_empty(session, tenant_id)
        now = datetime.now(timezone.utc)

        if not start_date:
            start_date = datetime(now.year, now.month, 1, 0, 0, 0, tzinfo=timezone.utc)
        if not end_date:
            # Default to 30 days ahead from start_date
            start_d = datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0, tzinfo=timezone.utc)
            end_date = start_d + timedelta(days=30, hours=23, minutes=59, seconds=59)

        # 1. Opening balance of all active bank accounts
        ba_stmt = select(BankAccount).where(
            BankAccount.tenant_id == tenant_id,
            BankAccount.is_active == True
        )
        bank_accounts = (await session.execute(ba_stmt)).scalars().all()
        current_total_balance = sum((acc.current_balance for acc in bank_accounts), Decimal("0"))

        # 2. Fetch all Payable Installments & Settlements in range
        pay_inst_stmt = select(PayableInstallment).where(
            PayableInstallment.tenant_id == tenant_id,
            PayableInstallment.status.in_(["PENDING", "SCHEDULED", "OVERDUE"]),
            PayableInstallment.due_date >= start_date,
            PayableInstallment.due_date <= end_date
        )
        pay_installments = (await session.execute(pay_inst_stmt)).scalars().all()

        pay_settle_stmt = select(PayableSettlement).where(
            PayableSettlement.tenant_id == tenant_id,
            PayableSettlement.settlement_date >= start_date,
            PayableSettlement.settlement_date <= end_date
        )
        pay_settlements = (await session.execute(pay_settle_stmt)).scalars().all()

        # 3. Fetch all Receivable Installments & Settlements in range
        rec_inst_stmt = select(ReceivableInstallment).where(
            ReceivableInstallment.tenant_id == tenant_id,
            ReceivableInstallment.status.in_(["PENDING", "OVERDUE"]),
            ReceivableInstallment.expected_settlement_date >= start_date,
            ReceivableInstallment.expected_settlement_date <= end_date
        )
        rec_installments = (await session.execute(rec_inst_stmt)).scalars().all()

        rec_settle_stmt = select(ReceivableSettlement).where(
            ReceivableSettlement.tenant_id == tenant_id,
            ReceivableSettlement.settlement_date >= start_date,
            ReceivableSettlement.settlement_date <= end_date
        )
        rec_settlements = (await session.execute(rec_settle_stmt)).scalars().all()

        # 4. Group by Day
        curr_day = datetime(start_date.year, start_date.month, start_date.day, tzinfo=timezone.utc)
        end_d = datetime(end_date.year, end_date.month, end_date.day, tzinfo=timezone.utc)

        days_list = []
        running_balance = current_total_balance
        lowest_balance = current_total_balance
        total_inflows_period = Decimal("0")
        total_outflows_period = Decimal("0")

        while curr_day <= end_d:
            day_str = curr_day.strftime("%Y-%m-%d")
            next_day = curr_day + timedelta(days=1)

            # Inflows expected on this day
            inflows_expected = sum(
                (r.net_amount for r in rec_installments if curr_day <= r.expected_settlement_date < next_day),
                Decimal("0")
            )
            # Inflows realized on this day
            inflows_realized = sum(
                (r.net_received_amount for r in rec_settlements if curr_day <= r.settlement_date < next_day),
                Decimal("0")
            )
            total_inflows_day = inflows_realized if inflows_realized > 0 else inflows_expected

            # Outflows expected on this day
            outflows_expected = sum(
                (p.amount for p in pay_installments if curr_day <= p.due_date < next_day),
                Decimal("0")
            )
            # Outflows realized on this day
            outflows_realized = sum(
                (p.total_paid for p in pay_settlements if curr_day <= p.settlement_date < next_day),
                Decimal("0")
            )
            total_outflows_day = outflows_realized if outflows_realized > 0 else outflows_expected

            net_day = total_inflows_day - total_outflows_day
            running_balance += net_day
            if running_balance < lowest_balance:
                lowest_balance = running_balance

            total_inflows_period += total_inflows_day
            total_outflows_period += total_outflows_day

            days_list.append({
                "date": day_str,
                "inflows_expected": float(inflows_expected),
                "inflows_realized": float(inflows_realized),
                "total_inflows": float(total_inflows_day),
                "outflows_expected": float(outflows_expected),
                "outflows_realized": float(outflows_realized),
                "total_outflows": float(total_outflows_day),
                "net_day": float(net_day),
                "accumulated_balance": float(running_balance),
                "is_negative": running_balance < 0
            })

            curr_day += timedelta(days=1)

        return {
            "initial_balance": float(current_total_balance),
            "final_projected_balance": float(running_balance),
            "lowest_projected_balance": float(lowest_balance),
            "total_inflows_period": float(total_inflows_period),
            "total_outflows_period": float(total_outflows_period),
            "net_period": float(total_inflows_period - total_outflows_period),
            "days": days_list
        }

    # =========================================================================
    # FINANCIAL DRE (DEMONSTRAÇÃO DO RESULTADO DO EXERCÍCIO)
    # =========================================================================

    @staticmethod
    async def get_financial_dre(
        session: AsyncSession,
        tenant_id: uuid.UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        view_type: str = "COMPETENCE" # "COMPETENCE" (por emissão/competência) ou "CASH" (por liquidação/caixa)
    ) -> Dict[str, Any]:
        await FinancialService.seed_defaults_if_empty(session, tenant_id)
        now = datetime.now(timezone.utc)

        if not start_date:
            start_date = datetime(now.year, now.month, 1, 0, 0, 0, tzinfo=timezone.utc)
        if not end_date:
            # End of current month
            import calendar
            _, last_day = calendar.monthrange(start_date.year, start_date.month)
            end_date = datetime(start_date.year, start_date.month, last_day, 23, 59, 59, tzinfo=timezone.utc)

        # 1. Categories Mapping
        cats_stmt = select(FinancialCategory).where(FinancialCategory.tenant_id == tenant_id)
        categories = (await session.execute(cats_stmt)).scalars().all()
        cat_map = {c.id: c for c in categories}

        # 2. Revenue & Deductions
        if view_type == "CASH":
            rec_stmt = select(ReceivableSettlement).where(
                ReceivableSettlement.tenant_id == tenant_id,
                ReceivableSettlement.settlement_date >= start_date,
                ReceivableSettlement.settlement_date <= end_date
            )
            settlements = (await session.execute(rec_stmt)).scalars().all()
            gross_revenue = sum((s.gross_amount for s in settlements), Decimal("0"))
            deductions = sum((s.fee_deducted for s in settlements), Decimal("0"))
            net_revenue = gross_revenue - deductions
        else:
            inv_stmt = select(ReceivableInvoice).where(
                ReceivableInvoice.tenant_id == tenant_id,
                ReceivableInvoice.status != "CANCELLED",
                ReceivableInvoice.issue_date >= start_date,
                ReceivableInvoice.issue_date <= end_date
            )
            invoices = (await session.execute(inv_stmt)).scalars().all()
            gross_revenue = sum((inv.gross_amount for inv in invoices), Decimal("0"))
            deductions = sum((inv.deductions_amount for inv in invoices), Decimal("0"))
            net_revenue = gross_revenue - deductions

        # Avoid divide by zero
        ref_revenue = net_revenue if net_revenue > 0 else (gross_revenue if gross_revenue > 0 else Decimal("1"))

        # 3. Expenses Aggregation by Category Type
        cmv_total = Decimal("0")
        personnel_total = Decimal("0")
        operational_total = Decimal("0")
        admin_total = Decimal("0")
        marketing_total = Decimal("0")
        tax_total = Decimal("0")
        financial_total = Decimal("0")

        category_breakdown: Dict[str, Dict[str, Any]] = {}

        if view_type == "CASH":
            pay_stmt = select(PayableSettlement).where(
                PayableSettlement.tenant_id == tenant_id,
                PayableSettlement.settlement_date >= start_date,
                PayableSettlement.settlement_date <= end_date
            )
            pay_settlements = (await session.execute(pay_stmt)).scalars().all()
            for ps in pay_settlements:
                inst_stmt = select(PayableInstallment).where(PayableInstallment.id == ps.installment_id)
                inst = (await session.execute(inst_stmt)).scalar_one_or_none()
                if not inst:
                    continue
                bill_stmt = select(PayableBill).where(PayableBill.id == inst.payable_bill_id)
                bill = (await session.execute(bill_stmt)).scalar_one_or_none()
                if not bill:
                    continue

                cat = cat_map.get(bill.category_id) if bill.category_id else None
                cat_type = cat.type if cat else "EXPENSE_OPERATIONAL"
                cat_name = cat.name if cat else "Outras Despesas"

                amount = ps.total_paid
                if cat_type == "EXPENSE_CMV": cmv_total += amount
                elif cat_type == "EXPENSE_PERSONNEL": personnel_total += amount
                elif cat_type == "EXPENSE_ADMIN": admin_total += amount
                elif cat_type == "EXPENSE_TAX": tax_total += amount
                elif cat_type == "EXPENSE_FINANCIAL": financial_total += amount
                else: operational_total += amount

                if cat_name not in category_breakdown:
                    category_breakdown[cat_name] = {"name": cat_name, "type": cat_type, "amount": Decimal("0")}
                category_breakdown[cat_name]["amount"] += amount
        else:
            bill_stmt = select(PayableBill).where(
                PayableBill.tenant_id == tenant_id,
                PayableBill.status != "CANCELLED",
                PayableBill.issue_date >= start_date,
                PayableBill.issue_date <= end_date
            )
            bills = (await session.execute(bill_stmt)).scalars().all()
            for bill in bills:
                cat = cat_map.get(bill.category_id) if bill.category_id else None
                cat_type = cat.type if cat else "EXPENSE_OPERATIONAL"
                cat_name = cat.name if cat else "Outras Despesas"

                amount = bill.total_amount
                if cat_type == "EXPENSE_CMV": cmv_total += amount
                elif cat_type == "EXPENSE_PERSONNEL": personnel_total += amount
                elif cat_type == "EXPENSE_ADMIN": admin_total += amount
                elif cat_type == "EXPENSE_TAX": tax_total += amount
                elif cat_type == "EXPENSE_FINANCIAL": financial_total += amount
                else: operational_total += amount

                if cat_name not in category_breakdown:
                    category_breakdown[cat_name] = {"name": cat_name, "type": cat_type, "amount": Decimal("0")}
                category_breakdown[cat_name]["amount"] += amount

        # 4. Computed DRE Figures
        gross_profit = net_revenue - cmv_total
        gross_margin_pct = (gross_profit / ref_revenue * Decimal("100")).quantize(Decimal("0.01"))

        prime_cost = cmv_total + personnel_total
        prime_cost_pct = (prime_cost / ref_revenue * Decimal("100")).quantize(Decimal("0.01"))

        total_opex = personnel_total + operational_total + admin_total + marketing_total
        ebitda = gross_profit - (operational_total + admin_total + marketing_total + personnel_total)
        ebitda_margin_pct = (ebitda / ref_revenue * Decimal("100")).quantize(Decimal("0.01"))

        net_profit = ebitda - (tax_total + financial_total)
        net_margin_pct = (net_profit / ref_revenue * Decimal("100")).quantize(Decimal("0.01"))

        def get_av(val: Decimal) -> float:
            return float((val / ref_revenue * Decimal("100")).quantize(Decimal("0.01")))

        lines = [
            {"code": "1", "name": "(+) Receita Bruta de Vendas", "amount": float(gross_revenue), "av_pct": get_av(gross_revenue), "is_header": True, "level": 1},
            {"code": "2", "name": "(-) Deduções & Taxas MDR / Comissões Delivery", "amount": -float(deductions), "av_pct": -get_av(deductions), "is_header": False, "level": 2},
            {"code": "3", "name": "(=) Receita Líquida Operacional", "amount": float(net_revenue), "av_pct": 100.0, "is_header": True, "level": 1, "highlight": "cyan"},
            {"code": "4", "name": "(-) Custo da Mercadoria Vendida (CMV / Insumos)", "amount": -float(cmv_total), "av_pct": -get_av(cmv_total), "is_header": False, "level": 2},
            {"code": "5", "name": "(=) Lucro Bruto Operacional", "amount": float(gross_profit), "av_pct": float(gross_margin_pct), "is_header": True, "level": 1, "highlight": "emerald"},
            {"code": "6", "name": "(-) Despesas com Pessoal & Folha (Mão de Obra)", "amount": -float(personnel_total), "av_pct": -get_av(personnel_total), "is_header": False, "level": 2},
            {"code": "7", "name": "(-) Despesas Operacionais (Ocupação / Gás / Energia)", "amount": -float(operational_total), "av_pct": -get_av(operational_total), "is_header": False, "level": 2},
            {"code": "8", "name": "(-) Despesas Administrativas & Outras", "amount": -float(admin_total), "av_pct": -get_av(admin_total), "is_header": False, "level": 2},
            {"code": "9", "name": "(=) EBITDA Operacional (Geração de Caixa)", "amount": float(ebitda), "av_pct": float(ebitda_margin_pct), "is_header": True, "level": 1, "highlight": "violet"},
            {"code": "10", "name": "(-) Impostos & Tributos", "amount": -float(tax_total), "av_pct": -get_av(tax_total), "is_header": False, "level": 2},
            {"code": "11", "name": "(-) Despesas Financeiras & Juros", "amount": -float(financial_total), "av_pct": -get_av(financial_total), "is_header": False, "level": 2},
            {"code": "12", "name": "(=) Resultado Líquido do Período", "amount": float(net_profit), "av_pct": float(net_margin_pct), "is_header": True, "level": 1, "highlight": "emerald" if net_profit >= 0 else "crimson"},
        ]

        breakdown_list = [
            {"name": item["name"], "type": item["type"], "amount": float(item["amount"]), "av_pct": get_av(item["amount"])}
            for item in sorted(category_breakdown.values(), key=lambda x: x["amount"], reverse=True)
        ]

        return {
            "period": {"start_date": start_date.strftime("%Y-%m-%d"), "end_date": end_date.strftime("%Y-%m-%d")},
            "view_type": view_type,
            "kpis": {
                "gross_revenue": float(gross_revenue),
                "net_revenue": float(net_revenue),
                "cmv_amount": float(cmv_total),
                "cmv_pct": get_av(cmv_total),
                "prime_cost_amount": float(prime_cost),
                "prime_cost_pct": float(prime_cost_pct),
                "ebitda_amount": float(ebitda),
                "ebitda_margin_pct": float(ebitda_margin_pct),
                "net_profit": float(net_profit),
                "net_margin_pct": float(net_margin_pct)
            },
            "lines": lines,
            "category_breakdown": breakdown_list
        }

    # =========================================================================
    # BANK STATEMENT (EXTRATOS BANCÁRIOS & CONCILIAÇÃO OFX)
    # =========================================================================

    @staticmethod
    async def import_bank_statement_ofx(
        session: AsyncSession,
        tenant_id: uuid.UUID,
        bank_account_id: uuid.UUID,
        ofx_content: str
    ) -> Dict[str, Any]:
        ba_stmt = select(BankAccount).where(
            BankAccount.id == uuid.UUID(str(bank_account_id)),
            BankAccount.tenant_id == tenant_id
        )
        bank_account = (await session.execute(ba_stmt)).scalar_one_or_none()
        if not bank_account:
            raise ValueError("Conta bancária de destino não encontrada.")

        import re
        # Basic OFX tag parser for STMTTRN
        transactions = []
        pattern = re.compile(r'<STMTTRN>(.*?)</STMTTRN>', re.DOTALL | re.IGNORECASE)
        blocks = pattern.findall(ofx_content)

        imported_count = 0
        skipped_count = 0

        for block in blocks:
            # Extract fields
            type_m = re.search(r'<TRNTYPE>(.*?)(\r|\n|<)', block, re.IGNORECASE)
            date_m = re.search(r'<DTPOSTED>(.*?)(\r|\n|<)', block, re.IGNORECASE)
            amt_m = re.search(r'<TRNAMT>(.*?)(\r|\n|<)', block, re.IGNORECASE)
            fitid_m = re.search(r'<FITID>(.*?)(\r|\n|<)', block, re.IGNORECASE)
            memo_m = re.search(r'<(?:MEMO|NAME)>(.*?)(\r|\n|<)', block, re.IGNORECASE)

            if not amt_m:
                continue

            amount_str = amt_m.group(1).strip().replace(',', '.')
            amount = Decimal(amount_str)
            tx_type = "CREDIT" if amount >= 0 else "DEBIT"

            fitid = fitid_m.group(1).strip() if fitid_m else None
            description = memo_m.group(1).strip() if memo_m else "Transação Bancária"

            # Parse date YYYYMMDD or YYYYMMDDHHMMSS
            tx_date = datetime.now(timezone.utc)
            if date_m:
                d_raw = date_m.group(1).strip()[:8]
                try:
                    tx_date = datetime.strptime(d_raw, "%Y%m%d").replace(tzinfo=timezone.utc)
                except Exception:
                    pass

            # Check if already imported
            if fitid:
                chk_stmt = select(BankStatementTransaction).where(
                    BankStatementTransaction.tenant_id == tenant_id,
                    BankStatementTransaction.bank_account_id == bank_account.id,
                    BankStatementTransaction.fitid == fitid
                )
                existing = (await session.execute(chk_stmt)).scalar_one_or_none()
                if existing:
                    skipped_count += 1
                    continue

            stmt_tx = BankStatementTransaction(
                tenant_id=tenant_id,
                bank_account_id=bank_account.id,
                transaction_date=tx_date,
                amount=amount,
                transaction_type=tx_type,
                description=description,
                fitid=fitid,
                is_reconciled=False
            )
            session.add(stmt_tx)
            imported_count += 1

        await session.flush()
        return {
            "bank_account_id": str(bank_account.id),
            "bank_account_name": bank_account.name,
            "imported_count": imported_count,
            "skipped_count": skipped_count
        }

    @staticmethod
    async def list_bank_statement_transactions(
        session: AsyncSession,
        tenant_id: uuid.UUID,
        bank_account_id: Optional[uuid.UUID] = None,
        is_reconciled: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        query = select(BankStatementTransaction).where(BankStatementTransaction.tenant_id == tenant_id)
        if bank_account_id:
            query = query.where(BankStatementTransaction.bank_account_id == uuid.UUID(str(bank_account_id)))
        if is_reconciled is not None:
            query = query.where(BankStatementTransaction.is_reconciled == is_reconciled)

        query = query.order_by(BankStatementTransaction.transaction_date.desc(), BankStatementTransaction.created_at.desc())
        result = await session.execute(query)
        rows = result.scalars().all()

        output = []
        for r in rows:
            output.append({
                "id": str(r.id),
                "bank_account_id": str(r.bank_account_id),
                "transaction_date": r.transaction_date.isoformat(),
                "amount": float(r.amount),
                "transaction_type": r.transaction_type,
                "description": r.description,
                "fitid": r.fitid,
                "is_reconciled": r.is_reconciled,
                "reconciled_at": r.reconciled_at.isoformat() if r.reconciled_at else None,
                "settlement_type": r.settlement_type,
                "settlement_id": str(r.settlement_id) if r.settlement_id else None,
                "notes": r.notes
            })
        return output

    @staticmethod
    async def reconcile_bank_transaction(
        session: AsyncSession,
        tenant_id: uuid.UUID,
        statement_tx_id: uuid.UUID,
        settlement_type: str,
        settlement_id: Optional[uuid.UUID] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        stmt = select(BankStatementTransaction).where(
            BankStatementTransaction.id == uuid.UUID(str(statement_tx_id)),
            BankStatementTransaction.tenant_id == tenant_id
        )
        tx = (await session.execute(stmt)).scalar_one_or_none()
        if not tx:
            raise ValueError("Lançamento do extrato bancário não encontrado.")

        tx.is_reconciled = True
        tx.reconciled_at = datetime.now(timezone.utc)
        tx.settlement_type = settlement_type
        tx.settlement_id = uuid.UUID(str(settlement_id)) if settlement_id else None
        if notes:
            tx.notes = notes

        await session.flush()
        return {
            "statement_tx_id": str(tx.id),
            "is_reconciled": True,
            "settlement_type": tx.settlement_type,
            "settlement_id": str(tx.settlement_id) if tx.settlement_id else None
        }


