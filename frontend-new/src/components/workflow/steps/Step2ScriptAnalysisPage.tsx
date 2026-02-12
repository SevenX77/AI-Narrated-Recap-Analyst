/**
 * Step2ScriptAnalysisPage - Script Analysis
 */
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Separator } from '@/components/ui/separator'
import { LogViewer, type LogEntry } from '@/components/workflow/LogViewer'
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion"
import type { Step2ScriptAnalysisState, PhaseStatus } from '@/types/workflow'
import { CheckCircle, Clock, XCircle, Loader2, Play, StopCircle, File, Eye } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useNavigate } from 'react-router-dom'

interface Step2ScriptAnalysisPageProps {
  projectId: string
  stepState: Step2ScriptAnalysisState
  logs?: Array<{
    id: string
    timestamp: string
    level: 'info' | 'warning' | 'error'
    message: string
    step_id?: string
  }>
  onStart?: () => void
  onStartEpisode?: (episodeId: string) => void
  onStopEpisode?: (episodeId: string) => void
  onStopAll?: () => void
}

const phaseNames: Record<string, string> = {
  phase_1: 'SRT Import',
  phase_2: 'Text Extraction',
  phase_3: 'Hook Detection (ep01 only)',
  phase_4: 'Hook Analysis',
  phase_5: 'Semantic Segmentation',
  phase_6: 'ABC Classification',
  phase_7: 'Quality Validation',
}

const statusConfig: Record<PhaseStatus, { icon: React.ReactNode; color: string; variant: 'default' | 'secondary' | 'destructive' | 'outline' }> = {
  locked: { icon: <Clock className="h-3 w-3" />, color: 'text-muted-foreground', variant: 'secondary' },
  ready: { icon: <Clock className="h-3 w-3" />, color: 'text-blue-500', variant: 'outline' },
  running: { icon: <Loader2 className="h-3 w-3 animate-spin" />, color: 'text-yellow-500', variant: 'outline' },
  completed: { icon: <CheckCircle className="h-3 w-3" />, color: 'text-green-500', variant: 'default' },
  failed: { icon: <XCircle className="h-3 w-3" />, color: 'text-red-500', variant: 'destructive' },
  cancelled: { icon: <XCircle className="h-3 w-3" />, color: 'text-gray-500', variant: 'secondary' },
}

function EpisodeCard({ 
  projectId,
  episodeId, 
  episodeData, 
  onStartEpisode, 
  onStopEpisode 
}: { 
  projectId: string
  episodeId: string
  episodeData: any
  onStartEpisode?: (episodeId: string) => void
  onStopEpisode?: (episodeId: string) => void
}) {
  const navigate = useNavigate()
  const isRunning = episodeData.status === 'running'
  const isCompleted = episodeData.status === 'completed'
  const canProcess = episodeData.status === 'ready' || episodeData.status === 'failed'

  return (
    <div className="flex items-center justify-between rounded-md p-3 border hover:bg-accent/50 transition-colors">
      <div className="flex items-center gap-3 flex-1 min-w-0">
        <div className={statusConfig[episodeData.status as PhaseStatus]?.color || 'text-muted-foreground'}>
          {statusConfig[episodeData.status as PhaseStatus]?.icon}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-mono text-sm font-medium">{episodeId}</span>
            <Badge variant={statusConfig[episodeData.status as PhaseStatus]?.variant || 'secondary'} className="text-xs uppercase">
              {episodeData.status}
            </Badge>
          </div>
          {isCompleted && episodeData.quality_score && (
            <div className="text-xs text-muted-foreground mt-1">
              Quality: {episodeData.quality_score}/100 • Cost: ${episodeData.cost?.toFixed(3) || '0.000'}
            </div>
          )}
          {isRunning && (
            <div className="text-xs text-muted-foreground mt-1">
              <Loader2 className="h-3 w-3 inline animate-spin mr-1" />
              Processing... • LLM Calls: {episodeData.llm_calls || 0}
            </div>
          )}
        </div>
      </div>
      <div className="flex items-center gap-1">
        {isCompleted && (
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            onClick={() => navigate(`/project/${projectId}/script-analysis/${episodeId}`)}
            title="View results"
          >
            <Eye className="h-4 w-4" />
          </Button>
        )}
        {canProcess && onStartEpisode && (
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            onClick={() => onStartEpisode(episodeId)}
            title="Process this episode"
          >
            <Play className="h-4 w-4" />
          </Button>
        )}
        {isRunning && onStopEpisode && (
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 text-destructive hover:text-destructive"
            onClick={() => onStopEpisode(episodeId)}
            title="Stop processing"
          >
            <StopCircle className="h-4 w-4" />
          </Button>
        )}
      </div>
    </div>
  )
}

