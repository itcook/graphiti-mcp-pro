'use client'

import type React from 'react'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { PasswordInput } from '@/components/ui/password-input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { toast } from 'sonner'
import { useLanguage } from '@/contexts/language-context'
import { toastConfig } from '@/lib/utils'
import RadioButtonGroup from '@/components/ui/radio-button-group'
import { useSettings, useUpdateSettings } from '@/hooks/useSettings'
import type { Setting, SettingUpdate } from '@/api/types'

interface SettingsForm {
  // syncReturn: boolean
  parallelRequests: number
  logSaveDays: number
  cleanLogsAtHour: number

  // Neo4j settings
  neo4j: {
    uri: string
    user: string
    password: string
  }

  // Large model settings
  largeModel: {
    baseUrl: string
    apiKey: string
    modelName: string
  }

  // Small model settings
  smallModel: {
    sameAsLarge: boolean
    baseUrl: string
    apiKey: string
    modelName: string
  }

  // Text embedding settings
  embedding: {
    sameAsLarge: boolean
    baseUrl: string
    apiKey: string
    modelName: string
  }
}

function isSmallModelSameAsLarge(settings: Setting): boolean {
  return (
    (settings.small_llm_base_url === settings.llm_base_url &&
      settings.small_llm_api_key === settings.llm_api_key &&
      settings.small_llm_model_name === settings.llm_model_name) ||
    (settings.small_llm_base_url == null &&
      settings.small_llm_api_key == null &&
      settings.small_llm_model_name == null)
  )
}

function isEmbeddingSameAsLarge(settings: Setting): boolean {
  return (
    (settings.embedding_base_url === settings.llm_base_url &&
      settings.embedding_api_key === settings.llm_api_key &&
      settings.embedding_model_name === settings.llm_model_name) ||
    (settings.embedding_base_url == null &&
      settings.embedding_api_key == null &&
      settings.embedding_model_name == null)
  )
}

// Convert backend Setting to frontend SettingsForm
const settingToForm = (setting: Setting): SettingsForm => {
  const _isSmallModelSameAsLarge = isSmallModelSameAsLarge(setting)
  const _isEmbeddingSameAsLarge = isEmbeddingSameAsLarge(setting)
  return {
    // syncReturn: setting.enable_sync_return,
    parallelRequests: setting.semaphore_limit,
    logSaveDays: setting.log_save_days,
    cleanLogsAtHour: setting.clean_logs_at_hour,
    neo4j: {
      uri: setting.neo4j_uri,
      user: setting.neo4j_user,
      password: setting.neo4j_password,
    },
    largeModel: {
      baseUrl: setting.llm_base_url,
      apiKey: setting.llm_api_key,
      modelName: setting.llm_model_name,
    },
    smallModel: {
      sameAsLarge: _isSmallModelSameAsLarge, // If small model URL is not set, consider it same as large model
      baseUrl: _isSmallModelSameAsLarge ? setting.llm_base_url : setting.small_llm_base_url || '',
      apiKey: _isSmallModelSameAsLarge ? setting.llm_api_key : setting.small_llm_api_key || '',
      modelName: _isSmallModelSameAsLarge
        ? setting.llm_model_name
        : setting.small_llm_model_name || '',
    },
    embedding: {
      sameAsLarge: _isEmbeddingSameAsLarge, // If embedding model URL is not set, consider it same as large model
      baseUrl: _isEmbeddingSameAsLarge ? setting.llm_base_url : setting.embedding_base_url || '',
      apiKey: _isEmbeddingSameAsLarge ? setting.llm_api_key : setting.embedding_api_key || '',
      modelName: _isEmbeddingSameAsLarge
        ? setting.llm_model_name
        : setting.embedding_model_name || '',
    },
  }
}

// Convert frontend SettingsForm to backend SettingUpdate
const formToSettingUpdate = (form: SettingsForm): SettingUpdate => {
  return {
    // enable_sync_return: form.syncReturn,
    semaphore_limit: form.parallelRequests,
    log_save_days: form.logSaveDays,
    clean_logs_at_hour: form.cleanLogsAtHour,
    neo4j_uri: form.neo4j.uri,
    neo4j_user: form.neo4j.user,
    neo4j_password: form.neo4j.password,
    llm_base_url: form.largeModel.baseUrl,
    llm_api_key: form.largeModel.apiKey,
    llm_model_name: form.largeModel.modelName,
    // Small model settings: if same as large model, pass undefined; otherwise pass specific values
    small_llm_base_url: form.smallModel.sameAsLarge
      ? form.largeModel.baseUrl
      : form.smallModel.baseUrl,
    small_llm_api_key: form.smallModel.sameAsLarge
      ? form.largeModel.apiKey
      : form.smallModel.apiKey,
    small_llm_model_name: form.smallModel.sameAsLarge
      ? form.largeModel.modelName
      : form.smallModel.modelName,
    // Embedding model settings: if same as large model, pass undefined; otherwise pass specific values
    embedding_base_url: form.embedding.sameAsLarge
      ? form.largeModel.baseUrl
      : form.embedding.baseUrl,
    embedding_api_key: form.embedding.sameAsLarge ? form.largeModel.apiKey : form.embedding.apiKey,
    embedding_model_name: form.embedding.sameAsLarge
      ? form.largeModel.modelName
      : form.embedding.modelName,
  }
}

