import { useRequest } from 'alova/client'
import { getSettings, updateSettings } from '../api/settings'
import type { SettingUpdate } from '../api/types'

/**
 * Hook for managing settings data
 */
export const useSettings = () => {
  // Get settings
  const {
    data: settings,
    loading: isLoading,
    error,
    send: refetch,
  } = useRequest(getSettings, {
    // Auto fetch on mount
    immediate: true,
  })

  return {
    settings,
    isLoading,
    error,
    refetch,
  }
}

/**
 * Hook for updating settings
 */
export const useUpdateSettings = () => {
  const {
    loading: isUpdating,
    error: updateError,
    send: updateSettingsAction,
  } = useRequest((data: SettingUpdate) => updateSettings(data), {
    // Don't auto fetch
    immediate: false,
  })

  const handleUpdateSettings = async (data: SettingUpdate) => {
    try {
      const result = await updateSettingsAction(data)
      return result
    } catch (error) {
      console.error('Failed to update settings:', error)
      throw error
    }
  }

  return {
    updateSettings: handleUpdateSettings,
    isUpdating,
    updateError,
  }
}
