export interface DocumentExtractionItem {
  id: string
  invoice_number: string
  issue_date: string | null
  total_amount: number
  status: string
  supplier_name: string | null
  created_at: string
}

export interface DocumentExtractionLineItem {
  id: string
  raw_description: string | null
  raw_code: string | null
  raw_quantity: number
  raw_uom: string | null
  raw_unit_price: number
  match_status: string
}

export interface DocumentExtractionDetail {
  id: string
  invoice_number: string
  issue_date: string | null
  total_amount: number
  status: string
  created_at: string
  supplier_name: string | null
  lines: DocumentExtractionLineItem[]
}

export interface UploadNFEResponse {
  id: string
  invoice_number: string
  status: string
  total_amount: number
}

export interface ApproveResponse {
  success: boolean
  invoice_id: string
}

export interface FetchExtractionsResponse {
  data: DocumentExtractionItem[]
  error?: string
}

export interface FetchExtractionDetailResponse {
  data: DocumentExtractionDetail
  error?: string
}