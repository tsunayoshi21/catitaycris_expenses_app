interface StatusMessageProps {
  text: string
  variant: 'error' | 'success'
}

export default function StatusMessage({ text, variant }: StatusMessageProps) {
  const color = variant === 'error' ? 'text-red-500 dark:text-red-400' : 'text-green-600 dark:text-green-400'
  return <p className={`text-sm ${color}`}>{text}</p>
}
