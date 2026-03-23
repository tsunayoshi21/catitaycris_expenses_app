import { ReactNode } from 'react'

interface BadgeProps {
  children: ReactNode
  className?: string
  dot?: string
}

export default function Badge({ children, className = '', dot }: BadgeProps) {
  return (
    <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium ${className}`}>
      {dot && <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: dot }} />}
      {children}
    </span>
  )
}
