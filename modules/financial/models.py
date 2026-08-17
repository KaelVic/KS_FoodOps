import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric, Boolean, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from packages.tenant.database import Base

class FinancialCategory(Base):
    __tablename__ = "financial_categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(50), nullable=True) # e.g. "1.01", "2.03"
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False, default="EXPENSE_OPERATIONAL") 
    # Types: EXPENSE_CMV, EXPENSE_OPERATIONAL, EXPENSE_ADMIN, EXPENSE_PERSONNEL, EXPENSE_TAX, EXPENSE_FINANCIAL, INCOME_SALES, INCOME_OTHER
    parent_id = Column(UUID(as_uuid=True), ForeignKey("financial_categories.id", ondelete="SET NULL"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class CostCenter(Base):
    __tablename__ = "cost_centers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(50), nullable=True) # e.g. "CC-COZ", "CC-SAL"
    name = Column(String(255), nullable=False)
    description = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class BankAccount(Base):
    __tablename__ = "bank_accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False) # e.g. "Banco Itaú - Conta Principal", "Caixa Gaveta Salão"
    account_type = Column(String(50), nullable=False, default="CHECKING") # CHECKING, SAVINGS, CASH, DIGITAL_WALLET
    bank_code = Column(String(20), nullable=True)
    agency_number = Column(String(50), nullable=True)
    account_number = Column(String(50), nullable=True)
    pix_key = Column(String(255), nullable=True)
    initial_balance = Column(Numeric(precision=24, scale=12), nullable=False, default=0)
    current_balance = Column(Numeric(precision=24, scale=12), nullable=False, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class PaymentMethod(Base):
    __tablename__ = "payment_methods"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False) # e.g. "PIX", "Boleto", "Cartão Corporativo", "TED", "Dinheiro"
    type = Column(String(50), nullable=False, default="PIX") # PIX, BOLETO, CREDIT_CARD, DEBIT_CARD, TRANSFER, CASH
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class PayableBill(Base):
    __tablename__ = "payable_bills"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=False, index=True)
    category_id = Column(UUID(as_uuid=True), ForeignKey("financial_categories.id", ondelete="RESTRICT"), nullable=True, index=True)
    cost_center_id = Column(UUID(as_uuid=True), ForeignKey("cost_centers.id", ondelete="RESTRICT"), nullable=True, index=True)
    purchase_order_id = Column(UUID(as_uuid=True), ForeignKey("purchase_orders.id", ondelete="SET NULL"), nullable=True, index=True)
    supplier_invoice_id = Column(UUID(as_uuid=True), ForeignKey("supplier_invoices.id", ondelete="SET NULL"), nullable=True, index=True)
    document_number = Column(String(100), nullable=True) # e.g. "NF 1248" ou "REC-889"
    description = Column(String(255), nullable=False)
    total_amount = Column(Numeric(precision=24, scale=12), nullable=False)
    issue_date = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    first_due_date = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(50), nullable=False, default="PENDING") 
    # Status: PENDING, SCHEDULED, PARTIALLY_PAID, PAID, CANCELLED
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class PayableInstallment(Base):
    __tablename__ = "payable_installments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    payable_bill_id = Column(UUID(as_uuid=True), ForeignKey("payable_bills.id", ondelete="CASCADE"), nullable=False, index=True)
    installment_number = Column(Integer, nullable=False, default=1)
    total_installments = Column(Integer, nullable=False, default=1)
    due_date = Column(DateTime(timezone=True), nullable=False)
    amount = Column(Numeric(precision=24, scale=12), nullable=False)
    barcode = Column(String(255), nullable=True) # Linha digitável / código de barras
    pix_code = Column(Text, nullable=True) # Código PIX copia e cola
    status = Column(String(50), nullable=False, default="PENDING") # PENDING, SCHEDULED, PAID, OVERDUE, CANCELLED
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class PayableSettlement(Base):
    __tablename__ = "payable_settlements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    installment_id = Column(UUID(as_uuid=True), ForeignKey("payable_installments.id", ondelete="CASCADE"), nullable=False, index=True)
    bank_account_id = Column(UUID(as_uuid=True), ForeignKey("bank_accounts.id", ondelete="RESTRICT"), nullable=False, index=True)
    payment_method = Column(String(50), nullable=False, default="PIX")
    settlement_date = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    principal_amount = Column(Numeric(precision=24, scale=12), nullable=False) # Valor nominal da parcela
    interest_amount = Column(Numeric(precision=24, scale=12), nullable=False, default=0) # Juros
    fine_amount = Column(Numeric(precision=24, scale=12), nullable=False, default=0) # Multa
    discount_amount = Column(Numeric(precision=24, scale=12), nullable=False, default=0) # Desconto
    total_paid = Column(Numeric(precision=24, scale=12), nullable=False) # principal + juros + multa - desconto
    receipt_url = Column(String(500), nullable=True)
    transaction_reference = Column(String(255), nullable=True) # Autenticação bancária / comprovante
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# --- ACCOUNTS RECEIVABLE (CONTAS A RECEBER & CONCILIAÇÃO) ---

