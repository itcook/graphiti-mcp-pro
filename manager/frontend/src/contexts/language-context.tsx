'use client'

import type React from 'react'

import { createContext, useContext, useState } from 'react'

type Language = 'zh-CN' | 'en-US'

interface LanguageContextType {
  language: Language
  setLanguage: (language: Language) => void
  t: (key: string) => string
}

const translations = {
  'zh-CN': {
    // Navigation
    'nav.home': '首页',
    'nav.settings': '设置',
    'nav.tokenUsage': 'TOKEN 用量',
    'nav.logs': '日志',

    // Home

    'home.graphitiMCPService': 'Graphiti MCP Pro 服务',
    'home.serverStatus.running': '运行中',
    'home.serverStatus.stopped': '已停止',
    'home.serverStatus.starting': '启动中...',
    'home.serverStatus.stopping': '停止中...',
    'home.start': '启动',
    'home.restart': '重启',
    'home.stop': '停止',
    'home.mcpConfig': 'MCP 配置',
    'home.mcpConfigDesc': '当前 MCP 服务器配置',
    'home.tokenUsage': '今日 TOKEN 用量',

    // Settings
    'settings.basic': '基础设置',
    'settings.syncReturn': '开启同步返回',
    'settings.parallelRequests': '大模型并行请求数',
    'settings.logSaveDays': '日志保存天数',
    'settings.cleanLogsAtHour': '日志清理时间',
    'settings.days': '天',
    'settings.neo4j': 'Neo4j 数据库设置',
    'settings.neo4j.uri': 'URI',
    'settings.neo4j.user': '用户名',
    'settings.neo4j.password': '密码',
    'settings.largeModel': '大模型连接设置',
    'settings.smallModel': '小模型连接设置',
    'settings.embedding': '文本嵌入连接设置',
    'settings.sameAsLarge': '与大模型相同',
    'settings.baseUrl': '请求地址',
    'settings.apiKey': 'API KEY',
    'settings.modelName': '模型名称',
    'settings.update': '更新',
    'settings.validate.llm': '大模型连接设置不完整',
    'settings.validate.smallModel': '小模型连接设置不完整',
    'settings.validate.embedding': '文本嵌入连接设置不完整',
    'settings.update.success': '设置修改成功',
    'settings.update.error': '设置修改失败，请检查日志',
    'settings.update.loading': '正在更新设置...',

    // Token Usage
    'tokenUsage.byDay': '按日',
    'tokenUsage.byWeek': '按周',
    'tokenUsage.byMonth': '按月',
    'tokenUsage.details': '详细记录',
    'tokenUsage.filter': '筛选',
    'tokenUsage.char.inputTokens': '输入 TOKEN',
    'tokenUsage.char.outputTokens': '输出 TOKEN',
    'tokenUsage.record.page': '页',
    'tokenUsage.record.total': '共',
    'tokenUsage.record.items': '条记录',
    'tokenUsage.record.item': '条记录',
    'tokenUsage.record.time': '时间',
    'tokenUsage.record.model': '模型名称',
    'tokenUsage.record.episode': '记忆片段',
    'tokenUsage.record.responseModel': '数据模型',
    'tokenUsage.record.inputTokens': '输入 TOKEN',
    'tokenUsage.record.outputTokens': '输出 TOKEN',
    'tokenUsage.record.totalTokens': '总计 TOKEN',

    // Logs
    'logs.realtime': '实时日志',
    'logs.history': '历史日志',
    'logs.pause': '暂停',
    'logs.paused': '已暂停',
    'logs.waitingData': '等待数据...',
    'logs.start': '开始',
    'logs.clear': '清空',
    'logs.export': '导出日志',
    'logs.level': '日志级别',
    'logs.source': '来源',
    'logs.level.all': '全部',
    'logs.level.error': '错误',
    'logs.level.warn': '警告',
    'logs.level.info': '信息',
    'logs.level.debug': '调试',
    'logs.searchPlaceholder': '搜索日志...',
    'logs.search': '搜索',
    'logs.noMatchingRecords': '没有匹配的记录',
    'logs.loadingFailed': '加载日志失败',

    // Common
    'common.language': '语言',
    'common.theme': '主题',
    'common.copy': '复制',
    'common.copied': 'MCP 配置代码已复制到剪贴板',
    'common.copyError': '复制 MCP 配置代码失败',
    'common.save': '保存',
    'common.cancel': '取消',
    'common.confirm': '确认',
    'common.loading': '加载中...',
    'common.error': '错误',
    'common.success': '成功',
    'common.warning': '警告',
    'common.info': '信息',
    'common.collapse': '收起',
    'common.pickDate': '请选择日期',
    'common.pickDateRange': '请选择起止日期',
    'common.pickWeek': '请选择周',
    'common.pickMonth': '请选择月份',
    'common.toast.starting': '服务正在启动...',
    'common.toast.started': '服务已启动',
    'common.toast.restarting': '服务正在重启...',
    'common.toast.restarted': '服务已重启',
    'common.toast.stopping': '服务正在停止...',
    'common.toast.stopped': '服务已停止',
  },
  'en-US': {
    // Navigation
    'nav.home': 'Home',
    'nav.settings': 'Settings',
    'nav.tokenUsage': 'Token Usage',
    'nav.logs': 'Logs',

    // Home
    'home.graphitiMCPService': 'Graphiti MC Pro Service',
    'home.serverStatus.running': 'Running',
    'home.serverStatus.stopped': 'Stopped',
    'home.serverStatus.starting': 'Starting...',
    'home.serverStatus.stopping': 'Stopping...',
    'home.start': 'Start',
    'home.restart': 'Restart',
    'home.stop': 'Stop',
    'home.mcpConfig': 'MCP Configuration',
    'home.mcpConfigDesc': 'Current MCP server configuration',
    'home.tokenUsage': "Today's Token Usage",

    // Settings
    'settings.basic': 'Basic Settings',
    'settings.syncReturn': 'Sync Return',
    'settings.parallelRequests': 'Parallel Requests',
    'settings.logSaveDays': 'Log Save Days',
    'settings.cleanLogsAtHour': 'Clean Logs At Hour',
    'settings.days': 'Days',
    'settings.neo4j': 'Neo4j Database Settings',
    'settings.neo4j.uri': 'URI',
    'settings.neo4j.user': 'User',
    'settings.neo4j.password': 'Password',
    'settings.largeModel': 'LLM Settings',
    'settings.smallModel': 'Small Model Settings',
    'settings.embedding': 'Text Embedding Settings',
    'settings.sameAsLarge': 'Same as Large Model',
    'settings.baseUrl': 'Base URL',
    'settings.apiKey': 'API Key',
    'settings.modelName': 'Model Name',
    'settings.update': 'Update',
    'settings.validate.llm': 'LLM settings are incomplete',
    'settings.validate.smallModel': 'Small model settings are incomplete',
    'settings.validate.embedding': 'Embedding settings are incomplete',
    'settings.update.success': 'Settings updated successfully',
    'settings.update.error': 'Failed to update settings, please check the logs',
    'settings.update.loading': 'Updating settings...',

    // Token Usage
    'tokenUsage.byDay': 'Daily',
    'tokenUsage.byWeek': 'Weekly',
    'tokenUsage.byMonth': 'Monthly',
    'tokenUsage.details': 'Detailed Records',
    'tokenUsage.char.inputTokens': 'Input Tokens',
    'tokenUsage.char.outputTokens': 'Output Tokens',
    'tokenUsage.filter': 'Filter',
    'tokenUsage.record.page': 'Page',
    'tokenUsage.record.total': 'Total',
    'tokenUsage.record.items': 'Records',
    'tokenUsage.record.item': 'Record',
    'tokenUsage.record.time': 'Time',
    'tokenUsage.record.model': 'LLM Model Name',
    'tokenUsage.record.episode': 'Episode',
    'tokenUsage.record.responseModel': 'Response Data Model',
    'tokenUsage.record.inputTokens': 'Input Tokens',
    'tokenUsage.record.outputTokens': 'Output Tokens',
    'tokenUsage.record.totalTokens': 'Total Tokens',

    // Logs
    'logs.realtime': 'Realtime',
    'logs.history': 'History',
    'logs.pause': 'Pause',
    'logs.paused': 'Paused',
    'logs.waitingData': 'Waiting for data...',
    'logs.start': 'Start',
    'logs.clear': 'Clear',
    'logs.level': 'Log Level',
    'logs.source': 'Source',
    'logs.level.all': 'All',
    'logs.level.error': 'Error',
    'logs.level.warn': 'Warn',
    'logs.level.info': 'Info',
    'logs.level.debug': 'Debug',
    'logs.searchPlaceholder': 'Search logs...',
    'logs.search': 'Search',
    'logs.noMatchingRecords': 'No matching records',
    'logs.loadingFailed': 'Failed to load logs',

    // Common
    'common.language': 'Language',
    'common.theme': 'Theme',
    'common.copy': 'Copy',
    'common.copied': 'MCP Config Code Copied',
    'common.copyError': 'Failed to copy MCP Config Code',
    'common.save': 'Save',
    'common.cancel': 'Cancel',
    'common.confirm': 'Confirm',
    'common.loading': 'Loading...',
    'common.error': 'Error',
    'common.success': 'Success',
    'common.warning': 'Warning',
    'common.info': 'Info',
    'common.collapse': 'Collapse',
    'common.pickDate': 'Pick a date',
    'common.pickDateRange': 'Pick a date range',
    'common.pickWeek': 'Pick a week',
    'common.pickMonth': 'Pick a month',
    'common.toast.starting': 'Service is starting...',
    'common.toast.started': 'Service started',
    'common.toast.restarting': 'Service is restarting...',
    'common.toast.restarted': 'Service restarted',
    'common.toast.stopping': 'Service is stopping...',
    'common.toast.stopped': 'Service stopped',
  },
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined)

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [language, setLanguage] = useState<Language>('zh-CN')

  const t = (key: string): string => {
    return translations[language][key as keyof (typeof translations)[typeof language]] || key
  }

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  )
}

export function useLanguage() {
  const context = useContext(LanguageContext)
  if (context === undefined) {
    throw new Error('useLanguage must be used within a LanguageProvider')
  }
  return context
}
