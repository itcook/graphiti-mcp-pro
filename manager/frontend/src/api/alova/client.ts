import { createAlovaInstance } from './base'

// API base URL configuration
// 使用代理方式：前端API路径已包含 /api，由 Caddy 代理转发到后端服务
const getApiBaseUrl = () => {
  // 如果有完整的 API 基础 URL 配置，直接使用（用于开发环境或特殊配置）
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL
  }
  
  // 生产环境：使用空字符串，因为 API 路径已经包含 /api 前缀
  // Caddy 会代理所有 /api/* 请求到后端服务
  return ''
}

const API_BASE_URL = getApiBaseUrl()

// Create alova instance
export const alovaInstance = createAlovaInstance(API_BASE_URL)
