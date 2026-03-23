function hashString(str: string): number {
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash)
    hash |= 0
  }
  return hash
}

/** Deterministic color for any category name — same name always → same color */
export function categoryColor(name: string): string {
  const hue = ((hashString(name) % 360) + 360) % 360
  return `hsl(${hue}, 65%, 55%)`
}

export function formatCLP(value: number): string {
  return '$' + Math.round(value).toLocaleString('es-CL')
}
