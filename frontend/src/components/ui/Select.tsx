import { useState, useRef, useEffect, useCallback } from 'react'
import { createPortal } from 'react-dom'

export interface SelectOption {
  value: string
  label: string
}

interface SelectProps {
  options: SelectOption[]
  value: string
  onChange: (value: string) => void
  placeholder?: string
  className?: string
}

export default function Select({ options, value, onChange, placeholder, className = '' }: SelectProps) {
  const [open, setOpen] = useState(false)
  const triggerRef = useRef<HTMLButtonElement>(null)
  const dropdownRef = useRef<HTMLDivElement>(null)
  const [pos, setPos] = useState({ top: 0, left: 0, width: 0 })

  const selectedLabel = options.find((o) => o.value === value)?.label ?? placeholder ?? ''

  const updatePosition = useCallback(() => {
    if (triggerRef.current) {
      const rect = triggerRef.current.getBoundingClientRect()
      setPos({ top: rect.bottom + 4, left: rect.left, width: rect.width })
    }
  }, [])

  useEffect(() => {
    if (!open) return
    updatePosition()

    function handleClickOutside(e: MouseEvent) {
      if (
        dropdownRef.current && !dropdownRef.current.contains(e.target as Node) &&
        triggerRef.current && !triggerRef.current.contains(e.target as Node)
      ) {
        setOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    window.addEventListener('scroll', updatePosition, true)
    window.addEventListener('resize', updatePosition)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
      window.removeEventListener('scroll', updatePosition, true)
      window.removeEventListener('resize', updatePosition)
    }
  }, [open, updatePosition])

  function handleSelect(val: string) {
    onChange(val)
    setOpen(false)
  }

  return (
    <>
      <button
        ref={triggerRef}
        type="button"
        onClick={() => setOpen(!open)}
        className={`inline-flex items-center justify-between gap-2 border border-surface-300 dark:border-surface-600 rounded-input px-3 py-2 text-sm
          bg-white dark:bg-white/[0.06] text-surface-800 dark:text-surface-200
          hover:border-surface-400 dark:hover:border-surface-500
          focus:outline-none focus:ring-2 focus:ring-primary-500 dark:focus:ring-primary-400
          cursor-pointer transition-colors ${className}`}
      >
        <span className={`truncate ${!value && placeholder ? 'text-surface-400 dark:text-surface-500' : ''}`}>
          {selectedLabel}
        </span>
        <svg
          className={`h-4 w-4 flex-shrink-0 text-surface-400 dark:text-surface-500 transition-transform ${open ? 'rotate-180' : ''}`}
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 20 20"
          fill="currentColor"
        >
          <path fillRule="evenodd" d="M5.22 8.22a.75.75 0 0 1 1.06 0L10 11.94l3.72-3.72a.75.75 0 1 1 1.06 1.06l-4.25 4.25a.75.75 0 0 1-1.06 0L5.22 9.28a.75.75 0 0 1 0-1.06Z" clipRule="evenodd" />
        </svg>
      </button>

      {open && createPortal(
        <div
          ref={dropdownRef}
          className="fixed z-50 bg-white dark:bg-surface-800 border border-surface-200 dark:border-white/[0.08] rounded-lg shadow-lg dark:shadow-modal-dark max-h-64 overflow-y-auto"
          style={{ top: pos.top, left: pos.left, width: Math.max(pos.width, 160) }}
        >
          {options.map((opt) => (
            <button
              key={opt.value}
              onClick={() => handleSelect(opt.value)}
              className={`w-full text-left px-3 py-1.5 text-sm transition-colors
                hover:bg-surface-50 dark:hover:bg-white/[0.06]
                ${opt.value === value
                  ? 'font-semibold text-primary-600 dark:text-primary-400'
                  : 'text-surface-700 dark:text-surface-200'
                }`}
            >
              {opt.label}
            </button>
          ))}
        </div>,
        document.body
      )}
    </>
  )
}
