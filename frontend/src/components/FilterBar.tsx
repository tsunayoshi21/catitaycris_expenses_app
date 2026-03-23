import { useState } from 'react'
import DateRangePicker from './DateRangePicker'
import type { FilterParams } from './DateRangePicker'
import { useCategories } from '../hooks/useCategories'

const inputClass = 'border border-surface-300 rounded-input px-3 py-1.5 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-primary-500 w-full md:w-auto dark:border-surface-600 dark:bg-white/[0.06] dark:text-surface-200 dark:placeholder:text-surface-500 dark:focus:ring-primary-400'
const selectClass = 'border border-surface-300 rounded-input px-3 py-1.5 text-sm w-full md:w-auto dark:border-surface-600 dark:bg-surface-800 dark:text-surface-200'

export interface Filters {
  year?: number
  month?: number
  start?: string
  end?: string
  type?: string
  search?: string
  category?: string
}

interface Props {
  filters: Filters
  onChange: (filters: Filters) => void
}

export default function FilterBar({ filters, onChange }: Props) {
  const { data: categories } = useCategories()
  const [searchValue, setSearchValue] = useState(filters.search ?? '')

  function handleDateChange(params: FilterParams) {
    onChange({
      ...filters,
      year: params.year,
      month: params.month,
      start: params.start,
      end: params.end,
    })
  }

  function handleSearch(value: string) {
    setSearchValue(value)
    onChange({ ...filters, search: value || undefined })
  }

  function handleType(value: string) {
    onChange({ ...filters, type: value || undefined })
  }

  function handleCategory(value: string) {
    onChange({ ...filters, category: value || undefined })
  }

  return (
    <div className="flex flex-col gap-3 md:flex-row md:flex-wrap md:items-center">
      <input
        type="text"
        placeholder="Buscar..."
        value={searchValue}
        onChange={(e) => handleSearch(e.target.value)}
        className={inputClass}
      />
      <select
        className={selectClass}
        value={filters.type ?? ''}
        onChange={(e) => handleType(e.target.value)}
      >
        <option value="">Todos los tipos</option>
        <option value="debito">Débito</option>
        <option value="credito">Crédito</option>
        <option value="transferencia">Transferencia</option>
        <option value="ingreso">Ingreso</option>
      </select>
      <select
        className={selectClass}
        value={filters.category ?? ''}
        onChange={(e) => handleCategory(e.target.value)}
      >
        <option value="">Todas las categorías</option>
        {categories?.map((cat) => (
          <option key={cat.id} value={cat.name}>{cat.label}</option>
        ))}
      </select>
      <DateRangePicker onFilterChange={handleDateChange} />
    </div>
  )
}
