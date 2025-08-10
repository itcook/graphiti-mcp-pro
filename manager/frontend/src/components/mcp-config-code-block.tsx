import {
  CodeBlock,
  CodeBlockHeader,
  CodeBlockFiles,
  CodeBlockFilename,
  CodeBlockCopyButton,
  CodeBlockBody,
  CodeBlockItem,
  CodeBlockContent,
} from '@/components/ui/shadcn-io/code-block'
import type { BundledLanguage } from '@/components/ui/shadcn-io/code-block'
import { toast } from 'sonner'
import { toastConfig } from '@/lib/utils'
import { useLanguage } from '@/contexts/language-context'

export function MCPConfigCodeBlock() {
  // MCP port is now obtained from environment variable, default is 8082
  const port = import.meta.env.VITE_MCP_PORT || '8082'
  const mcpConfig = {
    mcpServers: {
      graphiti_pro: {
        transport: 'http',
        url: `http://localhost:${port}/mcp`,
      },
    },
  }

  const code = [
    {
      language: 'json',
      filename: 'mcp.json',
      code: JSON.stringify(mcpConfig, null, 2),
    },
  ]

  const { t } = useLanguage()

  return (
    <CodeBlock data={code} defaultValue={code[0].language}>
      <CodeBlockHeader>
        <CodeBlockFiles>
          {(item) => (
            <CodeBlockFilename key={item.language} value={item.language}>
              {item.filename}
            </CodeBlockFilename>
          )}
        </CodeBlockFiles>
        <CodeBlockCopyButton
          onCopy={() => toast.success(t('common.copied'), toastConfig)}
          onError={() => toast.error(t('common.copyError'), toastConfig)}
        />
      </CodeBlockHeader>
      <CodeBlockBody>
        {(item) => (
          <CodeBlockItem key={item.language} value={item.language}>
            <CodeBlockContent language={item.language as BundledLanguage}>
              {item.code}
            </CodeBlockContent>
          </CodeBlockItem>
        )}
      </CodeBlockBody>
    </CodeBlock>
  )
}
