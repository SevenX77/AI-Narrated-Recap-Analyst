/**
 * Step4AlignmentPage - Script-Novel Alignment
 * Sentence-level alignment with non-linear visualization
 */
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Separator } from '@/components/ui/separator'
import type { Step4AlignmentState } from '@/types/workflow'
import { Eye, Download, ChevronRight, Maximize2 } from 'lucide-react'
import { useState } from 'react'
import { cn } from '@/lib/utils'
import { AlignmentSankeyDiagram } from '@/components/workflow/AlignmentSankeyDiagram'
import { useQuery } from '@tanstack/react-query'
import { projectsApiV2 } from '@/api/projectsV2'
import { Spinner } from '@/components/ui/spinner'

interface Step4AlignmentPageProps {
  projectId: string
  stepState: Step4AlignmentState
  onStart?: () => void
}

interface AlignmentPair {
  scriptSentenceId: number
  scriptText: string
  scriptTimestamp: string
  novelParagraphId: number
  novelText: string
  matchConfidence: number
  strategy: 'exact' | 'paraphrase' | 'summarize' | 'expand'
  scriptCategory: 'A' | 'B' | 'C'
  novelCategory: 'A' | 'B' | 'C'
}

// ❌ 删除 mockAlignments（使用真实数据）
// const mockAlignments = [...]

const strategyColors = {
  exact: 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300',
  paraphrase: 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300',
  summarize: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300',
  expand: 'bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300',
}

const categoryColors = {
  A: 'bg-blue-500',
  B: 'bg-green-500',
  C: 'bg-purple-500',
}