export function Step2ScriptAnalysisPage({ 
  projectId,
  stepState, 
  logs = [], 
  onStart, 
  onStartEpisode,
  onStopEpisode,
  onStopAll
}: Step2ScriptAnalysisPageProps) {
  // Convert logs to LogEntry format
  const logEntries: LogEntry[] = logs.map(log => ({
    id: log.id,
    timestamp: log.timestamp,
    level: log.level as 'info' | 'warning' | 'error',
    message: log.message,
    step_id: log.step_id,
  }))

  const hasRunningEpisodes = Object.values(stepState.episodes_status).some(
    (ep: any) => ep.status === 'running'
  )

  return (
    <div className="flex flex-1 flex-col gap-4 overflow-auto">
      <div className="px-2">
        <h2 className="text-3xl font-bold tracking-tight">Step 2: Script Analysis</h2>
        <p className="text-muted-foreground">Process script files through 7 phases</p>
      </div>

      {/* Progress Card */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Overall Progress</CardTitle>
              <CardDescription>
                {stepState.completed_episodes}/{stepState.total_episodes} episodes completed
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              {!hasRunningEpisodes ? (
                <Button onClick={onStart}>
                  <Play className="h-4 w-4 mr-2" />
                  Start All Episodes
                </Button>
              ) : (
                <Button variant="destructive" onClick={onStopAll}>
                  <StopCircle className="h-4 w-4 mr-2" />
                  Stop All
                </Button>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <Progress value={stepState.overall_progress} className="h-2" />
          <div className="grid grid-cols-4 gap-4 text-sm">
            <div>
              <p className="text-muted-foreground">Total Episodes</p>
              <p className="text-xl font-bold">{stepState.total_episodes}</p>
            </div>
            <div>
              <p className="text-muted-foreground">LLM Calls</p>
              <p className="text-xl font-bold">{stepState.llm_calls_count}</p>
            </div>
            <div>
              <p className="text-muted-foreground">Total Cost</p>
              <p className="text-xl font-bold">${stepState.total_cost.toFixed(3)}</p>
            </div>
            <div>
              <p className="text-muted-foreground">Time</p>
              <p className="text-xl font-bold">
                {stepState.processing_time > 60 ? `${(stepState.processing_time / 60).toFixed(0)}m` : `${stepState.processing_time.toFixed(0)}s`}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Separator />

      {/* Episodes List (File List Style) */}
      <Card>
        <CardHeader>
          <CardTitle>Episodes ({stepState.total_episodes})</CardTitle>
          <CardDescription>Process individual episodes or all at once</CardDescription>
        </CardHeader>
        <CardContent>
          {Object.keys(stepState.episodes_status).length > 0 ? (
            <Accordion type="multiple" defaultValue={['episodes']} className="w-full">
              <AccordionItem value="episodes" className="border rounded-lg px-2 last:border-b">
                <AccordionTrigger className="hover:no-underline py-2">
                  <div className="flex items-center gap-2">
                    <span className="text-foreground">SRT Episodes</span>
                    <span className="text-xs text-muted-foreground">({stepState.total_episodes})</span>
                  </div>
                </AccordionTrigger>
                <AccordionContent className="pt-2 pb-2">
                  <div className="space-y-2">
                    {Object.entries(stepState.episodes_status)
                      .sort(([a], [b]) => a.localeCompare(b))
                      .map(([episodeId, episodeData]) => (
                        <EpisodeCard
                          key={episodeId}
                          projectId={projectId}
                          episodeId={episodeId}
                          episodeData={episodeData}
                          onStartEpisode={onStartEpisode}
                          onStopEpisode={onStopEpisode}
                        />
                      ))}
                  </div>
                </AccordionContent>
              </AccordionItem>
            </Accordion>
          ) : (
            <div className="text-center py-12 text-muted-foreground">
              <File className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p className="text-sm">No episodes detected</p>
              <p className="text-xs mt-1">Make sure SRT files are uploaded in Step 1</p>
            </div>
          )}
        </CardContent>
      </Card>

      {logEntries.length > 0 && (
        <>
          <Separator />
          <LogViewer logs={logEntries} maxHeight="400px" autoScroll={true} />
        </>
      )}
    </div>
  )
}
