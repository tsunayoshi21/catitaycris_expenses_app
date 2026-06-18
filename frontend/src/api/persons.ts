import apiClient from './client'
import type { Person } from '../types'

export async function fetchPersons(includeArchived = false): Promise<Person[]> {
  const { data } = await apiClient.get<Person[]>(`/persons/${includeArchived ? '?archived=true' : ''}`)
  return data
}

export async function createPerson(payload: { name: string }): Promise<Person> {
  const { data } = await apiClient.post<Person>('/persons/', payload)
  return data
}
