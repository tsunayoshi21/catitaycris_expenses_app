import { ButtonHTMLAttributes } from 'react'

type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger'
type ButtonSize = 'sm' | 'md'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant
  size?: ButtonSize
  fullWidth?: boolean
  loading?: boolean
  loadingText?: string
}

const variantClasses: Record<ButtonVariant, string> = {
  primary:   'bg-primary-600 text-white hover:bg-primary-700 disabled:opacity-50 dark:bg-primary-500 dark:hover:bg-primary-400',
  secondary: 'bg-surface-100 text-surface-700 hover:bg-surface-200 border border-surface-300 disabled:opacity-50 dark:bg-white/[0.08] dark:text-surface-200 dark:border-surface-600 dark:hover:bg-white/[0.12]',
  ghost:     'text-surface-600 hover:text-surface-800 hover:bg-surface-100 dark:text-surface-400 dark:hover:text-surface-200 dark:hover:bg-white/[0.06]',
  danger:    'text-red-500 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300',
}

const sizeClasses: Record<ButtonSize, string> = {
  sm: 'px-3 py-1.5 text-xs',
  md: 'px-4 py-2 text-sm',
}

export default function Button({
  variant = 'primary',
  size = 'md',
  fullWidth = false,
  loading = false,
  loadingText,
  children,
  className = '',
  disabled,
  ...props
}: ButtonProps) {
  return (
    <button
      className={`rounded-input font-medium transition-colors
        ${variantClasses[variant]}
        ${sizeClasses[size]}
        ${fullWidth ? 'w-full' : ''}
        ${className}`}
      disabled={disabled || loading}
      {...props}
    >
      {loading && loadingText ? loadingText : children}
    </button>
  )
}
