export interface FinancialCategory {
  id: string
  tenant_id: string
  code?: string | null
  name: string
  type: "EXPENSE_CMV" | "EXPENSE_OPERATIONAL" | "EXPENSE_ADMIN" | "EXPENSE_PERSONNEL" | "EXPENSE_TAX" | "EXPENSE_FINANCIAL" | "INCOME_SALES" | "INCOME_OTHER"
  parent_id?: string | null
  is_active: boolean
  created_at?: string
}

export interface CostCenter {
  id: string
  tenant_id: string
  code?: string | null
  name: string
  description?: string | null
  is_active: boolean
  created_at?: string
}

export interface BankAccount {
  id: string
  tenant_id: string
  name: string
  account_type: "CHECKING" | "SAVINGS" | "CASH" | "DIGITAL_WALLET"
  bank_code?: string | null
  agency_number?: string | null
  account_number?: string | null
  pix_key?: string | null
  initial_balance: number
  current_balance: number
  is_active: boolean
  created_at?: string
}

export interface PayableSettlement {
  id: string
  bank_account_id: string
  payment_method: string
  settlement_date: string
  principal_amount: number
  interest_amount: number
  fine_amount: number
  discount_amount: number
  total_paid: number
  receipt_url?: string | null
  transaction_reference?: string | null
  notes?: string | null
}

export interface PayableInstallment {
  id: string
  installment_number: number
  total_installments: number
  due_date: string
  amount: number
  barcode?: string | null
  pix_code?: string | null
  status: "PENDING" | "SCHEDULED" | "PAID" | "OVERDUE" | "CANCELLED"
  settlements?: PayableSettlement[]
}

export interface PayableBill {
  id: string
  supplier_id: string
  supplier_name: string
  category_id?: string | null
  category_name?: string | null
  cost_center_id?: string | null
  cost_center_name?: string | null
  document_number?: string | null
  description: string
  total_amount: number
  paid_amount: number
  remaining_amount: number
  issue_date: string
  first_due_date: string
  status: "PENDING" | "SCHEDULED" | "PARTIALLY_PAID" | "PAID" | "CANCELLED"
  notes?: string | null
  installments_count?: number
  installments: PayableInstallment[]
}

export interface PayablesDashboardMetrics {
  total_due_today: number
  total_overdue: number
  total_next_7_days: number
  total_due_month: number
  total_paid_month: number
  total_bank_balance: number
  count_overdue: number
  count_due_today: number
  upcoming_installments: {
    installment_id: string
    bill_id: string
    document_number?: string
    description: string
    supplier_name: string
    installment_number: number
    total_installments: number
    due_date: string
    amount: number
    barcode?: string | null
    pix_code?: string | null
    status: string
  }[]
}

export interface CreatePayableBillPayload {
  supplier_id: string
  category_id?: string | null
  cost_center_id?: string | null
  purchase_order_id?: string | null
  supplier_invoice_id?: string | null
  document_number?: string | null
  description: string
  total_amount: number
  issue_date?: string
  first_due_date?: string
  installment_count?: number
  barcode?: string | null
  pix_code?: string | null
  notes?: string | null
  installments?: {
    installment_number: number
    total_installments: number
    due_date: string
    amount: number
    barcode?: string | null
    pix_code?: string | null
  }[]
}

export interface SettleInstallmentPayload {
  bank_account_id: string
  payment_method: string
  settlement_date?: string
  interest_amount?: number
  fine_amount?: number
  discount_amount?: number
  receipt_url?: string | null
  transaction_reference?: string | null
  notes?: string | null
}

// --- ACCOUNTS RECEIVABLE (CONTAS A RECEBER) ---

export interface PaymentAcquirer {
  id: string
  tenant_id: string
  name: string
  acquirer_type: "CREDIT_DEBIT" | "MEAL_VOUCHER" | "DELIVERY_PLATFORM" | "PIX_GATEWAY" | "BANK_BOLETO"
  debit_fee_percentage: number
  credit_1x_fee_percentage: number
  credit_inst_fee_percentage: number
  voucher_fee_percentage: number
  delivery_fee_percentage: number
  pix_fee_percentage: number
  fixed_fee: number
  settlement_days_debit: number
  settlement_days_credit: number
  settlement_days_voucher: number
  settlement_days_delivery: number
  is_active: boolean
  created_at?: string
}

export interface ReceivableSettlement {
  id: string
  bank_account_id: string
  settlement_date: string
  gross_amount: number
  fee_deducted: number
  net_received_amount: number
  bank_transaction_ref?: string | null
  notes?: string | null
}

export interface ReceivableInstallment {
  id: string
  installment_number: number
  total_installments: number
  payment_method: "PIX" | "DEBIT_CARD" | "CREDIT_CARD" | "MEAL_VOUCHER" | "DELIVERY_ONLINE" | "CASH" | "BOLETO"
  card_brand?: string | null
  acquirer_id?: string | null
  acquirer_name?: string | null
  gross_amount: number
  fee_percentage: number
  fee_amount: number
  net_amount: number
  expected_settlement_date: string
  status: "PENDING" | "RECEIVED" | "OVERDUE" | "CANCELLED"
  nsu?: string | null
  authorization_code?: string | null
  settlement?: ReceivableSettlement | null
}

