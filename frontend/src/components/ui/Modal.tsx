import { ReactNode, useEffect } from 'react'

interface ModalProps {
  open: boolean
  onClose: () => void
  title: string
  children: ReactNode
}

export default function Modal({ open, onClose, title, children }: ModalProps) {
  useEffect(() => {
    if (!open) return
    function handleKey(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handleKey)
    return () => document.removeEventListener('keydown', handleKey)
  }, [open, onClose])

  if (!open) return null

  return (
    <div className="fixed inset-0 glass-modal-overlay flex items-center justify-center z-50 p-4">
      <div className="glass-modal w-full max-w-auth">
        <h3 className="text-base font-semibold text-surface-800 dark:text-surface-100 mb-4">{title}</h3>
        {children}
      </div>
    </div>
  )
}
