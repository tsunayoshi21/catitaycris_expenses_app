interface Props {
  page: number
  totalPages: number
  onPageChange: (page: number) => void
}

/** Construye la lista de páginas a mostrar, con elipsis para rangos largos. */
function pageRange(current: number, total: number): (number | '...')[] {
  const delta = 1
  const left = Math.max(2, current - delta)
  const right = Math.min(total - 1, current + delta)
  const range: (number | '...')[] = [1]

  if (left > 2) range.push('...')
  for (let i = left; i <= right; i++) range.push(i)
  if (right < total - 1) range.push('...')
  if (total > 1) range.push(total)

  return range
}

const baseBtn =
  'min-w-[2rem] px-2.5 py-1.5 text-sm rounded-input border transition-colors disabled:opacity-40 disabled:cursor-not-allowed'
const inactiveBtn =
  'border-surface-300 dark:border-surface-600 text-surface-700 dark:text-surface-300 ' +
  'hover:bg-surface-50 dark:hover:bg-white/[0.06]'
const activeBtn =
  'border-primary-500 bg-primary-500 text-white dark:border-primary-400 dark:bg-primary-400'

export default function Pagination({ page, totalPages, onPageChange }: Props) {
  if (totalPages <= 1) return null

  const pages = pageRange(page, totalPages)

  return (
    <nav className="flex items-center justify-center gap-1.5 mt-6 flex-wrap" aria-label="Paginación">
      <button
        type="button"
        onClick={() => onPageChange(page - 1)}
        disabled={page <= 1}
        className={`${baseBtn} ${inactiveBtn}`}
      >
        Anterior
      </button>

      {pages.map((p, i) =>
        p === '...' ? (
          <span key={`gap-${i}`} className="px-1.5 text-surface-400 dark:text-surface-500 select-none">
            …
          </span>
        ) : (
          <button
            key={p}
            type="button"
            onClick={() => onPageChange(p)}
            aria-current={p === page ? 'page' : undefined}
            className={`${baseBtn} ${p === page ? activeBtn : inactiveBtn}`}
          >
            {p}
          </button>
        ),
      )}

      <button
        type="button"
        onClick={() => onPageChange(page + 1)}
        disabled={page >= totalPages}
        className={`${baseBtn} ${inactiveBtn}`}
      >
        Siguiente
      </button>
    </nav>
  )
}