class PaymentAcquirer(Base):
    __tablename__ = "payment_acquirers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False) # e.g. "Cielo", "Stone", "Rede", "iFood Pagamentos", "VR Benefícios", "Alelo", "Sodexo"
    acquirer_type = Column(String(50), nullable=False, default="CREDIT_DEBIT") 
    # acquirer_type: CREDIT_DEBIT, MEAL_VOUCHER, DELIVERY_PLATFORM, PIX_GATEWAY, BANK_BOLETO
    debit_fee_percentage = Column(Numeric(precision=10, scale=4), nullable=False, default=1.50) # Ex: 1.50%
    credit_1x_fee_percentage = Column(Numeric(precision=10, scale=4), nullable=False, default=2.80) # Ex: 2.80%
    credit_inst_fee_percentage = Column(Numeric(precision=10, scale=4), nullable=False, default=3.80) # Ex: 3.80%
    voucher_fee_percentage = Column(Numeric(precision=10, scale=4), nullable=False, default=5.50) # Ex: 5.50%
    delivery_fee_percentage = Column(Numeric(precision=10, scale=4), nullable=False, default=23.00) # Ex: 23.00% iFood
    pix_fee_percentage = Column(Numeric(precision=10, scale=4), nullable=False, default=0.00) # Ex: 0.00% ou 0.99%
    fixed_fee = Column(Numeric(precision=24, scale=12), nullable=False, default=0.00) # Taxa fixa por transação
    settlement_days_debit = Column(Integer, nullable=False, default=1) # D+1
    settlement_days_credit = Column(Integer, nullable=False, default=30) # D+30
    settlement_days_voucher = Column(Integer, nullable=False, default=30) # D+30
    settlement_days_delivery = Column(Integer, nullable=False, default=7) # D+7 repasse semanal
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ReceivableInvoice(Base):
    __tablename__ = "receivable_invoices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_name = Column(String(255), nullable=False) # e.g. "Consumidor Final (PDV)", "Empresa ABC Ltda (Evento)", "iFood Marketplace"
    customer_tax_id = Column(String(50), nullable=True) # CPF ou CNPJ
    channel = Column(String(50), nullable=False, default="POS") 
    # channel: POS, DELIVERY_IFOOD, DELIVERY_OWN, CORPORATE_INVOICE, CATERING_EVENT
    category_id = Column(UUID(as_uuid=True), ForeignKey("financial_categories.id", ondelete="RESTRICT"), nullable=True, index=True)
    cost_center_id = Column(UUID(as_uuid=True), ForeignKey("cost_centers.id", ondelete="RESTRICT"), nullable=True, index=True)
    document_number = Column(String(100), nullable=True) # e.g. "FAT-001", "CUPOM-4992"
    description = Column(String(255), nullable=False)
    gross_amount = Column(Numeric(precision=24, scale=12), nullable=False) # Valor total faturado
    deductions_amount = Column(Numeric(precision=24, scale=12), nullable=False, default=0) # Taxas MDR e comissões retidas
    net_amount = Column(Numeric(precision=24, scale=12), nullable=False) # Valor líquido a receber
    issue_date = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    due_date = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(50), nullable=False, default="PENDING") 
    # status: PENDING, PARTIALLY_RECEIVED, RECEIVED, OVERDUE, CANCELLED
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ReceivableInstallment(Base):
    __tablename__ = "receivable_installments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("receivable_invoices.id", ondelete="CASCADE"), nullable=False, index=True)
    acquirer_id = Column(UUID(as_uuid=True), ForeignKey("payment_acquirers.id", ondelete="SET NULL"), nullable=True, index=True)
    installment_number = Column(Integer, nullable=False, default=1)
    total_installments = Column(Integer, nullable=False, default=1)
    payment_method = Column(String(50), nullable=False, default="CREDIT_CARD") 
    # payment_method: PIX, DEBIT_CARD, CREDIT_CARD, MEAL_VOUCHER, DELIVERY_ONLINE, CASH, BOLETO
    card_brand = Column(String(50), nullable=True) # VISA, MASTERCARD, ELO, AMEX, VR, SODEXO, ALELO, IFOOD_PAY
    gross_amount = Column(Numeric(precision=24, scale=12), nullable=False)
    fee_percentage = Column(Numeric(precision=10, scale=4), nullable=False, default=0)
    fee_amount = Column(Numeric(precision=24, scale=12), nullable=False, default=0) # Taxa MDR retida
    net_amount = Column(Numeric(precision=24, scale=12), nullable=False) # Líquido a repassar
    expected_settlement_date = Column(DateTime(timezone=True), nullable=False) # Previsão de repasse
    status = Column(String(50), nullable=False, default="PENDING") # PENDING, RECEIVED, OVERDUE, CANCELLED
    nsu = Column(String(100), nullable=True) # Número Sequencial Único da maquininha
    authorization_code = Column(String(100), nullable=True) # Código de autorização
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ReceivableSettlement(Base):
    __tablename__ = "receivable_settlements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    installment_id = Column(UUID(as_uuid=True), ForeignKey("receivable_installments.id", ondelete="CASCADE"), nullable=False, index=True)
    bank_account_id = Column(UUID(as_uuid=True), ForeignKey("bank_accounts.id", ondelete="RESTRICT"), nullable=False, index=True)
    settlement_date = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    gross_amount = Column(Numeric(precision=24, scale=12), nullable=False)
    fee_deducted = Column(Numeric(precision=24, scale=12), nullable=False, default=0)
    net_received_amount = Column(Numeric(precision=24, scale=12), nullable=False) # Valor que efetivamente entrou na conta
    bank_transaction_ref = Column(String(255), nullable=True) # ID no extrato bancário
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# --- BANK STATEMENT & RECONCILIATION (EXTRATOS BANCÁRIOS & OFX) ---

