import { useState, useMemo } from 'react'
import DateRangePicker from './DateRangePicker'
import type { FilterParams } from './DateRangePicker'
import { useCategories } from '../hooks/useCategories'
import { Select } from './ui'

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

const TYPE_OPTIONS = [
  { value: '', label: 'Todos los tipos' },
  { value: 'debito', label: 'Débito' },
  { value: 'credito', label: 'Crédito' },
  { value: 'transferencia', label: 'Transferencia' },
  { value: 'ingreso', label: 'Ingreso' },
  { value: 'comision', label: 'Comisión/Cargos' },
  { value: 'pago_tarjeta', label: 'Pago tarjeta' },
]

export default function FilterBar({ filters, onChange }: Props) {
  const { data: categories } = useCategories()
  const [searchValue, setSearchValue] = useState(filters.search ?? '')

  const categoryOptions = useMemo(() => [
    { value: '', label: 'Todas las categorías' },
    ...(categories?.map((cat) => ({ value: cat.name, label: cat.label })) ?? []),
  ], [categories])

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

  return (
    <div className="flex flex-col gap-3 md:flex-row md:flex-wrap md:items-center">
      <input
        type="text"
        placeholder="Buscar..."
        value={searchValue}
        onChange={(e) => handleSearch(e.target.value)}
        className="border border-surface-300 dark:border-surface-600 rounded-input px-3 py-2 text-sm
          bg-white dark:bg-white/[0.06] text-surface-800 dark:text-surface-200
          placeholder:text-surface-400 dark:placeholder:text-surface-500
          focus:outline-none focus:ring-2 focus:ring-primary-500 dark:focus:ring-primary-400
          w-full md:w-auto"
      />
      <Select
        options={TYPE_OPTIONS}
        value={filters.type ?? ''}
        onChange={(val) => onChange({ ...filters, type: val || undefined })}
      />
      <Select
        options={categoryOptions}
        value={filters.category ?? ''}
        onChange={(val) => onChange({ ...filters, category: val || undefined })}
      />
      <DateRangePicker onFilterChange={handleDateChange} />
    </div>
  )
}
