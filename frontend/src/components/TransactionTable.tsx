import { useState, Fragment } from 'react'
import {
  useReactTable,
  getCoreRowModel,
  flexRender,
  createColumnHelper,
} from '@tanstack/react-table'
import type { Transaction } from '../types'
import CategoryCell from './CategoryCell'
import SplitPanel from './SplitPanel'
import { formatCLP } from '../utils/categoryColors'

const TYPE_STYLES: Record<string, string> = {
  debito:        'bg-red-50 text-red-700 dark:bg-red-500/10 dark:text-red-400',
  credito:       'bg-blue-50 text-blue-700 dark:bg-blue-500/10 dark:text-blue-400',
  transferencia: 'bg-purple-50 text-purple-700 dark:bg-purple-500/10 dark:text-purple-400',
  ingreso:       'bg-green-50 text-green-700 dark:bg-green-500/10 dark:text-green-400',
}

const TYPE_LABELS: Record<string, string> = {
  debito: 'Débito', credito: 'Crédito', transferencia: 'Transferencia',
  ingreso: 'Ingreso',
}

const columnHelper = createColumnHelper<Transaction>()

interface Props {
  transactions: Transaction[]
  total: number
}

export default function TransactionTable({ transactions, total }: Props) {
  const [expandedId, setExpandedId] = useState<number | null>(null)

  const columns = [
    columnHelper.accessor('date', {
      header: 'Fecha',
      cell: (info) => new Date(info.getValue()).toLocaleDateString('es-CL'),
    }),
    columnHelper.accessor('merchant', {
      header: 'Comercio',
      cell: (info) => info.getValue() || '-',
    }),
    columnHelper.accessor('amount', {
      header: 'Monto',
      cell: (info) => {
        const type = info.row.original.type
        const isPositive = type === 'ingreso' || type === 'credito'
        return (
          <span className={isPositive ? 'text-green-600 dark:text-green-400' : ''}>
            {formatCLP(parseFloat(info.getValue()))}
          </span>
        )
      },
    }),
    columnHelper.accessor('net_amount', {
      header: 'Neto',
      cell: (info) => {
        const type = info.row.original.type
        const isPositive = type === 'ingreso' || type === 'credito'
        return (
          <span className={isPositive ? 'text-green-600 dark:text-green-400' : ''}>
            {formatCLP(parseFloat(info.getValue()))}
          </span>
        )
      },
    }),
    columnHelper.accessor('type', {
      header: 'Tipo',
      cell: (info) => {
        const type = info.getValue()
        return (
          <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${TYPE_STYLES[type] ?? 'bg-surface-100 text-surface-600 dark:bg-white/[0.06] dark:text-surface-400'}`}>
            {TYPE_LABELS[type] ?? type}
          </span>
        )
      },
    }),
    columnHelper.accessor('category_name', {
      header: 'Categoría',
      cell: (info) => <CategoryCell transaction={info.row.original} />,
    }),
    columnHelper.accessor('description', {
      header: 'Descripción',
      cell: (info) => <span className="text-sm text-surface-600 dark:text-surface-400">{info.getValue() || '-'}</span>,
    }),
    columnHelper.display({
      id: 'splits',
      header: 'Splits',
      cell: (info) => {
        const tx = info.row.original
        return (
          <button
            onClick={() => setExpandedId(expandedId === tx.id ? null : tx.id)}
            className="text-xs text-primary-500 hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300"
          >
            {tx.split_count > 0 ? `${tx.split_count} split(s)` : '+ Agregar'}
          </button>
        )
      },
    }),
  ]

  const table = useReactTable({
    data: transactions,
    columns,
    getCoreRowModel: getCoreRowModel(),
  })

  return (
    <div>
      <p className="text-sm text-surface-500 dark:text-surface-400 mb-3">{total} transacciones</p>
      <div className="overflow-x-auto rounded-xl shadow-sm dark:shadow-card-dark">
        <table className="w-full min-w-[800px] text-sm bg-white dark:bg-white/[0.04]">
          <thead>
            {table.getHeaderGroups().map((hg) => (
              <tr key={hg.id} className="bg-surface-50 border-b border-surface-200 dark:bg-white/[0.04] dark:border-white/[0.08]">
                {hg.headers.map((header) => (
                  <th key={header.id} className="px-4 py-3 text-left font-semibold text-surface-600 dark:text-surface-300">
                    {flexRender(header.column.columnDef.header, header.getContext())}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {table.getRowModel().rows.map((row) => (
              <Fragment key={row.id}>
                <tr className="border-b border-surface-100 hover:bg-surface-50 dark:border-white/[0.04] dark:hover:bg-white/[0.04]">
                  {row.getVisibleCells().map((cell) => (
                    <td key={cell.id} className="px-4 py-3">
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </td>
                  ))}
                </tr>
                {expandedId === row.original.id && (
                  <tr>
                    <td colSpan={columns.length} className="px-4 py-2 bg-primary-50 dark:bg-primary-500/10">
                      <SplitPanel transactionId={row.original.id} />
                    </td>
                  </tr>
                )}
              </Fragment>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
