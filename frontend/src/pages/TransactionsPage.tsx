import { useState } from 'react'
import { useTransactions } from '../hooks/useTransactions'
import TransactionTable from '../components/TransactionTable'
import FilterBar from '../components/FilterBar'
import type { Filters } from '../components/FilterBar'
import PageLayout from '../components/PageLayout'
import EstimatesBanner from '../components/EstimatesBanner'
import Pagination from '../components/Pagination'

const PAGE_SIZE = 25

export default function TransactionsPage() {
  const now = new Date()
  const [filters, setFilters] = useState<Filters>({
    year: now.getFullYear(),
    month: now.getMonth() + 1,
  })
  const [page, setPage] = useState(1)

  // Cualquier cambio de filtro o búsqueda reinicia a la primera página,
  // así los resultados (que se buscan en todo el servidor) se ven desde el inicio.
  function handleFiltersChange(next: Filters) {
    setFilters(next)
    setPage(1)
  }

  const { data, isLoading } = useTransactions({
    ...filters,
    type: filters.type ? [filters.type] : undefined,
    ordering: '-date',
    page,
    page_size: PAGE_SIZE,
  })

  const totalPages = data ? Math.max(1, Math.ceil(data.count / PAGE_SIZE)) : 1

  return (
    <PageLayout maxWidth="wide">
      <h1 className="text-2xl font-bold text-surface-800 dark:text-surface-100 mb-4">Transacciones</h1>
      <div className="mb-6">
        <FilterBar filters={filters} onChange={handleFiltersChange} />
      </div>
      <EstimatesBanner show={!!data?.results.some((t) => t.fx_status === 'estimated')} />
      {isLoading && <p className="text-surface-500 dark:text-surface-400">Cargando...</p>}
      {data && data.results.length > 0 && (
        <>
          <TransactionTable transactions={data.results} total={data.count} />
          <Pagination page={page} totalPages={totalPages} onPageChange={setPage} />
        </>
      )}
      {data && data.results.length === 0 && (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <svg className="w-24 h-24 text-surface-300 dark:text-surface-600 mb-4" viewBox="0 0 100 100" fill="none">
            <rect x="25" y="10" width="50" height="70" rx="4" stroke="currentColor" strokeWidth="2" opacity="0.3" />
            <line x1="35" y1="30" x2="65" y2="30" stroke="currentColor" strokeWidth="2" opacity="0.2" />
            <line x1="35" y1="42" x2="65" y2="42" stroke="currentColor" strokeWidth="2" opacity="0.2" />
            <line x1="35" y1="54" x2="55" y2="54" stroke="currentColor" strokeWidth="2" opacity="0.2" />
          </svg>
          <p className="text-lg font-semibold text-surface-600 dark:text-surface-300 mb-1">No hay transacciones</p>
          <p className="text-sm text-surface-400 dark:text-surface-500">No se encontraron transacciones para los filtros seleccionados</p>
        </div>
      )}
    </PageLayout>
  )
}
