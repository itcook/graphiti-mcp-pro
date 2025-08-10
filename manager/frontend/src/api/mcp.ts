import { alovaInstance } from './alova/client'
import { MCPControlRequest, MCPControlResponse, MCPStatusResponse } from './types'

/**
 * Control MCP service (start/stop/restart)
 */
export const controlMCPService = (data: MCPControlRequest) => {
  return alovaInstance.Post<MCPControlResponse>('/api/mcp/control', data, {
    name: 'controlMCPService',
  })
}

/**
 * Get current MCP service health
 */
export const getMCPServiceHealth = () => {
  return alovaInstance.Get<MCPStatusResponse>('/api/mcp/health', {
    name: 'getMCPServiceHealth',
  })
}

/**
 * Get current MCP service status （Server-Sent Events）
 */

export const getMCPServiceStatus = () => {
  return alovaInstance.Get<MCPStatusResponse>('/api/mcp/status', {
    name: 'getMCPServiceStatus',
  })
}
