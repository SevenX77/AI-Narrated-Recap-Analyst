/**
 * Novel Analysis Result Page
 * 显示Novel分析的详细结果（分段、标注、系统元素）
 */
import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { projectsApiV2 } from '@/api/projectsV2'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Spinner } from '@/components/ui/spinner'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion'
import { ArrowLeft, CheckCircle, Clock, List, Tags, Zap, Database } from 'lucide-react'
import { cn } from '@/lib/utils'

export default function NovelAnalysisResultPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const navigate = useNavigate()
  const [selectedChapter, setSelectedChapter] = useState<string>('chapter_001')

  if (!projectId) {
    return <div>Missing project ID</div>
  }

  // 获取章节列表
  const { data: chaptersData, isLoading: chaptersLoading } = useQuery({
    queryKey: ['novel-chapters', projectId],
    queryFn: () => projectsApiV2.getNovelAnalysisChapters(projectId),
  })

  // 获取分段结果
  const { data: segmentation } = useQuery({
    queryKey: ['novel-segmentation', projectId, selectedChapter],
    queryFn: () => projectsApiV2.getNovelSegmentation(projectId, selectedChapter),
    enabled: !!selectedChapter,
  })

  // 获取标注结果
  const { data: annotation } = useQuery({
    queryKey: ['novel-annotation', projectId, selectedChapter],
    queryFn: () => projectsApiV2.getNovelAnnotation(projectId, selectedChapter),
    enabled: !!selectedChapter,
  })

  // 获取系统目录
  const { data: systemCatalog } = useQuery({
    queryKey: ['system-catalog', projectId],
    queryFn: () => projectsApiV2.getSystemCatalog(projectId),
  })

  // 自动选择第一章
  if (chaptersData && !selectedChapter && chaptersData.chapters.length > 0) {
    setSelectedChapter(chaptersData.chapters[0].chapter_id)
  }

  if (chaptersLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Spinner size="lg" />
      </div>
    )
  }

  return (
    <div className="flex h-screen">
      {/* Left Sidebar: Chapter List */}
      <div className="w-64 border-r bg-muted/10 flex flex-col">
        <div className="p-4 border-b">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate(`/project/${projectId}/workflow`)}
            className="w-full justify-start"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Workflow
          </Button>
        </div>

        <div className="flex-1 overflow-auto p-2">
          <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide px-2 py-2">
            Chapters
          </h3>
          {chaptersLoading ? (
            <div className="flex justify-center py-8">
              <Spinner size="sm" />
            </div>
          ) : (
            <div className="space-y-1">
              {chaptersData?.chapters.map((chapter: any) => (
                <button
                  key={chapter.chapter_id}
                  onClick={() => setSelectedChapter(chapter.chapter_id)}
                  className={cn(
                    'w-full text-left px-3 py-2 rounded-md text-sm transition-colors',
                    selectedChapter === chapter.chapter_id
                      ? 'bg-accent text-accent-foreground font-medium'
                      : 'hover:bg-accent/50 text-muted-foreground'
                  )}
                >
                  <div className="flex items-center gap-2">
                    {chapter.status === 'completed' ? (
                      <CheckCircle className="h-3 w-3 text-green-500" />
                    ) : (
                      <Clock className="h-3 w-3" />
                    )}
                    <span className="truncate flex-1">{chapter.chapter_title}</span>
                  </div>
                  {chapter.quality_score && (
                    <div className="text-xs text-muted-foreground mt-1">
                      Quality: {chapter.quality_score}/100
                    </div>
                  )}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Right Content: Tabs */}
      <div className="flex-1 overflow-auto p-6">
        <Tabs defaultValue="segmentation" className="space-y-4">
          <TabsList>
            <TabsTrigger value="segmentation">
              <List className="h-4 w-4 mr-2" />
              Segmentation
            </TabsTrigger>
            <TabsTrigger value="annotation">
              <Tags className="h-4 w-4 mr-2" />
              Annotation
            </TabsTrigger>
            <TabsTrigger value="system">
              <Database className="h-4 w-4 mr-2" />
              System Elements
            </TabsTrigger>
          </TabsList>

          {/* Tab 1: Segmentation */}
          <TabsContent value="segmentation" className="space-y-4">
            {/* Category Distribution */}
            {segmentation?.category_distribution && (
              <Card>
                <CardHeader>
                  <CardTitle>Paragraph Distribution</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-wrap gap-3">
                    {Object.entries(segmentation.category_distribution).map(([category, count]) => {
                      const total = segmentation.total_paragraphs || 1
                      const percentage = ((count as number / total) * 100).toFixed(1)
                      return (
                        <Badge key={category} variant="outline" className="text-sm py-1 px-3">
                          {category}: {count as number} ({percentage}%)
                        </Badge>
                      )
                    })}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Paragraph List */}
            <Card>
              <CardHeader>
                <CardTitle>Paragraphs ({segmentation?.total_paragraphs || 0})</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {segmentation?.paragraphs?.map((paragraph: any) => (
                    <div
                      key={paragraph.paragraph_id}
                      className="p-3 rounded-lg border hover:bg-accent/30 transition-colors"
                    >
                      <div className="flex items-start gap-3">
                        <Badge variant="outline" className="text-xs">
                          {paragraph.paragraph_id}
                        </Badge>
                        <Badge variant="secondary" className="text-xs">
                          {paragraph.category}
                        </Badge>
                        <p className="text-sm leading-relaxed flex-1">{paragraph.content}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Tab 2: Annotation */}
          <TabsContent value="annotation" className="space-y-4">
            {/* Event Timeline */}
            <Card>
              <CardHeader>
                <CardTitle>
                  <Zap className="h-5 w-5 inline mr-2" />
                  Event Timeline ({annotation?.event_timeline?.length || 0})
                </CardTitle>
                <CardDescription>Key events extracted from the chapter</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {annotation?.event_timeline?.map((event: any) => (
                    <div
                      key={event.event_id}
                      className="p-4 rounded-lg border-l-4 border-blue-500 bg-accent/20"
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1">
                          <p className="font-medium">{event.description}</p>
                          <div className="flex flex-wrap gap-2 mt-2 text-xs text-muted-foreground">
                            {event.timestamp && (
                              <span>📅 {event.timestamp}</span>
                            )}
                            {event.location && (
                              <span>📍 {event.location}</span>
                            )}
                            {event.participants && event.participants.length > 0 && (
                              <span>👥 {event.participants.join(', ')}</span>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Setting Library */}
            <Card>
              <CardHeader>
                <CardTitle>
                  <Tags className="h-5 w-5 inline mr-2" />
                  Setting Library ({annotation?.setting_library?.length || 0})
                </CardTitle>
                <CardDescription>World settings and rules</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {annotation?.setting_library?.map((setting: any) => (
                    <div
                      key={setting.setting_id}
                      className="p-4 rounded-lg border bg-muted/30"
                    >
                      <div className="flex items-start gap-3">
                        <Badge variant="outline">{setting.type}</Badge>
                        <p className="text-sm leading-relaxed flex-1">{setting.content}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Tab 3: System Elements */}
          <TabsContent value="system" className="space-y-4">
            {systemCatalog && (
              <Card>
                <CardHeader>
                  <CardTitle>
                    <Database className="h-5 w-5 inline mr-2" />
                    {systemCatalog.system_name || 'System Elements'}
                  </CardTitle>
                  <CardDescription>Categorized system elements catalog</CardDescription>
                </CardHeader>
                <CardContent>
                  <Accordion type="single" collapsible>
                    {systemCatalog.categories &&
                      Object.entries(systemCatalog.categories).map(([categoryName, elements]) => (
                        <AccordionItem key={categoryName} value={categoryName}>
                          <AccordionTrigger>
                            {categoryName.replace(/_/g, ' ')} ({(elements as any[]).length})
                          </AccordionTrigger>
                          <AccordionContent>
                            <div className="space-y-2">
                              {(elements as any[]).map((element: any, index: number) => (
                                <div
                                  key={index}
                                  className="p-3 rounded-md border bg-background"
                                >
                                  <p className="font-medium text-sm">{element.name}</p>
                                  <p className="text-xs text-muted-foreground mt-1">
                                    {element.description}
                                  </p>
                                  {element.first_appearance && (
                                    <p className="text-xs text-muted-foreground mt-1">
                                      First: {element.first_appearance}
                                    </p>
                                  )}
                                </div>
                              ))}
                            </div>
                          </AccordionContent>
                        </AccordionItem>
                      ))}
                  </Accordion>
                </CardContent>
              </Card>
            )}
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}
