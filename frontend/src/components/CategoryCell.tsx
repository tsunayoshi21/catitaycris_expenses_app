import { useState, useRef, useEffect, useCallback } from 'react'
import { createPortal } from 'react-dom'
import { useQueryClient } from '@tanstack/react-query'
import { useCategories } from '../hooks/useCategories'
import { useUpdateTransaction } from '../hooks/useTransactions'
import { createCategory, deleteCategory } from '../api/categories'
import type { Transaction } from '../types'
import { categoryColor } from '../utils/categoryColors'

interface Props {
  transaction: Transaction
}

export default function CategoryCell({ transaction }: Props) {
  const [editing, setEditing] = useState(false)
  const [creating, setCreating] = useState(false)
  const [newLabel, setNewLabel] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)
  const triggerRef = useRef<HTMLButtonElement>(null)
  const dropdownRef = useRef<HTMLDivElement>(null)
  const [dropdownPos, setDropdownPos] = useState({ top: 0, left: 0 })
  const { data: categories } = useCategories()
  const { mutate: updateTx } = useUpdateTransaction()
  const qc = useQueryClient()

  useEffect(() => {
    if (creating && inputRef.current) inputRef.current.focus()
  }, [creating])

  const updatePosition = useCallback(() => {
    if (triggerRef.current) {
      const rect = triggerRef.current.getBoundingClientRect()
      setDropdownPos({ top: rect.bottom + 4, left: rect.left })
    }
  }, [])

  useEffect(() => {
    if (!editing || creating) return
    updatePosition()
    function handleClick(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setEditing(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    window.addEventListener('scroll', updatePosition, true)
    return () => {
      document.removeEventListener('mousedown', handleClick)
      window.removeEventListener('scroll', updatePosition, true)
    }
  }, [editing, creating, updatePosition])

  function handleSelect(value: string) {
    updateTx({ id: transaction.id, data: { category_name: value } })
    setEditing(false)
  }

  async function handleDelete(id: number, e: React.MouseEvent) {
    e.stopPropagation()
    try {
      await deleteCategory(id)
      await qc.invalidateQueries({ queryKey: ['categories'] })
      await qc.invalidateQueries({ queryKey: ['transactions'] })
    } catch { /* backend rejects deleting defaults */ }
  }

  async function handleCreate() {
    const label = newLabel.trim()
    if (!label) return
    try {
      const cat = await createCategory({ label })
      await qc.invalidateQueries({ queryKey: ['categories'] })
      updateTx({ id: transaction.id, data: { category_name: cat.name } })
    } finally {
      setCreating(false)
      setNewLabel('')
      setEditing(false)
    }
  }

  if (!editing) {
    return (
      <button
        ref={triggerRef}
        onClick={() => setEditing(true)}
        className="text-left"
      >
        {transaction.category_name ? (
          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium bg-surface-100 dark:bg-white/[0.06] text-surface-700 dark:text-surface-200 hover:ring-1 hover:ring-primary-300 dark:hover:ring-primary-500 transition-shadow">
            <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: categoryColor(transaction.category_name) }} />
            {transaction.category_name}
          </span>
        ) : (
          <span className="text-surface-400 dark:text-surface-500 italic text-sm">Sin categoría</span>
        )}
      </button>
    )
  }

  if (creating) {
    return (
      <div className="flex items-center gap-1">
        <input
          ref={inputRef}
          value={newLabel}
          onChange={(e) => setNewLabel(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') handleCreate()
            if (e.key === 'Escape') { setCreating(false); setNewLabel('') }
          }}
          placeholder="Nombre categoría"
          className="text-sm border border-primary-300 dark:border-primary-500 bg-white dark:bg-white/[0.06] dark:text-surface-200 rounded px-2 py-1 w-32"
        />
        <button
          onClick={handleCreate}
          disabled={!newLabel.trim()}
          className="text-xs bg-primary-600 dark:bg-primary-500 text-white rounded px-2 py-1 hover:bg-primary-700 dark:hover:bg-primary-400 disabled:opacity-50"
        >
          Crear
        </button>
        <button
          onClick={() => { setCreating(false); setNewLabel('') }}
          className="text-xs text-surface-500 hover:text-surface-700 dark:text-surface-400 dark:hover:text-surface-200"
        >
          ×
        </button>
      </div>
    )
  }

  return (
    <>
      <button
        ref={triggerRef}
        className="text-left"
      >
        {transaction.category_name ? (
          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium bg-surface-100 dark:bg-white/[0.06] text-surface-700 dark:text-surface-200 ring-1 ring-primary-300 dark:ring-primary-500">
            <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: categoryColor(transaction.category_name) }} />
            {transaction.category_name}
          </span>
        ) : (
          <span className="text-surface-400 dark:text-surface-500 italic text-sm">Sin categoría</span>
        )}
      </button>
      {createPortal(
        <div
          ref={dropdownRef}
          className="fixed z-50 w-56 bg-white dark:bg-surface-800 border border-surface-200 dark:border-white/[0.08] rounded-lg shadow-lg dark:shadow-modal-dark max-h-64 overflow-y-auto"
          style={{ top: dropdownPos.top, left: dropdownPos.left }}
        >
          <button
            onClick={() => handleSelect('')}
            className="w-full text-left px-3 py-1.5 text-sm text-surface-400 dark:text-surface-500 italic hover:bg-surface-50 dark:hover:bg-white/[0.06]"
          >
            Sin categoría
          </button>

          <div className="border-t border-surface-100 dark:border-white/[0.06]" />

          {categories?.map((cat) => (
            <div
              key={cat.id}
              className="flex items-center group hover:bg-surface-50 dark:hover:bg-white/[0.06]"
            >
              <button
                onClick={() => handleSelect(cat.name)}
                className={`flex-1 text-left px-3 py-1.5 text-sm ${
                  cat.name === transaction.category_name ? 'font-semibold text-primary-600 dark:text-primary-400' : 'text-surface-700 dark:text-surface-200'
                }`}
              >
                {cat.label}
              </button>
              {!cat.is_default && (
                <button
                  onClick={(e) => handleDelete(cat.id, e)}
                  className="px-2 py-1 text-xs text-red-400 dark:text-red-500 opacity-0 group-hover:opacity-100 hover:text-red-600 dark:hover:text-red-400"
                  title="Eliminar categoría"
                >
                  ×
                </button>
              )}
            </div>
          ))}

          <div className="border-t border-surface-100 dark:border-white/[0.06]" />

          <button
            onClick={() => setCreating(true)}
            className="w-full text-left px-3 py-1.5 text-sm text-primary-600 dark:text-primary-400 hover:bg-primary-50 dark:hover:bg-primary-500/10 font-medium"
          >
            + Nueva categoría...
          </button>
        </div>,
        document.body
      )}
    </>
  )
}
