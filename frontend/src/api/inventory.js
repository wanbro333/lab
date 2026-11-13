import { request } from './client'

export const listItems = (filters = {}) =>
  request(`/inventory/items/?${new URLSearchParams(filters)}`)
export const createItem = (item) => request('/inventory/items/', { method: 'POST', body: item })