function AlignmentPairRow({ pair }: { pair: AlignmentPair }) {
  const [showDetails, setShowDetails] = useState(false)
  const isNonLinear = pair.novelParagraphId > pair.scriptSentenceId + 3

  return (
    <Card>
      <CardContent className="pt-6">
        <div className="grid grid-cols-[1fr_auto_1fr] gap-4">
          {/* Script Sentence */}
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="text-xs">
                Sentence {pair.scriptSentenceId}
              </Badge>
              <Badge className={cn('text-xs text-white', categoryColors[pair.scriptCategory])}>
                {pair.scriptCategory}
              </Badge>
              <span className="text-xs text-muted-foreground">{pair.scriptTimestamp}</span>
            </div>
            <p className="text-sm">{pair.scriptText}</p>
          </div>

          {/* Connection */}
          <div className="flex flex-col items-center justify-center gap-1 px-4">
            <ChevronRight className="h-4 w-4 text-primary" />
            <Progress value={pair.matchConfidence} className="h-1 w-16" />
            <span className="text-xs font-mono">{pair.matchConfidence}%</span>
            <Badge className={cn('text-xs', strategyColors[pair.strategy])} variant="outline">
              {pair.strategy}
            </Badge>
            {isNonLinear && (
              <Badge variant="destructive" className="text-xs">
                Jump
              </Badge>
            )}
          </div>

          {/* Novel Paragraph */}
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="text-xs">
                Para {pair.novelParagraphId}
              </Badge>
              <Badge className={cn('text-xs text-white', categoryColors[pair.novelCategory])}>
                {pair.novelCategory}
              </Badge>
              {pair.scriptCategory !== pair.novelCategory && (
                <Badge variant="outline" className="text-xs text-orange-600">
                  Type Mismatch
                </Badge>
              )}
            </div>
            <p className="text-sm">{pair.novelText}</p>
          </div>
        </div>

        <div className="mt-4">
          <Button variant="ghost" size="sm" onClick={() => setShowDetails(!showDetails)}>
            <Eye className="h-3 w-3 mr-2" />
            {showDetails ? 'Hide' : 'Show'} Details
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

function NovelParagraphGap({ paragraphId, reason }: { paragraphId: number; reason: string }) {
  return (
    <Card className="border-2 border-dashed border-orange-400 bg-orange-50 dark:bg-orange-950">
      <CardContent className="pt-6">
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="text-xs">
            Para {paragraphId}
          </Badge>
          <Badge variant="outline" className="text-xs text-orange-600">
            Gap
          </Badge>
        </div>
        <p className="text-sm text-orange-700 dark:text-orange-300 mt-2">{reason}</p>
      </CardContent>
    </Card>
  )
}

export function Step4AlignmentPage({ projectId, stepState }: Step4AlignmentPageProps) {
  // 获取对齐对列表
  const { data: pairs } = useQuery({
    queryKey: ['alignment-pairs', projectId],
    queryFn: () => projectsApiV2.getAlignmentPairs(projectId),
    enabled: stepState.status === 'completed',
  })

  // 默认选择第一对
  const firstPair = pairs?.pairs?.[0]
  
  // 获取对齐详情（假设为第一对）
  const { data: alignmentData, isLoading } = useQuery({
    queryKey: ['alignment-result', projectId, firstPair?.chapter_id, firstPair?.episode_id],
    queryFn: () => projectsApiV2.getAlignmentResult(projectId, firstPair!.chapter_id, firstPair!.episode_id),
    enabled: !!firstPair && stepState.status === 'completed',
  })

  // 如果正在加载数据，显示loading
  if (stepState.status === 'completed' && isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Spinner size="lg" />
      </div>
    )
  }

  // 使用真实数据或显示占位符
  const alignments = alignmentData?.alignments || []
  
  const displaySequence: Array<{ type: 'alignment' | 'gap'; data: any }> = []
  let lastNovelId = 0

  alignments.forEach((alignment: any) => {
    if (alignment.novelParagraphId > lastNovelId + 1) {
      for (let i = lastNovelId + 1; i < alignment.novelParagraphId; i++) {
        displaySequence.push({
          type: 'gap',
          data: {
            paragraphId: i,
            reason: 'This paragraph is skipped (may correspond to other script sentences or unused)',
          },
        })
      }
    }
    displaySequence.push({ type: 'alignment', data: alignment })
    lastNovelId = alignment.novelParagraphId
  })

  return (
    <div className="flex flex-1 flex-col gap-4 overflow-auto">
      <div className="px-2">
        <h2 className="text-3xl font-bold tracking-tight">Step 4: Script-Novel Alignment</h2>
        <p className="text-muted-foreground">Sentence-level alignment with non-linear visualization</p>
      </div>

      {/* Statistics Card */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Alignment Completed</CardTitle>
              <CardDescription>ep01 ↔ Chapters 1-3</CardDescription>
            </div>
            <Button variant="outline">
              <Download className="h-4 w-4 mr-2" />
              Export Results
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <Progress value={85} className="h-2" />
          <div className="grid grid-cols-5 gap-4 text-sm">
            <div>
              <p className="text-muted-foreground">Match Rate</p>
              <p className="text-2xl font-bold">85%</p>
            </div>
            <div>
              <p className="text-muted-foreground">Event Coverage</p>
              <p className="text-xl font-bold">{(stepState.event_coverage_rate ?? 92).toFixed(0)}%</p>
            </div>
            <div>
              <p className="text-muted-foreground">Setting Coverage</p>
              <p className="text-xl font-bold">{(stepState.setting_coverage_rate ?? 78).toFixed(0)}%</p>
            </div>
            <div>
              <p className="text-muted-foreground">Avg Confidence</p>
              <p className="text-xl font-bold">{(stepState.average_match_confidence ?? 0.88).toFixed(2)}</p>
            </div>
            <div>
              <p className="text-muted-foreground">Total Pairs</p>
              <p className="text-xl font-bold">{stepState.total_alignments}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Separator />

      {/* Adaptation Strategy Distribution */}
      <Card>
        <CardHeader>
          <CardTitle>Adaptation Strategy Distribution</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-4 gap-4">
            {[
              { strategy: 'exact', label: 'Exact', value: 10, color: strategyColors.exact },
              { strategy: 'paraphrase', label: 'Paraphrase', value: 70, color: strategyColors.paraphrase },
              { strategy: 'summarize', label: 'Summarize', value: 15, color: strategyColors.summarize },
              { strategy: 'expand', label: 'Expand', value: 5, color: strategyColors.expand },
            ].map((item) => (
              <div key={item.strategy} className="space-y-2">
                <Badge className={item.color}>{item.label}</Badge>
                <Progress value={item.value} className="h-2" />
                <p className="text-xs text-muted-foreground">{item.value}%</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Separator />

      {/* Sankey Diagram */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">Alignment Flow Visualization</h3>
          <Button variant="outline" size="sm">
            <Maximize2 className="h-3 w-3 mr-2" />
            Fullscreen
          </Button>
        </div>

        <AlignmentSankeyDiagram
          novelNodes={[
            { id: 'novel_1', label: 'Para 1', text: 'He walked into the room...', category: 'B' },
            { id: 'novel_2', label: 'Para 2', text: 'He saw a letter on the table...', category: 'B' },
            { id: 'novel_3', label: 'Para 3', text: 'Gap (skipped)', category: 'B', isGap: true },
            { id: 'novel_4', label: 'Para 4', text: 'World setting explanation...', category: 'A' },
            { id: 'novel_5', label: 'Para 5', text: 'He suddenly remembered...', category: 'B' },
          ]}
          scriptNodes={[
            { id: 'script_1', label: 'S1', text: 'Protagonist enters room', category: 'B' },
            { id: 'script_2', label: 'S2', text: 'He discovers a letter', category: 'B' },
            { id: 'script_3', label: 'S3', text: 'In this world...', category: 'A' },
            { id: 'script_4', label: 'S4', text: 'He recalls the past', category: 'B' },
          ]}
          links={[
            { source: 'novel_1', target: 'script_1', confidence: 92, strategy: 'paraphrase' },
            { source: 'novel_2', target: 'script_2', confidence: 88, strategy: 'paraphrase' },
            { source: 'novel_4', target: 'script_3', confidence: 95, strategy: 'exact' },
            { source: 'novel_5', target: 'script_4', confidence: 75, strategy: 'summarize' },
          ]}
          onNodeClick={(nodeId, type) => {
            console.log(`Clicked ${type} node: ${nodeId}`)
          }}
        />
      </div>

      <Separator />

      {/* Alignment Pairs */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold">Alignment Details (Sentence-level)</h3>

        <Card className="border-blue-200 bg-blue-50 dark:bg-blue-950">
          <CardContent className="pt-6">
            <div className="text-sm space-y-1">
              <p className="font-semibold">Non-linear Alignment Legend:</p>
              <p className="text-muted-foreground">• Orange Gap: Novel paragraph skipped</p>
              <p className="text-muted-foreground">• Jump Badge: Current script sentence corresponds to non-sequential novel paragraph</p>
              <p className="text-muted-foreground">• Unmatched novel paragraphs are preserved (not omitted)</p>
            </div>
          </CardContent>
        </Card>

        <div className="space-y-3">
          {displaySequence.map((item, index) => (
            <div key={index}>
              {item.type === 'alignment' ? (
                <AlignmentPairRow pair={item.data} />
              ) : (
                <NovelParagraphGap paragraphId={item.data.paragraphId} reason={item.data.reason} />
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Statistics Report */}
      <Card>
        <CardHeader>
          <CardTitle>Statistics Report</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-muted-foreground">Perfect Match {'>'}=90%:</span>
            <span className="font-mono font-semibold">5 paragraphs</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Good Match 70-90%:</span>
            <span className="font-mono font-semibold">3 paragraphs</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Low Match {'(<'}70%):</span>
            <span className="font-mono font-semibold">0</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Novel Uncovered:</span>
            <span className="font-mono font-semibold">2 paragraphs (Para 7, 9)</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Script Original:</span>
            <span className="font-mono font-semibold">1 (Hook section)</span>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
