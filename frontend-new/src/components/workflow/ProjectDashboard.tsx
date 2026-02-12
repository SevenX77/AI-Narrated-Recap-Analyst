import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Separator } from '@/components/ui/separator'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import type { PhaseIAnalystState, PhaseStatus } from '@/types/workflow'
import { File, Film, BookOpen, Link2, Clock, Zap } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

interface ProjectDashboardProps {
  projectId: string
  phaseState: PhaseIAnalystState
}

const stepConfig = {
  step_1_import: {
    icon: File,
    title: 'Import',
    description: 'Upload and standardize source files',
  },
  step_2_script: {
    icon: Film,
    title: 'Script Analysis',
    description: 'Process script files through 7 phases',
  },
  step_3_novel: {
    icon: BookOpen,
    title: 'Novel Analysis',
    description: 'Analyze novel content in 8 steps',
  },
  step_4_alignment: {
    icon: Link2,
    title: 'Script-Novel Alignment',
    description: 'Align script sentences with novel paragraphs',
  },
}

const statusConfig: Record<PhaseStatus, { label: string; color: string }> = {
  locked: { label: 'Locked', color: 'bg-gray-500' },
  ready: { label: 'Ready', color: 'bg-blue-500' },
  running: { label: 'Running', color: 'bg-yellow-500' },
  completed: { label: 'Completed', color: 'bg-green-500' },
  failed: { label: 'Failed', color: 'bg-red-500' },
  cancelled: { label: 'Cancelled', color: 'bg-gray-400' },
}

// Get lock reason for a step
const getLockReason = (stepKey: string, phaseState: PhaseIAnalystState): string | null => {
  const stepState = phaseState[stepKey as keyof PhaseIAnalystState]
  if (typeof stepState === 'object' && stepState.status === 'locked' && !stepState.dependencies?.is_met) {
    switch (stepKey) {
      case 'step_2_script':
        return 'Requires Import step to be completed'
      case 'step_3_novel':
        return 'Requires Import step to be completed'
      case 'step_4_alignment':
        return 'Requires Script Analysis and Novel Analysis to be completed'
      default:
        return 'Locked'
    }
  }
  return null
}

export function ProjectDashboard({ projectId, phaseState }: ProjectDashboardProps) {
  const navigate = useNavigate()

  const completedSteps = [
    phaseState.step_1_import,
    phaseState.step_2_script,
    phaseState.step_3_novel,
    phaseState.step_4_alignment,
  ].filter((s) => s.status === 'completed').length

  return (
    <div className="flex flex-1 flex-col gap-4 overflow-auto">
      {/* Header */}
      <div className="flex items-center justify-between px-2">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Phase I: Analyst Agent</h1>
          <p className="text-muted-foreground">Content analysis workflow</p>
        </div>
      </div>

        {/* Overall Progress */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Zap className="h-5 w-5" />
              <CardTitle>Overall Progress</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <Progress value={phaseState.overall_progress} className="h-2" />
            <div className="grid grid-cols-4 gap-4 text-sm">
              <div>
                <p className="text-muted-foreground">Completed Steps</p>
                <p className="text-2xl font-bold">
                  {completedSteps}/4
                </p>
              </div>
              <div>
                <p className="text-muted-foreground">LLM Calls</p>
                <p className="text-2xl font-bold">{phaseState.total_llm_calls}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Total Cost</p>
                <p className="text-2xl font-bold">${phaseState.total_cost.toFixed(3)}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Processing Time</p>
                <p className="text-2xl font-bold">
                  {phaseState.total_processing_time > 60
                    ? `${(phaseState.total_processing_time / 60).toFixed(0)}m`
                    : `${phaseState.total_processing_time.toFixed(0)}s`}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Separator />

        {/* Step Cards */}
        <div className="grid gap-4 md:grid-cols-2">
          {Object.entries(phaseState).map(([key, stepState]) => {
            if (!key.startsWith('step_')) return null

            const config = stepConfig[key as keyof typeof stepConfig]
            if (!config) return null

            if (typeof stepState !== 'object' || !('status' in stepState)) return null
            const statusCfg = statusConfig[stepState.status as PhaseStatus]
            const Icon = config.icon
            const isLocked = stepState.status === 'locked'
            const lockReason = getLockReason(key, phaseState)

            return (
              <Card
                key={key}
                className={`transition-shadow ${
                  isLocked
                    ? 'cursor-not-allowed opacity-60'
                    : 'cursor-pointer hover:shadow-md'
                }`}
                onClick={() => {
                  if (!isLocked) {
                    navigate(`/project/${projectId}/workflow/${key}`)
                  }
                }}
              >
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="p-2 rounded-lg bg-primary/10">
                        <Icon className="h-5 w-5 text-primary" />
                      </div>
                      <div>
                        <CardTitle className="text-base">{config.title}</CardTitle>
                        <CardDescription className="text-xs mt-1">{config.description}</CardDescription>
                      </div>
                    </div>
                    {lockReason ? (
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Badge className={statusCfg.color}>{statusCfg.label}</Badge>
                        </TooltipTrigger>
                        <TooltipContent>
                          <p>{lockReason}</p>
                        </TooltipContent>
                      </Tooltip>
                    ) : (
                      <Badge className={statusCfg.color}>{statusCfg.label}</Badge>
                    )}
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <Progress value={stepState.overall_progress} className="h-1.5" />
                    <div className="grid grid-cols-3 gap-2 text-xs">
                      <div>
                        <p className="text-muted-foreground">LLM Calls</p>
                        <p className="font-mono font-semibold">{stepState.llm_calls_count}</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Cost</p>
                        <p className="font-mono font-semibold">${stepState.total_cost.toFixed(3)}</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Time</p>
                        <p className="font-mono font-semibold">
                          {stepState.processing_time > 60
                            ? `${(stepState.processing_time / 60).toFixed(0)}m`
                            : `${stepState.processing_time.toFixed(0)}s`}
                        </p>
                      </div>
                    </div>

                    {stepState.error_message && (
                      <p className="text-xs text-destructive">{stepState.error_message}</p>
                    )}

                    {stepState.status === 'locked' && stepState.dependencies?.is_met === false && (
                      <p className="text-xs text-muted-foreground">
                        {key === 'step_2_script' && 'Import Script files first'}
                        {key === 'step_3_novel' && 'Import Novel files first'}
                        {key === 'step_4_alignment' && 'Complete Script and Novel analysis first'}
                      </p>
                    )}
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>

      {/* Next Steps */}
      {phaseState.overall_status === 'ready' && (
        <Card className="border-blue-200 bg-blue-50 dark:bg-blue-950">
          <CardContent className="pt-6">
            <div className="flex items-start gap-3">
              <Clock className="h-5 w-5 text-blue-600 dark:text-blue-400 mt-0.5" />
              <div>
                <p className="font-semibold text-blue-900 dark:text-blue-100">Next Steps</p>
                <p className="text-sm text-blue-700 dark:text-blue-300 mt-1">
                  Import Novel and Script files to begin processing
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
