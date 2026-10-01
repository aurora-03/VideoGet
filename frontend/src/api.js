import axios from 'axios'

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',
  timeout: 30000,
  withCredentials: true,
  headers: { 'X-Model-Session': 'required' }
})

export function fileUrl(path) {
  return new URL(path, new URL(api.defaults.baseURL, window.location.origin)).href
}