class BankStatementTransaction(Base):
    __tablename__ = "bank_statement_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    bank_account_id = Column(UUID(as_uuid=True), ForeignKey("bank_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    transaction_date = Column(DateTime(timezone=True), nullable=False)
    amount = Column(Numeric(precision=24, scale=12), nullable=False) # Positivo = Entrada / Negativo = Saída
    transaction_type = Column(String(20), nullable=False, default="CREDIT") # CREDIT, DEBIT
    description = Column(String(500), nullable=False)
    fitid = Column(String(255), nullable=True, index=True) # Unique Transaction ID from OFX
    check_number = Column(String(100), nullable=True)
    is_reconciled = Column(Boolean, nullable=False, default=False)
    reconciled_at = Column(DateTime(timezone=True), nullable=True)
    settlement_type = Column(String(50), nullable=True) # PAYABLE, RECEIVABLE, TRANSFER, MANUAL_EXPENSE, MANUAL_INCOME
    settlement_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class BankReconciliationRule(Base):
    __tablename__ = "bank_reconciliation_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    pattern = Column(String(255), nullable=False) # Ex: "IFOOD", "TARIFA BANC", "ENEL"
    category_id = Column(UUID(as_uuid=True), ForeignKey("financial_categories.id", ondelete="SET NULL"), nullable=True)
    cost_center_id = Column(UUID(as_uuid=True), ForeignKey("cost_centers.id", ondelete="SET NULL"), nullable=True)
    action_type = Column(String(50), nullable=False, default="AUTO_EXPENSE")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


