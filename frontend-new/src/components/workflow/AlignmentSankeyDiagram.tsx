/**
 * AlignmentSankeyDiagram - 对齐桑基图可视化
 * 展示 Novel 段落 → Script 句子的非线性对齐流向
 * 
 * 特性：
 * - 粗细表示匹配度
 * - 颜色表示类型 (A/B/C)
 * - 支持非线性连接
 * - 交互：悬停显示详情，点击跳转
 */
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

interface AlignmentNode {
  id: string
  label: string
  text: string
  category: 'A' | 'B' | 'C'
  isGap?: boolean
}

interface AlignmentLink {
  source: string // Novel paragraph ID
  target: string // Script sentence ID
  confidence: number // 0-100
  strategy: 'exact' | 'paraphrase' | 'summarize' | 'expand'
}

interface AlignmentSankeyDiagramProps {
  novelNodes: AlignmentNode[]
  scriptNodes: AlignmentNode[]
  links: AlignmentLink[]
  onNodeClick?: (nodeId: string, type: 'novel' | 'script') => void
}

const categoryColors = {
  A: { bg: 'bg-blue-100 dark:bg-blue-900', border: 'border-blue-500', text: 'text-blue-700 dark:text-blue-300' },
  B: { bg: 'bg-green-100 dark:bg-green-900', border: 'border-green-500', text: 'text-green-700 dark:text-green-300' },
  C: { bg: 'bg-purple-100 dark:bg-purple-900', border: 'border-purple-500', text: 'text-purple-700 dark:text-purple-300' },
}

function NodeCard({
  node,
  onClick,
}: {
  node: AlignmentNode
  type: 'novel' | 'script'
  onClick?: () => void
}) {
  const colors = categoryColors[node.category]

  if (node.isGap) {
    return (
      <div className="border-2 border-dashed border-orange-300 rounded-lg p-2 bg-orange-50 dark:bg-orange-950 min-h-[60px] flex items-center justify-center">
        <p className="text-xs text-orange-600">空档</p>
      </div>
    )
  }

  return (
    <div
      className={cn(
        'border-2 rounded-lg p-3 min-h-[80px] cursor-pointer transition-all hover:shadow-md',
        colors.bg,
        colors.border,
        'hover:scale-105'
      )}
      onClick={onClick}
    >
      <div className="flex items-center gap-2 mb-1">
        <Badge variant="outline" className="text-xs">
          {node.label}
        </Badge>
        <Badge variant="outline" className="text-xs">
          {node.category}类
        </Badge>
      </div>
      <p className={cn('text-xs line-clamp-2', colors.text)}>{node.text}</p>
    </div>
  )
}

function ConnectionLine({
  confidence,
  strategy,
  isNonLinear,
}: {
  confidence: number
  strategy: string
  isNonLinear: boolean
}) {
  const strokeWidth = confidence >= 90 ? 4 : confidence >= 70 ? 2 : 1
  const strokeColor =
    confidence >= 90
      ? 'stroke-green-500'
      : confidence >= 70
      ? 'stroke-blue-500'
      : 'stroke-orange-400'
  const strokeDasharray = confidence < 70 ? '5,5' : '0'

  return (
    <div className="flex items-center justify-center">
      <svg width="60" height="4" className="overflow-visible">
        <line
          x1="0"
          y1="2"
          x2="60"
          y2="2"
          className={strokeColor}
          strokeWidth={strokeWidth}
          strokeDasharray={strokeDasharray}
        />
        {isNonLinear && (
          <circle cx="30" cy="2" r="6" className="fill-red-500" />
        )}
      </svg>
      <div className="text-xs text-center mx-2">
        <p className="font-mono font-semibold">{confidence}%</p>
        <p className="text-muted-foreground">{strategy}</p>
      </div>
    </div>
  )
}

