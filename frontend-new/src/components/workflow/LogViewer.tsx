/**
 * LogViewer - Real-time Log Viewer
 */
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { useState, useEffect, useRef } from 'react'
import { ChevronDown, ChevronRight, Search, Download, Trash2 } from 'lucide-react'
import { cn } from '@/lib/utils'

export interface LogEntry {
  id: string
  timestamp: string
  level: 'info' | 'warning' | 'error' | 'debug'
  message: string
  step_id?: string
  llm_data?: {
    model: string
    prompt_summary: string
    response_summary: string
    tokens_used?: { input: number; output: number; total: number }
    cost?: number
    duration_ms?: number
  }
}

interface LogViewerProps {
  logs: LogEntry[]
  autoScroll?: boolean
  maxHeight?: string
  showFilters?: boolean
  onExport?: () => void
}

const levelConfig = {
  info: { color: 'text-blue-600 dark:text-blue-400', bg: 'bg-blue-100 dark:bg-blue-900', label: 'INFO' },
  warning: { color: 'text-yellow-600 dark:text-yellow-400', bg: 'bg-yellow-100 dark:bg-yellow-900', label: 'WARN' },
  error: { color: 'text-red-600 dark:text-red-400', bg: 'bg-red-100 dark:bg-red-900', label: 'ERROR' },
  debug: { color: 'text-gray-600 dark:text-gray-400', bg: 'bg-gray-100 dark:bg-gray-900', label: 'DEBUG' },
}

function LLMThinkingBlock({ data }: { data: LogEntry['llm_data'] }) {
  const [isExpanded, setIsExpanded] = useState(false)

  if (!data) return null

  return (
    <div className="mt-2 border-l-2 border-purple-500 pl-3">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center gap-2 text-sm font-medium text-purple-700 dark:text-purple-300 hover:underline"
      >
        {isExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
        <span>LLM Thinking Process</span>
        <Badge variant="outline" className="text-xs">
          {data.model}
        </Badge>
      </button>

      {isExpanded && (
        <div className="mt-2 space-y-2 text-xs">
          <div className="p-2 bg-purple-50 dark:bg-purple-950 rounded">
            <p className="font-semibold mb-1">Prompt Summary:</p>
            <p className="text-muted-foreground">{data.prompt_summary}</p>
          </div>

          <div className="p-2 bg-purple-50 dark:bg-purple-950 rounded">
            <p className="font-semibold mb-1">Response Summary:</p>
            <p className="text-muted-foreground">{data.response_summary}</p>
          </div>

          {data.tokens_used && (
            <div className="flex items-center gap-4 p-2 bg-muted rounded text-xs">
              <div>
                <span className="text-muted-foreground">Tokens:</span>
                <span className="font-mono ml-1">{data.tokens_used.total}</span>
                <span className="text-muted-foreground ml-1">
                  (in: {data.tokens_used.input}, out: {data.tokens_used.output})
                </span>
              </div>
              {data.cost !== undefined && (
                <div>
                  <span className="text-muted-foreground">Cost:</span>
                  <span className="font-mono ml-1">${data.cost.toFixed(4)}</span>
                </div>
              )}
              {data.duration_ms !== undefined && (
                <div>
                  <span className="text-muted-foreground">Time:</span>
                  <span className="font-mono ml-1">{(data.duration_ms / 1000).toFixed(2)}s</span>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function LogEntryItem({ log, searchTerm }: { log: LogEntry; searchTerm: string }) {
  const config = levelConfig[log.level]
  const time = new Date(log.timestamp).toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })

  const highlightText = (text: string) => {
    if (!searchTerm) return text
    const parts = text.split(new RegExp(`(${searchTerm})`, 'gi'))
    return parts.map((part, i) =>
      part.toLowerCase() === searchTerm.toLowerCase() ? (
        <mark key={i} className="bg-yellow-200 dark:bg-yellow-800">
          {part}
        </mark>
      ) : (
        part
      )
    )
  }

  return (
    <div className="py-2 border-b last:border-b-0">
      <div className="flex items-start gap-2">
        <span className="font-mono text-xs text-muted-foreground shrink-0">{time}</span>
        <Badge className={cn('shrink-0 text-xs', config.bg, config.color)}>{config.label}</Badge>
        <p className="text-sm flex-1 break-words">{highlightText(log.message)}</p>
      </div>
      <LLMThinkingBlock data={log.llm_data} />
    </div>
  )
}

export function LogViewer({ logs, autoScroll = true, maxHeight = '500px', showFilters = true, onExport }: LogViewerProps) {
  const [searchTerm, setSearchTerm] = useState('')
  const [levelFilter, setLevelFilter] = useState<Set<LogEntry['level']>>(new Set(['info', 'warning', 'error']))
  const logContainerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (autoScroll && logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight
    }
  }, [logs, autoScroll])

  const filteredLogs = logs.filter((log) => {
    if (!levelFilter.has(log.level)) return false
    if (searchTerm && !log.message.toLowerCase().includes(searchTerm.toLowerCase())) return false
    return true
  })

  const toggleLevelFilter = (level: LogEntry['level']) => {
    const newFilter = new Set(levelFilter)
    if (newFilter.has(level)) {
      newFilter.delete(level)
    } else {
      newFilter.add(level)
    }
    setLevelFilter(newFilter)
  }

  const handleExport = () => {
    if (onExport) {
      onExport()
    } else {
      const text = logs.map((log) => `[${log.timestamp}] [${log.level.toUpperCase()}] ${log.message}`).join('\n')
      const blob = new Blob([text], { type: 'text/plain' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `logs-${Date.now()}.txt`
      a.click()
      URL.revokeObjectURL(url)
    }
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between gap-4">
          <CardTitle className="text-base">Real-time Logs ({filteredLogs.length}/{logs.length})</CardTitle>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={handleExport}>
              <Download className="h-3 w-3 mr-2" />
              Export
            </Button>
            <Button variant="outline" size="sm" onClick={() => confirm('Clear all logs?')}>
              <Trash2 className="h-3 w-3 mr-2" />
              Clear
            </Button>
          </div>
        </div>

        {showFilters && (
          <>
            <Separator className="my-3" />
            <div className="space-y-3">
              <div className="relative">
                <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input placeholder="Search logs..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} className="pl-8 h-9" />
              </div>

              <div className="flex items-center gap-2">
                <span className="text-xs text-muted-foreground">Level:</span>
                {(['info', 'warning', 'error', 'debug'] as const).map((level) => (
                  <Button
                    key={level}
                    variant={levelFilter.has(level) ? 'default' : 'outline'}
                    size="sm"
                    className="h-7 text-xs"
                    onClick={() => toggleLevelFilter(level)}
                  >
                    {levelConfig[level].label}
                  </Button>
                ))}
              </div>
            </div>
          </>
        )}
      </CardHeader>

      <CardContent className="p-0">
        <div ref={logContainerRef} className="overflow-auto scrollbar-thin px-4 py-2 bg-muted/30" style={{ maxHeight }}>
          {filteredLogs.length > 0 ? (
            <div className="space-y-0">
              {filteredLogs.map((log) => (
                <LogEntryItem key={log.id} log={log} searchTerm={searchTerm} />
              ))}
            </div>
          ) : (
            <div className="flex items-center justify-center h-32 text-muted-foreground text-sm">
              {logs.length === 0 ? 'No logs yet' : 'No matching logs'}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
