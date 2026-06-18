import apiClient from './client'
import type { Transaction, PaginatedResponse, TransactionFilters } from '../types'

export async function fetchTransactions(filters: TransactionFilters = {}): Promise<PaginatedResponse<Transaction>> {
  const params = new URLSearchParams()
  Object.entries(filters).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') {
      if (Array.isArray(v)) {
        v.forEach((item) => params.append(k, String(item)))
      } else {
        params.append(k, String(v))
      }
    }
  })
  const { data } = await apiClient.get<PaginatedResponse<Transaction>>(`/transactions/?${params}`)
  return data
}

export async function fetchTransaction(id: number): Promise<Transaction> {
  const { data } = await apiClient.get<Transaction>(`/transactions/${id}/`)
  return data
}

export async function updateTransaction(id: number, payload: Partial<Pick<Transaction, 'description' | 'category_name' | 'category'>>): Promise<Transaction> {
  const { data } = await apiClient.patch<Transaction>(`/transactions/${id}/`, payload)
  return data
}

export async function fetchSplits(transactionId: number) {
  const { data } = await apiClient.get(`/transactions/${transactionId}/splits/`)
  return data
}

export async function createSplit(transactionId: number, payload: { person_name: string; amount: string; note?: string }) {
  const { data } = await apiClient.post(`/transactions/${transactionId}/splits/`, payload)
  return data
}

export async function updateSplit(transactionId: number, splitId: number, payload: Partial<{ paid_back: boolean; amount: string; note: string }>) {
  const { data } = await apiClient.patch(`/transactions/${transactionId}/splits/${splitId}/`, payload)
  return data
}

export async function deleteSplit(transactionId: number, splitId: number) {
  await apiClient.delete(`/transactions/${transactionId}/splits/${splitId}/`)
}
