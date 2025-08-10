import { createAlovaInstance } from './base'

const MANAGER_SERVER_PORT = import.meta.env.VITE_MANAGER_SERVER_PORT || '7072'
// API base URL configuration
const API_BASE_URL = `http://localhost:${MANAGER_SERVER_PORT}`

// Create alova instance
export const alovaInstance = createAlovaInstance(API_BASE_URL)
