import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchTransactions, updateTransaction } from '../api/transactions'
import type { TransactionFilters } from '../types'

export function useTransactions(filters: TransactionFilters = {}) {
  return useQuery({
    queryKey: ['transactions', filters],
    queryFn: () => fetchTransactions(filters),
  })
}

export function useUpdateTransaction() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: Parameters<typeof updateTransaction>[1] }) =>
      updateTransaction(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['transactions'] })
    },
  })
}
