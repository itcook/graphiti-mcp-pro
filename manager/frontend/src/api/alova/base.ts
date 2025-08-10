import { createAlova } from 'alova'
import adapterFetch from 'alova/fetch'
import ReactHook from 'alova/react'
import { logger } from '@/utils/logger'

// Create alova instance
export const createAlovaInstance = (baseURL: string) => {
  const instance = createAlova({
    // Request adapter
    requestAdapter: adapterFetch(),

    // State hook for React
    statesHook: ReactHook,

    // Base URL
    baseURL,

    // Global request configuration
    beforeRequest(method) {
      // Set default headers
      method.config.headers = {
        'Content-Type': 'application/json',
        ...method.config.headers,
      }

      // Log request for debugging
      logger.info(`[API Request] ${method.type.toUpperCase()} ${method.url}`)
    },

    // Global response interceptor
    responded: {
      // Success response handler
      onSuccess: async (response, method) => {
        logger.info(
          `[API Response] ${method.type.toUpperCase()} ${method.url} - ${response.status}`
        )

        // Check if response is ok
        if (!response.ok) {
          throw new Error(`HTTP Error: ${response.status} ${response.statusText}`)
        }

        // Parse JSON response
        const data = await response.json()
        return data
      },

      // Error response handler
      onError: (error, method) => {
        logger.error(`[API Error] ${method.type.toUpperCase()} ${method.url}:`, error)

        // Handle different types of errors
        if (error instanceof TypeError && error.message.includes('fetch')) {
          // Network error
          throw new Error(
            'Network connection failed. Please check if the backend server is running.'
          )
        }

        if (error.message.includes('HTTP Error: 404')) {
          throw new Error('API endpoint not found.')
        }

        if (error.message.includes('HTTP Error: 500')) {
          throw new Error('Internal server error. Please try again later.')
        }

        // Re-throw the original error
        throw error
      },
    },

    cacheFor: null,

    // Global timeout (30 seconds)
    timeout: 30000,
  })

  return instance
}
