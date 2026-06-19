import { useState, useEffect } from 'react'
import { useDashboard } from '../hooks/useDashboard'
import CategoryBarChart from '../components/MonthlyBarChart'
import CategoryDoughnut from '../components/CategoryDoughnut'
import CategoryLegend from '../components/CategoryLegend'
import FilterBar from '../components/FilterBar'
import type { Filters } from '../components/FilterBar'
import { categoryColor, formatCLP } from '../utils/categoryColors'
import { Card } from '../components/ui'
import PageLayout from '../components/PageLayout'
import EstimatesBanner from '../components/EstimatesBanner'

export default function DashboardPage() {
  const now = new Date()
  const [filters, setFilters] = useState<Filters>({
    year: now.getFullYear(),
    month: now.getMonth() + 1,
  })
  const [selectedCategories, setSelectedCategories] = useState<Set<string>>(new Set())

  const { data, isLoading } = useDashboard(filters)

  useEffect(() => {
    if (data) {
      setSelectedCategories(new Set(data.by_category.map((c) => c.category_name)))
    }
  }, [data])

  function toggleCategory(name: string) {
    setSelectedCategories((prev) => {
      const next = new Set(prev)
      if (next.has(name)) {
        next.delete(name)
      } else {
        next.add(name)
      }
      return next
    })
  }

  return (
    <PageLayout maxWidth="wide">
      <h1 className="text-2xl font-bold text-surface-800 dark:text-surface-100 mb-4">Dashboard</h1>
      <div className="mb-6">
        <FilterBar filters={filters} onChange={setFilters} />
      </div>

      <EstimatesBanner show={!!data?.has_estimates} />

      {isLoading && <p className="text-surface-500 dark:text-surface-400">Cargando...</p>}

      {data && (() => {
        const totalSpent = data.by_category.reduce((s, c) => s + parseFloat(c.net_total), 0)
        const catCount = data.by_category.length
        const topCategory = data.by_category.length > 0
          ? data.by_category.reduce((a, b) => parseFloat(a.net_total) > parseFloat(b.net_total) ? a : b).category_name
          : '-'
        const average = catCount > 0 ? totalSpent / catCount : 0

        return <>
          {/* Stat cards */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 md:gap-4 mb-6">
            <Card className="flex items-center gap-3">
              <div className="p-2.5 rounded-lg bg-red-50 dark:bg-red-500/10">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-red-500 dark:text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v12m-3-2.818l.879.659c1.171.879 3.07.879 4.242 0 1.172-.879 1.172-2.303 0-3.182C13.536 12.219 12.768 12 12 12c-.725 0-1.45-.22-2.003-.659-1.106-.879-1.106-2.303 0-3.182s2.9-.879 4.006 0l.415.33M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div className="min-w-0">
                <p className="text-lg font-bold text-surface-800 dark:text-surface-100 truncate">{formatCLP(totalSpent)}</p>
                <p className="text-xs text-surface-500 dark:text-surface-400">Total gastado</p>
              </div>
            </Card>
            <Card className="flex items-center gap-3">
              <div className="p-2.5 rounded-lg bg-blue-50 dark:bg-blue-500/10">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-blue-500 dark:text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9.568 3H5.25A2.25 2.25 0 003 5.25v4.318c0 .597.237 1.17.659 1.591l9.581 9.581c.699.699 1.78.872 2.607.33a18.095 18.095 0 005.223-5.223c.542-.827.369-1.908-.33-2.607L11.16 3.66A2.25 2.25 0 009.568 3z" />
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 6h.008v.008H6V6z" />
                </svg>
              </div>
              <div className="min-w-0">
                <p className="text-lg font-bold text-surface-800 dark:text-surface-100">{catCount}</p>
                <p className="text-xs text-surface-500 dark:text-surface-400">Categorías</p>
              </div>
            </Card>
            <Card className="flex items-center gap-3">
              <div className="p-2.5 rounded-lg bg-amber-50 dark:bg-amber-500/10">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-amber-500 dark:text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 18.75h-9m9 0a3 3 0 013 3h-15a3 3 0 013-3m9 0v-3.375c0-.621-.503-1.125-1.125-1.125h-.871M7.5 18.75v-3.375c0-.621.504-1.125 1.125-1.125h.872m5.007 0H9.497m5.007 0a7.454 7.454 0 01-.982-3.172M9.497 14.25a7.454 7.454 0 00.981-3.172M5.25 4.236c-.982.143-1.954.317-2.916.52A6.003 6.003 0 007.73 9.728M5.25 4.236V4.5c0 2.108.966 3.99 2.48 5.228M5.25 4.236V2.721C7.456 2.41 9.71 2.25 12 2.25c2.291 0 4.545.16 6.75.47v1.516M18.75 4.236c.982.143 1.954.317 2.916.52A6.003 6.003 0 0016.27 9.728M18.75 4.236V4.5c0 2.108-.966 3.99-2.48 5.228m0 0a6.003 6.003 0 01-5.54 0" />
                </svg>
              </div>
              <div className="min-w-0">
                <p className="text-lg font-bold text-surface-800 dark:text-surface-100 truncate">{topCategory}</p>
                <p className="text-xs text-surface-500 dark:text-surface-400">Categoría top</p>
              </div>
            </Card>
            <Card className="flex items-center gap-3">
              <div className="p-2.5 rounded-lg bg-green-50 dark:bg-green-500/10">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-green-500 dark:text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
                </svg>
              </div>
              <div className="min-w-0">
                <p className="text-lg font-bold text-surface-800 dark:text-surface-100 truncate">{formatCLP(average)}</p>
                <p className="text-xs text-surface-500 dark:text-surface-400">Promedio</p>
              </div>
            </Card>
          </div>

          {data.by_category.length > 0 ? (
            <>
              <div className="flex flex-wrap gap-2 mb-6">
                {data.by_category.map((cat) => {
                  const selected = selectedCategories.has(cat.category_name)
                  const color = categoryColor(cat.category_name)
                  return (
                    <button
                      key={cat.category_name}
                      onClick={() => toggleCategory(cat.category_name)}
                      className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium border transition-colors ${
                        selected
                          ? 'bg-white dark:bg-white/[0.1] text-surface-800 dark:text-surface-100 border-surface-300 dark:border-white/[0.12] shadow-sm'
                          : 'bg-surface-100 dark:bg-white/[0.04] text-surface-400 dark:text-surface-500 border-surface-200 dark:border-white/[0.06]'
                      }`}
                    >
                      <span
                        className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                        style={{ backgroundColor: selected ? color : 'rgb(203 213 225)' }}
                      />
                      {cat.category_name}
                      <span className="text-xs opacity-60">{formatCLP(parseFloat(cat.net_total))}</span>
                    </button>
                  )
                })}
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6">
                <Card>
                  <h2 className="text-lg font-semibold mb-4 text-surface-700 dark:text-surface-200">Por categoría</h2>
                  <CategoryBarChart data={data.by_category} selectedCategories={selectedCategories} />
                </Card>
                <Card>
                  <h2 className="text-lg font-semibold mb-4 text-surface-700 dark:text-surface-200">Distribución</h2>
                  <CategoryDoughnut data={data.by_category} selectedCategories={selectedCategories} />
                </Card>
                <Card>
                  <h2 className="text-lg font-semibold mb-4 text-surface-700 dark:text-surface-200">Ranking de gastos</h2>
                  <CategoryLegend data={data.by_category} />
                </Card>
              </div>
            </>
          ) : (
            <div className="flex flex-col items-center justify-center py-20 text-center">
              <svg className="w-24 h-24 text-surface-300 dark:text-surface-600 mb-4" viewBox="0 0 100 100" fill="none">
                <rect x="15" y="60" width="12" height="20" rx="2" fill="currentColor" opacity="0.3" />
                <rect x="35" y="45" width="12" height="35" rx="2" fill="currentColor" opacity="0.4" />
                <rect x="55" y="50" width="12" height="30" rx="2" fill="currentColor" opacity="0.3" />
                <rect x="75" y="55" width="12" height="25" rx="2" fill="currentColor" opacity="0.2" />
                <line x1="10" y1="85" x2="92" y2="85" stroke="currentColor" strokeWidth="2" opacity="0.3" />
              </svg>
              <p className="text-lg font-semibold text-surface-600 dark:text-surface-300 mb-1">No hay datos para este período</p>
              <p className="text-sm text-surface-400 dark:text-surface-500">Probá seleccionando otro mes o rango de fechas</p>
            </div>
          )}
        </>
      })()}
    </PageLayout>
  )
}
