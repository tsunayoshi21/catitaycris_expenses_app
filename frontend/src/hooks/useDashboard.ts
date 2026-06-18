import { useQuery } from '@tanstack/react-query'
import { fetchDashboard } from '../api/dashboard'

export function useDashboard(params: {
  start?: string
  end?: string
  year?: number
  month?: number
  type?: string
  search?: string
  category?: string
} = {}) {
  return useQuery({
    queryKey: ['dashboard', params],
    queryFn: () => fetchDashboard(params),
  })
}
