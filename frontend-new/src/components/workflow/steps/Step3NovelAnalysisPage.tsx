/**
 * Step3NovelAnalysisPage - Novel Analysis
 */
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { Separator } from '@/components/ui/separator'
import { LogViewer, type LogEntry } from '@/components/workflow/LogViewer'
import type { Step3NovelAnalysisState } from '@/types/workflow'
import { Play, Pause, XCircle, FileText, List, Tags, Zap, Database, Eye } from 'lucide-react'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

interface Step3NovelAnalysisPageProps {
  projectId: string
  stepState: Step3NovelAnalysisState
  onStart?: () => void
  onPause?: () => void
  onCancel?: () => void
}

export function Step3NovelAnalysisPage({ projectId, stepState, onStart, onPause, onCancel }: Step3NovelAnalysisPageProps) {
  const [logs] = useState<LogEntry[]>([])
  const navigate = useNavigate()

  return (
    <div className="flex flex-1 flex-col gap-4 overflow-auto">
      <div className="px-2">
        <h2 className="text-3xl font-bold tracking-tight">Step 3: Novel Analysis</h2>
        <p className="text-muted-foreground">Analyze novel content through 8 processing steps</p>
      </div>

      {/* Progress Card */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Processing Status</CardTitle>
              <CardDescription>
                {stepState.status === 'completed' ? 'Analysis completed' : stepState.status === 'running' ? 'Processing...' : 'Ready to start'}
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              {stepState.status === 'completed' && (
                <Button variant="outline" onClick={() => navigate(`/project/${projectId}/novel-analysis`)}>
                  <Eye className="h-4 w-4 mr-2" />
                  View Results
                </Button>
              )}
              {stepState.status !== 'running' ? (
                <Button onClick={onStart}>
                  <Play className="h-4 w-4 mr-2" />
                  Start Analysis
                </Button>
              ) : (
                <>
                  <Button variant="outline" onClick={onPause}>
                    <Pause className="h-4 w-4 mr-2" />
                    Pause
                  </Button>
                  <Button variant="destructive" onClick={onCancel}>
                    <XCircle className="h-4 w-4 mr-2" />
                    Cancel
                  </Button>
                </>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <Progress value={stepState.overall_progress} className="h-2" />
          <div className="grid grid-cols-4 gap-4 text-sm">
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
            <div>
              <p className="text-muted-foreground">Quality Score</p>
              <p className="text-xl font-bold">{stepState.quality_score ? `${stepState.quality_score}/100` : '-'}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Separator />

      {/* Key Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <List className="h-4 w-4" />
              Chapters
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{stepState.total_chapters}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <FileText className="h-4 w-4" />
              Paragraphs
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{stepState.total_paragraphs}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Zap className="h-4 w-4" />
              Events
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{stepState.total_events}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Tags className="h-4 w-4" />
              Settings
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{stepState.total_settings}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Database className="h-4 w-4" />
              System Elements
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{stepState.total_system_elements}</p>
          </CardContent>
        </Card>

        <Card className="border-primary">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Actions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <Button variant="outline" size="sm" className="w-full">
              View Event Timeline
            </Button>
            <Button variant="outline" size="sm" className="w-full">
              View Setting Library
            </Button>
          </CardContent>
        </Card>
      </div>

      {logs.length > 0 && (
        <>
          <Separator />
          <LogViewer logs={logs} maxHeight="400px" autoScroll={true} />
        </>
      )}
    </div>
  )
}