export function Settings() {
  // Use API hooks
  const { settings: apiSettings, isLoading, error, refetch } = useSettings()
  const { updateSettings: updateSettingsAPI, isUpdating } = useUpdateSettings()

  // Local form state
  const [settings, setSettings] = useState<SettingsForm | undefined>()

  const { t } = useLanguage()

  // When API data loading is complete, update local form state
  useEffect(() => {
    if (apiSettings) {
      setSettings(settingToForm(apiSettings))
    }
  }, [apiSettings])

  useEffect(() => {
    if (isUpdating) {
      toast.loading(t('settings.update.loading'), {
        id: 'settings-update-loading',
        ...toastConfig,
        duration: 0,
      })
    } else {
      toast.dismiss('settings-update-loading')
    }
  }, [isUpdating])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!settings?.largeModel.baseUrl || !settings?.largeModel.modelName) {
      toast.error(t('settings.validate.llm'), toastConfig)
      return
    }

    if (
      !settings?.smallModel.sameAsLarge &&
      (!settings?.smallModel.baseUrl || !settings?.smallModel.modelName)
    ) {
      toast.error(t('settings.validate.smallModel'), toastConfig)
      return
    }

    if (
      !settings?.embedding.sameAsLarge &&
      (!settings?.embedding.baseUrl || !settings?.embedding.modelName)
    ) {
      toast.error(t('settings.validate.embedding'), toastConfig)
      return
    }

    try {
      if (!settings) return

      // Convert form data to API format and submit
      const updateData = formToSettingUpdate(settings)
      await updateSettingsAPI(updateData)

      // Refetch latest data
      refetch()

      toast.success(t('settings.update.success'), toastConfig)
    } catch (error) {
      console.error('Failed to save settings:', error)
      toast.error(t('settings.update.error'), toastConfig)
    }
  }

  const updateSettings = (path: string, value: any) => {
    setSettings((prev) => {
      if (prev == null) return prev

      const keys = path.split('.')
      const newSettings = { ...prev }
      let current: any = newSettings

      for (let i = 0; i < keys.length - 1; i++) {
        current[keys[i]] = { ...current[keys[i]] }
        current = current[keys[i]]
      }

      current[keys[keys.length - 1]] = value
      return newSettings
    })
  }

  // Show loading state
  if (isLoading) {
    return (
      <div className='flex items-center justify-center h-64'>
        <div className='text-center'>
          <div className='animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto mb-4'></div>
          <p>Loading settings...</p>
        </div>
      </div>
    )
  }

  // Show error state
  if (error) {
    return (
      <div className='flex items-center justify-center h-64'>
        <div className='text-center'>
          <p className='text-red-500 mb-4'>Failed to load settings: {error.message}</p>
          <Button onClick={() => refetch()}>Retry</Button>
        </div>
      </div>
    )
  }

  if (settings) {
    return (
      <div className='space-y-6'>
        <form onSubmit={handleSubmit} className='space-y-6'>
          <div className='grid grid-cols-2 gap-6'>
            {/* Basic Settings */}
            <Card>
              <CardHeader>
                <CardTitle>{t('settings.basic')}</CardTitle>
              </CardHeader>
              <CardContent className='space-y-4'>
                <div className='flex items-center space-x-4'>
                  <Label htmlFor='parallelRequests' className='w-32 text-right'>
                    {t('settings.parallelRequests')}
                  </Label>
                  <Input
                    id='parallelRequests'
                    type='number'
                    value={settings.parallelRequests}
                    onChange={(e) =>
                      updateSettings('parallelRequests', Number.parseInt(e.target.value))
                    }
                    className='flex-1'
                  />
                </div>

                {/* <div className='flex items-center space-x-4'>
                  <Label htmlFor='syncReturn' className='w-32 text-right'>
                    {t('settings.syncReturn')}
                  </Label>
                  <Switch
                    id='syncReturn'
                    checked={settings.syncReturn}
                    onCheckedChange={(checked) => updateSettings('syncReturn', checked)}
                  />
                </div> */}
                <div className='flex items-center space-x-4'>
                  <Label htmlFor='logSaveDays' className='w-32 text-right'>
                    {t('settings.logSaveDays')}
                  </Label>
                  <RadioButtonGroup
                    id='logSaveDays'
                    // className='flex-1'
                    value={settings.logSaveDays}
                    onChange={(value) => updateSettings('logSaveDays', value)}
                    options={[
                      { label: `3 ${t('settings.days')}`, value: 3 },
                      { label: `7 ${t('settings.days')}`, value: 7 },
                      { label: `15 ${t('settings.days')}`, value: 15 },
                      { label: `30 ${t('settings.days')}`, value: 30 },
                    ]}
                  />
                </div>
                <div className='flex items-center space-x-4'>
                  <Label htmlFor='cleanLogsAtHour' className='w-32 text-right'>
                    {t('settings.cleanLogsAtHour')}
                  </Label>
                  <Select
                    value={settings.cleanLogsAtHour.toString()}
                    onValueChange={(value) =>
                      updateSettings('cleanLogsAtHour', Number.parseInt(value))
                    }>
                    <SelectTrigger className='flex-1'>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {Array.from({ length: 24 }, (_, i) => (
                        <SelectItem key={i} value={i.toString()}>
                          {i.toString().padStart(2, '0')}:00
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </CardContent>
            </Card>

            {/* Neo4j Connection Settings */}
            <Card>
              <CardHeader>
                <CardTitle>{t('settings.neo4j')}</CardTitle>
              </CardHeader>
              <CardContent className='space-y-4'>
                <div className='flex items-center space-x-4'>
                  <Label htmlFor='neo4jUri' className='w-32 text-right'>
                    {t('settings.neo4j.uri')}
                  </Label>
                  <Input
                    id='neo4jUri'
                    type='url'
                    value={settings.neo4j.uri}
                    onChange={(e) => updateSettings('neo4j.uri', e.target.value)}
                    className='flex-1'
                  />
                </div>
                <div className='flex items-center space-x-4'>
                  <Label htmlFor='neo4jUser' className='w-32 text-right'>
                    {t('settings.neo4j.user')}
                  </Label>
                  <Input
                    id='neo4jUser'
                    value={settings.neo4j.user}
                    onChange={(e) => updateSettings('neo4j.user', e.target.value)}
                    className='flex-1'
                  />
                </div>
                <div className='flex items-center space-x-4'>
                  <Label htmlFor='neo4jPassword' className='w-32 text-right'>
                    {t('settings.neo4j.password')}
                  </Label>
                  <PasswordInput
                    id='neo4jPassword'
                    value={settings.neo4j.password}
                    onChange={(e) => updateSettings('neo4j.password', e.target.value)}
                    className='flex-1'
                  />
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Large Model Connection Settings */}
          <Card>
            <CardHeader>
              <CardTitle>{t('settings.largeModel')}</CardTitle>
            </CardHeader>
            <CardContent className='space-y-4'>
              <div className='flex items-center space-x-4'>
                <Label htmlFor='largeModelUrl' className='w-32 text-right'>
                  {t('settings.baseUrl')}
                </Label>
                <Input
                  id='largeModelUrl'
                  type='url'
                  value={settings.largeModel.baseUrl}
                  onChange={(e) => updateSettings('largeModel.baseUrl', e.target.value)}
                  className='flex-1'
                />
              </div>
              <div className='flex items-center space-x-4'>
                <Label htmlFor='largeModelApiKey' className='w-32 text-right'>
                  {t('settings.apiKey')}
                </Label>
                <PasswordInput
                  id='largeModelApiKey'
                  value={settings.largeModel.apiKey}
                  onChange={(e) => updateSettings('largeModel.apiKey', e.target.value)}
                  className='flex-1'
                />
              </div>
              <div className='flex items-center space-x-4'>
                <Label htmlFor='largeModelName' className='w-32 text-right'>
                  {t('settings.modelName')}
                </Label>
                <Input
                  id='largeModelName'
                  value={settings.largeModel.modelName}
                  onChange={(e) => updateSettings('largeModel.modelName', e.target.value)}
                  className='flex-1'
                />
              </div>
            </CardContent>
          </Card>
          <div className='grid grid-cols-2 gap-6'>
            {/* Small Model Connection Settings */}
            <Card>
              <CardHeader>
                <div className='flex items-center justify-between'>
                  <div>
                    <CardTitle>{t('settings.smallModel')}</CardTitle>
                  </div>
                  <div className='flex items-center space-x-2'>
                    <Switch
                      id='smallModelSameAsLarge'
                      checked={settings.smallModel.sameAsLarge}
                      onCheckedChange={(checked) =>
                        updateSettings('smallModel.sameAsLarge', checked)
                      }
                    />
                    <Label htmlFor='smallModelSameAsLarge'>{t('settings.sameAsLarge')}</Label>
                  </div>
                </div>
              </CardHeader>
              <CardContent className='space-y-4'>
                <div className='flex items-center space-x-4'>
                  <Label htmlFor='smallModelUrl' className='w-32 text-right'>
                    {t('settings.baseUrl')}
                  </Label>
                  <Input
                    id='smallModelUrl'
                    type='url'
                    value={
                      settings.smallModel.sameAsLarge
                        ? settings.largeModel.baseUrl
                        : settings.smallModel.baseUrl
                    }
                    disabled={settings.smallModel.sameAsLarge}
                    onChange={(e) => updateSettings('smallModel.baseUrl', e.target.value)}
                    className='flex-1'
                  />
                </div>
                <div className='flex items-center space-x-4'>
                  <Label htmlFor='smallModelApiKey' className='w-32 text-right'>
                    {t('settings.apiKey')}
                  </Label>
                  <PasswordInput
                    id='smallModelApiKey'
                    value={
                      settings.smallModel.sameAsLarge
                        ? settings.largeModel.apiKey
                        : settings.smallModel.apiKey
                    }
                    disabled={settings.smallModel.sameAsLarge}
                    onChange={(e) => updateSettings('smallModel.apiKey', e.target.value)}
                    className='flex-1'
                  />
                </div>
                <div className='flex items-center space-x-4'>
                  <Label htmlFor='smallModelName' className='w-32 text-right'>
                    {t('settings.modelName')}
                  </Label>
                  <Input
                    id='smallModelName'
                    value={
                      settings.smallModel.sameAsLarge
                        ? settings.largeModel.modelName
                        : settings.smallModel.modelName
                    }
                    disabled={settings.smallModel.sameAsLarge}
                    onChange={(e) => updateSettings('smallModel.modelName', e.target.value)}
                    className='flex-1'
                  />
                </div>
              </CardContent>
            </Card>

            {/* Text Embedding Connection Settings */}
            <Card>
              <CardHeader>
                <div className='flex items-center justify-between'>
                  <div>
                    <CardTitle>{t('settings.embedding')}</CardTitle>
                  </div>
                  <div className='flex items-center space-x-2'>
                    <Switch
                      id='embeddingSameAsLarge'
                      checked={settings.embedding.sameAsLarge}
                      onCheckedChange={(checked) =>
                        updateSettings('embedding.sameAsLarge', checked)
                      }
                    />
                    <Label htmlFor='embeddingSameAsLarge'>{t('settings.sameAsLarge')}</Label>
                  </div>
                </div>
              </CardHeader>
              <CardContent className='space-y-4'>
                <div className='flex items-center space-x-4'>
                  <Label htmlFor='embeddingUrl' className='w-32 text-right'>
                    {t('settings.baseUrl')}
                  </Label>
                  <Input
                    id='embeddingUrl'
                    type='url'
                    value={
                      settings.embedding.sameAsLarge
                        ? settings.largeModel.baseUrl
                        : settings.embedding.baseUrl
                    }
                    disabled={settings.embedding.sameAsLarge}
                    onChange={(e) => updateSettings('embedding.baseUrl', e.target.value)}
                    className='flex-1'
                  />
                </div>
                <div className='flex items-center space-x-4'>
                  <Label htmlFor='embeddingApiKey' className='w-32 text-right'>
                    {t('settings.apiKey')}
                  </Label>
                  <PasswordInput
                    id='embeddingApiKey'
                    value={
                      settings.embedding.sameAsLarge
                        ? settings.largeModel.apiKey
                        : settings.embedding.apiKey || ''
                    }
                    disabled={settings.embedding.sameAsLarge}
                    onChange={(e) => updateSettings('embedding.apiKey', e.target.value)}
                    className='flex-1'
                  />
                </div>
                <div className='flex items-center space-x-4'>
                  <Label htmlFor='embeddingModelName' className='w-32 text-right'>
                    {t('settings.modelName')}
                  </Label>
                  <Input
                    id='embeddingModelName'
                    value={
                      settings.embedding.sameAsLarge
                        ? settings.largeModel.modelName
                        : settings.embedding.modelName
                    }
                    disabled={settings.embedding.sameAsLarge}
                    onChange={(e) => updateSettings('embedding.modelName', e.target.value)}
                    className='flex-1'
                  />
                </div>
              </CardContent>
            </Card>
          </div>

          <Button type='submit' size='lg' disabled={isUpdating}>
            {isUpdating ? 'Saving...' : t('settings.update')}
          </Button>
        </form>
      </div>
    )
  }
}
