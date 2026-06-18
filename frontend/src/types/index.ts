export interface Transaction {
  id: number
  date: string
  amount: string
  net_amount: string
  merchant: string | null
  type: 'debito' | 'credito' | 'transferencia' | 'ingreso' | 'desconocido'
  description: string | null
  category_name: string | null
  category: number | null
  split_count: number
  splits?: ExpenseSplit[]
  created_at: string
  updated_at: string
}

export interface Category {
  id: number
  name: string
  label: string
  is_default: boolean
  owner: number | null
}

export interface Person {
  id: number
  name: string
  archived: boolean
}

export interface ExpenseSplit {
  id: number
  person: number | null
  person_name_snapshot: string
  amount: string
  paid_back: boolean
  paid_back_at: string | null
  note: string
}

export interface DashboardData {
  period: { start: string | null; end: string | null }
  monthly_totals: { year: number; month: number; total: string; net_total: string }[]
  by_category: { category_name: string; total: string; net_total: string }[]
}

export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export interface UserMe {
  id: number
  username: string
  email: string | null
  telegram_chat_id: string | null
  telegram_link_token: string | null
  telegram_linked: boolean
  telegram_bot_username: string
  created_at: string
}

export interface TransactionFilters {
  start?: string
  end?: string
  year?: number
  month?: number
  type?: string[]
  category?: string
  search?: string
  ordering?: string
  page?: number
  page_size?: number
}
