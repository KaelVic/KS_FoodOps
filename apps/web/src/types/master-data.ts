export interface UOM {
  id: string
  tenant_id: string
  name: string
  symbol: string
  base_type: string
}

export interface Category {
  id: string
  tenant_id: string
  name: string
  parent_id: string | null
}

export interface SKU {
  id: string
  tenant_id: string
  name: string
  category_id: string | null
  base_uom_id: string
  is_active: boolean
}

export interface Supplier {
  id: string
  tenant_id: string
  name: string
  tax_id: string | null
  is_active: boolean
}

export interface Location {
  id: string
  tenant_id: string
  name: string
  business_unit_id: string
}

export interface TeamMember {
  id: string
  tenant_id: string
  user_id: string
  role: string
}