export interface ReceivableInvoice {
  id: string
  customer_name: string
  customer_tax_id?: string | null
  channel: "POS" | "DELIVERY_IFOOD" | "DELIVERY_OWN" | "CORPORATE_INVOICE" | "CATERING_EVENT"
  category_id?: string | null
  category_name?: string | null
  cost_center_id?: string | null
  cost_center_name?: string | null
  document_number?: string | null
  description: string
  gross_amount: number
  deductions_amount: number
  net_amount: number
  issue_date: string
  due_date: string
  status: "PENDING" | "PARTIALLY_RECEIVED" | "RECEIVED" | "OVERDUE" | "CANCELLED"
  notes?: string | null
  installments: ReceivableInstallment[]
  created_at?: string
}

export interface ReceivablesDashboardMetrics {
  total_expected_today: number
  total_overdue: number
  total_next_7_days: number
  total_received_month: number
  total_fees_deducted_month: number
  total_bank_balance: number
  count_overdue: number
  count_expected_today: number
  upcoming_transfers: {
    installment_id: string
    invoice_id: string
    customer_name: string
    channel: string
    payment_method: string
    card_brand?: string | null
    acquirer_name: string
    gross_amount: number
    fee_amount: number
    net_amount: number
    expected_settlement_date: string
    status: string
  }[]
}

export interface CreateReceivableInvoicePayload {
  customer_name: string
  customer_tax_id?: string | null
  channel?: "POS" | "DELIVERY_IFOOD" | "DELIVERY_OWN" | "CORPORATE_INVOICE" | "CATERING_EVENT"
  category_id?: string | null
  cost_center_id?: string | null
  acquirer_id?: string | null
  payment_method?: string
  card_brand?: string | null
  document_number?: string | null
  description: string
  gross_amount: number
  fee_percentage?: number | null
  issue_date?: string
  due_date?: string
  nsu?: string | null
  authorization_code?: string | null
  notes?: string | null
  installments?: {
    installment_number: number
    total_installments: number
    payment_method: string
    card_brand?: string | null
    gross_amount: number
    fee_percentage?: number | null
    expected_settlement_date?: string
    nsu?: string | null
    authorization_code?: string | null
  }[]
}

export interface SettleReceivableInstallmentPayload {
  bank_account_id: string
  settlement_date?: string
  gross_amount?: number
  fee_deducted?: number
  net_received_amount?: number
  bank_transaction_ref?: string | null
  notes?: string | null
}

export interface CreateAcquirerPayload {
  name: string
  acquirer_type?: string
  debit_fee_percentage?: number
  credit_1x_fee_percentage?: number
  credit_inst_fee_percentage?: number
  voucher_fee_percentage?: number
  delivery_fee_percentage?: number
  pix_fee_percentage?: number
  fixed_fee?: number
  settlement_days_debit?: number
  settlement_days_credit?: number
  settlement_days_voucher?: number
  settlement_days_delivery?: number
}

// --- Phase 3: Cash Flow & Financial DRE Types ---

export interface CashFlowDay {
  date: string
  inflows_expected: number
  inflows_realized: number
  total_inflows: number
  outflows_expected: number
  outflows_realized: number
  total_outflows: number
  net_day: number
  accumulated_balance: number
  is_negative: boolean
}

export interface CashFlowProjection {
  initial_balance: number
  final_projected_balance: number
  lowest_projected_balance: number
  total_inflows_period: number
  total_outflows_period: number
  net_period: number
  days: CashFlowDay[]
}

export interface DRELineItem {
  code: string
  name: string
  amount: number
  av_pct: number
  is_header: boolean
  level: number
  highlight?: "cyan" | "emerald" | "violet" | "crimson" | "amber"
}

export interface CategoryBreakdownItem {
  name: string
  type: string
  amount: number
  av_pct: number
}

export interface FinancialDREResponse {
  period: {
    start_date: string
    end_date: string
  }
  view_type: "COMPETENCE" | "CASH"
  kpis: {
    gross_revenue: number
    net_revenue: number
    cmv_amount: number
    cmv_pct: number
    prime_cost_amount: number
    prime_cost_pct: number
    ebitda_amount: number
    ebitda_margin_pct: number
    net_profit: number
    net_margin_pct: number
  }
  lines: DRELineItem[]
  category_breakdown: CategoryBreakdownItem[]
}

export interface BankStatementTransaction {
  id: string
  bank_account_id: string
  transaction_date: string
  amount: number
  transaction_type: "CREDIT" | "DEBIT"
  description: string
  fitid?: string | null
  is_reconciled: boolean
  reconciled_at?: string | null
  settlement_type?: string | null
  settlement_id?: string | null
  notes?: string | null
}

export interface UploadOFXPayload {
  bank_account_id: string
  ofx_content: string
}

export interface ReconcileBankTransactionPayload {
  settlement_type: string
  settlement_id?: string | null
  notes?: string | null
}


