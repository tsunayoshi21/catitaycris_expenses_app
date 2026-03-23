import { useState } from 'react'
import { Button } from './ui'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchSplits, createSplit, updateSplit, deleteSplit } from '../api/transactions'
import { fetchPersons } from '../api/persons'
import type { ExpenseSplit, Person } from '../types'

interface Props {
  transactionId: number
}

export default function SplitPanel({ transactionId }: Props) {
  const qc = useQueryClient()
  const [personName, setPersonName] = useState('')
  const [amount, setAmount] = useState('')

  const { data: splits = [], isLoading } = useQuery({
    queryKey: ['splits', transactionId],
    queryFn: () => fetchSplits(transactionId),
  })

  const { data: persons = [] } = useQuery({
    queryKey: ['persons'],
    queryFn: () => fetchPersons(),
  })

  const addSplit = useMutation({
    mutationFn: () => createSplit(transactionId, { person_name: personName, amount }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['splits', transactionId] })
      qc.invalidateQueries({ queryKey: ['transactions'] })
      setPersonName('')
      setAmount('')
    },
  })

  const markPaid = useMutation({
    mutationFn: (splitId: number) => updateSplit(transactionId, splitId, { paid_back: true }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['splits', transactionId] })
      qc.invalidateQueries({ queryKey: ['transactions'] })
    },
  })

  const removeSplit = useMutation({
    mutationFn: (splitId: number) => deleteSplit(transactionId, splitId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['splits', transactionId] })
      qc.invalidateQueries({ queryKey: ['transactions'] })
    },
  })

  if (isLoading) return <p className="text-sm text-surface-500 dark:text-surface-400">Cargando splits...</p>

  return (
    <div className="py-2">
      <h3 className="text-sm font-semibold text-surface-700 dark:text-surface-200 mb-2">Splits</h3>
      {splits.length === 0 && <p className="text-xs text-surface-400 dark:text-surface-500 mb-2">Sin splits registrados.</p>}
      <div className="space-y-1 mb-3">
        {(splits as ExpenseSplit[]).map((split) => (
          <div key={split.id} className="flex items-center gap-3 text-sm dark:text-surface-200">
            <span className="font-medium">{split.person_name_snapshot}</span>
            <span>${parseFloat(split.amount).toLocaleString('es-CL')}</span>
            {split.paid_back ? (
              <span className="text-green-600 dark:text-green-400 text-xs">✓ Pagado</span>
            ) : (
              <button
                onClick={() => markPaid.mutate(split.id)}
                className="text-xs text-primary-500 hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300"
              >
                Marcar pagado
              </button>
            )}
            <button
              onClick={() => removeSplit.mutate(split.id)}
              className="text-xs text-red-400 hover:text-red-600 dark:text-red-500 dark:hover:text-red-400"
            >
              ×
            </button>
          </div>
        ))}
      </div>
      <div className="flex items-center gap-2">
        <input
          list={`persons-${transactionId}`}
          value={personName}
          onChange={(e) => setPersonName(e.target.value)}
          placeholder="Nombre persona"
          className="border border-surface-300 dark:border-surface-600 bg-white dark:bg-white/[0.06] dark:text-surface-200 rounded-input px-2 py-1 text-sm w-36"
        />
        <datalist id={`persons-${transactionId}`}>
          {(persons as Person[]).map((p) => (
            <option key={p.id} value={p.name} />
          ))}
        </datalist>
        <input
          type="number"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          placeholder="Monto"
          className="border border-surface-300 dark:border-surface-600 bg-white dark:bg-white/[0.06] dark:text-surface-200 rounded-input px-2 py-1 text-sm w-24"
        />
        <Button size="sm" onClick={() => addSplit.mutate()} disabled={!personName || !amount}>
          Agregar
        </Button>
      </div>
    </div>
  )
}