export function AlignmentSankeyDiagram({
  novelNodes,
  scriptNodes,
  links,
  onNodeClick,
}: AlignmentSankeyDiagramProps) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-base">🌊 对齐流向图 (桑基图)</CardTitle>
          <div className="flex items-center gap-4 text-xs">
            <div className="flex items-center gap-1">
              <div className="w-3 h-1 bg-green-500" />
              <span className="text-muted-foreground">高匹配 (≥90%)</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-2 h-1 bg-blue-500" />
              <span className="text-muted-foreground">中匹配 (70-89%)</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-1 h-1 bg-orange-400" />
              <span className="text-muted-foreground">低匹配 {'(<'}70%)</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-2 h-2 rounded-full bg-red-500" />
              <span className="text-muted-foreground">非线性跳转</span>
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="overflow-auto">
          {/* 三列布局：Novel | 连接线 | Script */}
          <div className="grid grid-cols-[1fr_auto_1fr] gap-4 min-w-[900px]">
            {/* Novel 列 */}
            <div className="space-y-3">
              <h4 className="text-sm font-semibold text-center mb-4">📖 Novel 段落</h4>
              {novelNodes.map((node) => (
                <NodeCard
                  key={node.id}
                  node={node}
                  type="novel"
                  onClick={() => onNodeClick?.(node.id, 'novel')}
                />
              ))}
            </div>

            {/* 连接线列 */}
            <div className="space-y-3 pt-12">
              {links.map((link, index) => {
                const prevLink = index > 0 ? links[index - 1] : null
                const sourceIdNum = parseInt(link.source.replace('novel_', ''))
                const prevSourceIdNum = prevLink ? parseInt(prevLink.source.replace('novel_', '')) : 0
                const isNonLinear = sourceIdNum > prevSourceIdNum + 1

                return (
                  <div key={`${link.source}-${link.target}`} className="h-[80px] flex items-center">
                    <ConnectionLine
                      confidence={link.confidence}
                      strategy={link.strategy}
                      isNonLinear={isNonLinear}
                    />
                  </div>
                )
              })}
            </div>

            {/* Script 列 */}
            <div className="space-y-3">
              <h4 className="text-sm font-semibold text-center mb-4">📺 Script 句子</h4>
              {scriptNodes.map((node) => (
                <NodeCard
                  key={node.id}
                  node={node}
                  type="script"
                  onClick={() => onNodeClick?.(node.id, 'script')}
                />
              ))}
            </div>
          </div>
        </div>

        {/* 图例说明 */}
        <div className="mt-6 p-3 bg-muted rounded-lg">
          <p className="text-xs text-muted-foreground">
            💡 提示：连接线的粗细代表匹配置信度，红点表示非线性跳转（Novel 段落不连续）。
            橙色空档表示被跳过的 Novel 段落。
          </p>
        </div>
      </CardContent>
    </Card>
  )
}

// 导出一个使用示例的包装组件
export function AlignmentSankeyExample() {
  // 模拟数据
  const novelNodes: AlignmentNode[] = [
    { id: 'novel_1', label: '段落 1', text: 'Novel 第1段：李明走进房间...', category: 'B' },
    { id: 'novel_2', label: '段落 2', text: 'Novel 第2段：他看到桌上的信...', category: 'B' },
    { id: 'novel_3', label: '段落 3', text: 'Novel 第3段：空档（被跳过）', category: 'B', isGap: true },
    { id: 'novel_4', label: '段落 4', text: 'Novel 第4段：世界设定说明...', category: 'A' },
    { id: 'novel_5', label: '段落 5', text: 'Novel 第5段：他突然想起...', category: 'B' },
  ]

  const scriptNodes: AlignmentNode[] = [
    { id: 'script_1', label: '句子 1', text: 'Script 句1：男主走进房间', category: 'B' },
    { id: 'script_2', label: '句子 2', text: 'Script 句2：他发现了一封信', category: 'B' },
    { id: 'script_3', label: '句子 3', text: 'Script 句3：在这个世界...', category: 'A' },
    { id: 'script_4', label: '句子 4', text: 'Script 句4：他回忆起往事', category: 'B' },
  ]

  const links: AlignmentLink[] = [
    { source: 'novel_1', target: 'script_1', confidence: 92, strategy: 'paraphrase' },
    { source: 'novel_2', target: 'script_2', confidence: 88, strategy: 'paraphrase' },
    { source: 'novel_4', target: 'script_3', confidence: 95, strategy: 'exact' }, // 非线性跳转
    { source: 'novel_5', target: 'script_4', confidence: 75, strategy: 'summarize' },
  ]

  return (
    <AlignmentSankeyDiagram
      novelNodes={novelNodes}
      scriptNodes={scriptNodes}
      links={links}
      onNodeClick={(nodeId, type) => {
        console.log(`Clicked ${type} node: ${nodeId}`)
      }}
    />
  )
}
