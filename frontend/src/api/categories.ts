import apiClient from './client'
import type { Category } from '../types'

export async function fetchCategories(): Promise<Category[]> {
  const { data } = await apiClient.get<Category[]>('/categories/')
  return data
}

export async function createCategory(payload: { label: string }): Promise<Category> {
  const { data } = await apiClient.post<Category>('/categories/', payload)
  return data
}

export async function deleteCategory(id: number): Promise<void> {
  await apiClient.delete(`/categories/${id}/`)
}
