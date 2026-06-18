import { useState, useMemo } from 'react'
import { Select } from './ui'

export type FilterParams = { year?: number; month?: number; start?: string; end?: string }
type Mode = 'month' | 'range'

interface Props {
  onFilterChange: (params: FilterParams) => void
}

const MONTHS = [
  'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
  'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre',
]

const CURRENT_YEAR = new Date().getFullYear()
const YEARS = Array.from({ length: CURRENT_YEAR - 2023 }, (_, i) => 2024 + i)

const MONTH_OPTIONS = MONTHS.map((name, i) => ({ value: String(i + 1), label: name }))
const YEAR_OPTIONS = YEARS.map((y) => ({ value: String(y), label: String(y) }))

const dateInputClass = 'border border-surface-300 dark:border-surface-600 rounded-input px-3 py-2 text-sm bg-white dark:bg-white/[0.06] text-surface-800 dark:text-surface-200 focus:outline-none focus:ring-2 focus:ring-primary-500 dark:focus:ring-primary-400'

export default function DateRangePicker({ onFilterChange }: Props) {
  const now = useMemo(() => new Date(), [])
  const [mode, setMode] = useState<Mode>('month')

  const [year, setYear] = useState(now.getFullYear())
  const [month, setMonth] = useState(now.getMonth() + 1)

  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')

  function switchMode(newMode: Mode) {
    setMode(newMode)
    if (newMode === 'month') {
      onFilterChange({ year, month, start: undefined, end: undefined })
    } else {
      onFilterChange({ year: undefined, month: undefined, start: startDate || undefined, end: endDate || undefined })
    }
  }

  function handleMonthChange(y: number, m: number) {
    setYear(y)
    setMonth(m)
    onFilterChange({ year: y, month: m, start: undefined, end: undefined })
  }

  function handleStartDate(val: string) {
    setStartDate(val)
    onFilterChange({ year: undefined, month: undefined, start: val || undefined, end: endDate || undefined })
  }

  function handleEndDate(val: string) {
    setEndDate(val)
    onFilterChange({ year: undefined, month: undefined, start: startDate || undefined, end: val || undefined })
  }

  return (
    <div className="flex items-center gap-3 flex-wrap">
      {/* Mode toggle */}
      <div className="flex rounded-lg overflow-hidden border border-surface-300 dark:border-surface-600 text-sm">
        {([{ id: 'month', label: 'Mes' }, { id: 'range', label: 'Rango' }] as const).map(({ id, label }) => (
          <button
            key={id}
            onClick={() => switchMode(id)}
            className={`px-3 py-1.5 ${mode === id ? 'bg-primary-500 dark:bg-primary-600 text-white' : 'bg-white dark:bg-surface-800 text-surface-600 dark:text-surface-300 hover:bg-surface-50 dark:hover:bg-surface-700'}`}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Stack both modes in the same space so the toggle never shifts */}
      <div className="grid">
        <div className={`col-start-1 row-start-1 flex items-center gap-3 ${mode !== 'month' ? 'invisible' : ''}`}>
          <Select
            options={MONTH_OPTIONS}
            value={String(month)}
            onChange={(val) => handleMonthChange(year, +val)}
          />
          <Select
            options={YEAR_OPTIONS}
            value={String(year)}
            onChange={(val) => handleMonthChange(+val, month)}
          />
        </div>

        <div className={`col-start-1 row-start-1 flex items-center gap-3 ${mode !== 'range' ? 'invisible' : ''}`}>
          <span className="text-sm text-surface-500 dark:text-surface-400">Desde</span>
          <input
            type="date"
            value={startDate}
            onChange={(e) => handleStartDate(e.target.value)}
            className={dateInputClass}
          />
          <span className="text-sm text-surface-500 dark:text-surface-400">Hasta</span>
          <input
            type="date"
            value={endDate}
            onChange={(e) => handleEndDate(e.target.value)}
            className={dateInputClass}
          />
        </div>
      </div>
    </div>
  )
}
