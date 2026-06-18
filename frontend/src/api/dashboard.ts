import apiClient from './client'
import type { DashboardData } from '../types'

export async function fetchDashboard(params: {
  start?: string
  end?: string
  year?: number
  month?: number
  type?: string
  search?: string
  category?: string
} = {}): Promise<DashboardData> {
  const { data } = await apiClient.get<DashboardData>('/dashboard/', { params })
  return data
}
