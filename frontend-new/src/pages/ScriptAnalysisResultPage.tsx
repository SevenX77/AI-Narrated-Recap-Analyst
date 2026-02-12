/**
 * Script Analysis Result Page
 * 显示Script分析的详细结果（分段、Hook、质量报告）
 */
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { projectsApiV2 } from '@/api/projectsV2'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Spinner } from '@/components/ui/spinner'
import { ArrowLeft, CheckCircle, AlertCircle } from 'lucide-react'
import { cn } from '@/lib/utils'

export default function ScriptAnalysisResultPage() {
  const { projectId, episodeId } = useParams<{ projectId: string; episodeId: string }>()
  const navigate = useNavigate()

  if (!projectId || !episodeId) {
    return <div>Missing project ID or episode ID</div>
  }

  // 获取分段结果
  const { data: segmentation, isLoading: segmentationLoading } = useQuery({
    queryKey: ['script-segmentation', projectId, episodeId],
    queryFn: () => projectsApiV2.getScriptSegmentation(projectId, episodeId),
  })

  // 获取Hook检测结果（仅ep01）
  const { data: hook } = useQuery({
    queryKey: ['script-hook', projectId, episodeId],
    queryFn: () => projectsApiV2.getScriptHook(projectId, episodeId),
    enabled: episodeId === 'ep01',
  })

  // 获取质量报告
  const { data: validation } = useQuery({
    queryKey: ['script-validation', projectId, episodeId],
    queryFn: () => projectsApiV2.getScriptValidation(projectId, episodeId),
  })

  const categoryColors = {
    A: 'bg-blue-500',
    B: 'bg-green-500',
    C: 'bg-purple-500',
  }

  if (segmentationLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Spinner size="lg" />
      </div>
    )
  }

  if (!segmentation) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen gap-4">
        <AlertCircle className="h-12 w-12 text-muted-foreground" />
        <p className="text-muted-foreground">Segmentation result not found</p>
        <Button onClick={() => navigate(`/project/${projectId}/workflow`)}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Workflow
        </Button>
      </div>
    )
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => navigate(`/project/${projectId}/workflow`)}
        >
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div>
          <h1 className="text-3xl font-bold">Script Analysis Result</h1>
          <p className="text-muted-foreground">Episode: {episodeId}</p>
        </div>
      </div>

      {/* Hook Detection (ep01 only) */}
      {hook && episodeId === 'ep01' && (
        <Card>
          <CardHeader>
            <CardTitle>Hook Detection</CardTitle>
            <CardDescription>Opening hook analysis for first episode</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                {hook.has_hook ? (
                  <>
                    <CheckCircle className="h-5 w-5 text-green-500" />
                    <span className="font-medium">Hook Detected</span>
                  </>
                ) : (
                  <>
                    <AlertCircle className="h-5 w-5 text-yellow-500" />
                    <span className="font-medium">No Hook Detected</span>
                  </>
                )}
              </div>
              {hook.has_hook && (
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-muted-foreground">Hook End Time</p>
                    <p className="text-lg font-semibold">{hook.hook_end_time}s</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Confidence</p>
                    <p className="text-lg font-semibold">
                      {(hook.confidence * 100).toFixed(0)}%
                    </p>
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* ABC Distribution */}
      <Card>
        <CardHeader>
          <CardTitle>ABC Distribution</CardTitle>
          <CardDescription>Segment category breakdown</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4">
            {['A', 'B', 'C'].map((category) => {
              const count = segmentation.abc_distribution?.[category] || 0
              const percentage =
                segmentation.total_segments > 0
                  ? ((count / segmentation.total_segments) * 100).toFixed(1)
                  : 0
              return (
                <div key={category} className="text-center space-y-2">
                  <Badge
                    className={cn(
                      'text-white text-lg px-4 py-2',
                      categoryColors[category as keyof typeof categoryColors]
                    )}
                  >
                    {category}
                  </Badge>
                  <div>
                    <p className="text-2xl font-bold">{count}</p>
                    <p className="text-sm text-muted-foreground">{percentage}%</p>
                  </div>
                </div>
              )
            })}
          </div>
        </CardContent>
      </Card>

      {/* Quality Report */}
      {validation && (
        <Card>
          <CardHeader>
            <CardTitle>Quality Report</CardTitle>
            <CardDescription>Validation results and suggestions</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <p className="text-sm text-muted-foreground">Quality Score</p>
                <p className="text-3xl font-bold">{validation.quality_score}/100</p>
              </div>
              {validation.issues && validation.issues.length > 0 && (
                <div>
                  <p className="text-sm font-medium mb-2">Issues Found</p>
                  <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground">
                    {validation.issues.map((issue: string, index: number) => (
                      <li key={index}>{issue}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Segment List */}
      <Card>
        <CardHeader>
          <CardTitle>Segments ({segmentation.total_segments})</CardTitle>
          <CardDescription>Detailed segment breakdown with timestamps</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {segmentation.segments?.map((segment: any) => (
              <div
                key={segment.segment_id}
                className="flex gap-4 p-3 rounded-lg border hover:bg-accent/50 transition-colors"
              >
                <Badge
                  className={cn(
                    'h-6 text-white',
                    categoryColors[segment.category as keyof typeof categoryColors]
                  )}
                >
                  {segment.category}
                </Badge>
                <div className="flex-1 min-w-0">
                  <p className="text-sm leading-relaxed">{segment.content}</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    {segment.start_time.toFixed(1)}s - {segment.end_time.toFixed(1)}s
                  </p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
