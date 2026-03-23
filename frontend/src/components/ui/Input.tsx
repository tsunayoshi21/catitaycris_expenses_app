import { InputHTMLAttributes, forwardRef } from 'react'

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string
  hint?: string
}

const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, hint, id, className = '', ...props }, ref) => {
    const inputId = id || props.name
    return (
      <div>
        {label && (
          <label htmlFor={inputId} className="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={inputId}
          className={`w-full border border-surface-300 dark:border-surface-600 rounded-input px-3 py-2 text-sm
            bg-white dark:bg-white/[0.06] text-surface-800 dark:text-surface-200
            placeholder:text-surface-400 dark:placeholder:text-surface-500
            focus:outline-none focus:ring-2 focus:ring-primary-500 dark:focus:ring-primary-400 focus:border-primary-500 dark:focus:border-primary-400
            disabled:opacity-60 disabled:cursor-not-allowed
            ${className}`}
          {...props}
        />
        {hint && <p className="text-xs text-surface-400 dark:text-surface-500 mt-1">{hint}</p>}
      </div>
    )
  }
)
Input.displayName = 'Input'
export default Input
