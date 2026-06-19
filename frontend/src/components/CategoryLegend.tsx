import { categoryColor, formatCLP } from '../utils/categoryColors'

interface CatTotal {
  category_name: string
  total: string
  net_total: string
}

interface Props {
  data: CatTotal[]
}

export default function CategoryLegend({ data }: Props) {
  const total = data.reduce((sum, cat) => sum + parseFloat(cat.net_total), 0)

  return (
    <ul className="space-y-2">
      {data.map((cat, i) => {
        const value = parseFloat(cat.net_total)
        const pct = total > 0 ? (value / total) * 100 : 0
        return (
          <li key={cat.category_name} className="flex items-center gap-3">
            <span className="text-xs text-surface-400 dark:text-surface-500 w-5 text-right">{i + 1}</span>
            <span
              className="w-3 h-3 rounded-full flex-shrink-0"
              style={{ backgroundColor: categoryColor(cat.category_name) }}
            />
            <span className="text-sm text-surface-700 dark:text-surface-300 flex-1 truncate">{cat.category_name}</span>
            <span className="text-sm font-medium text-surface-800 dark:text-surface-100 tabular-nums">
              {formatCLP(value)}
            </span>
            <span className="text-xs text-surface-400 dark:text-surface-500 tabular-nums w-12 text-right">
              {pct.toFixed(1)}%
            </span>
          </li>
        )
      })}
    </ul>
  )
}
