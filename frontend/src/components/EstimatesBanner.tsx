interface EstimatesBannerProps {
  show: boolean
}

export default function EstimatesBanner({ show }: EstimatesBannerProps) {
  if (!show) return null

  return (
    <div className="flex items-start gap-2 mb-4 rounded-lg border border-amber-300 dark:border-amber-500/40 bg-amber-50 dark:bg-amber-500/10 px-4 py-3 text-sm text-amber-800 dark:text-amber-300">
      <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
      </svg>
      <span>Algunos montos en USD son estimados (tipo de cambio referencial) y se ajustarán al pagar la tarjeta.</span>
    </div>
  )
}
