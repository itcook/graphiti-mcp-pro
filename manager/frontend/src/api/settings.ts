import { alovaInstance } from './alova/client'
import type { Setting, SettingUpdate } from './types'

/**
 * Get current settings
 */
export const getSettings = () => {
  return alovaInstance.Get<Setting>('/api/settings', {
    name: 'getSettings',
  })
}

/**
 * Update settings
 */
export const updateSettings = (data: SettingUpdate) => {
  return alovaInstance.Put<Setting>('/api/settings', data, {
    name: 'updateSettings',
  })
}
