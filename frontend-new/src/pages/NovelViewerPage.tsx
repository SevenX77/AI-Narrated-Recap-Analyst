import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { projectsApiV2 } from '@/api/projectsV2'
import { Spinner } from '@/components/ui/spinner'
import { cn } from '@/lib/utils'
import ReactMarkdown from 'react-markdown'
import { ViewerLayout } from '@/components/layout/ViewerLayout'

export default function NovelViewerPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const [selectedChapter, setSelectedChapter] = useState<number | 'intro' | null>(null)

  if (!projectId) {
    return <div>Project ID not found</div>
  }

  // 获取章节列表
  const { data: chaptersData, isLoading: chaptersLoading } = useQuery({
    queryKey: ['project-chapters', projectId],
    queryFn: () => projectsApiV2.getChapters(projectId),
  })

  // 获取章节或intro内容（markdown格式）
  const { data: chapterContent, isLoading: contentLoading } = useQuery({
    queryKey: ['chapter-content', projectId, selectedChapter],
    queryFn: async () => {
      if (!selectedChapter) return null
      
      if (selectedChapter === 'intro') {
        // 获取 intro.md
        const response = await fetch(`http://localhost:8000/data/projects/${projectId}/analyst/import/novel/intro.md`)
        if (!response.ok) return null
        return response.text()
      } else {
        // 获取章节内容（从 novel-imported.md 中提取）
        const response = await fetch(`http://localhost:8000/data/projects/${projectId}/analyst/import/novel/novel-imported.md`)
        if (!response.ok) return null
        const fullContent = await response.text()
        
        // 按章节分割
        const chapterRegex = /^# 第(\d+)章/gm
        const matches = [...fullContent.matchAll(chapterRegex)]
        
        const currentChapterMatch = matches.find(m => parseInt(m[1]) === selectedChapter)
        if (!currentChapterMatch) return null
        
        const startIdx = currentChapterMatch.index!
        const nextChapterMatch = matches.find(m => parseInt(m[1]) === selectedChapter + 1)
        const endIdx = nextChapterMatch?.index ?? fullContent.length
        
        return fullContent.slice(startIdx, endIdx).trim()
      }
    },
    enabled: !!selectedChapter,
  })

  // 自动选择 intro
  if (chaptersData && !selectedChapter && chaptersData.chapters.length > 0) {
    setSelectedChapter('intro')
  }

  const totalChapters = chaptersData?.chapters.length || 0

  // 导航内容
  const navContent = chaptersLoading ? (
    <div className="flex items-center justify-center py-8">
      <Spinner size="sm" />
    </div>
  ) : chaptersData && chaptersData.chapters.length > 0 ? (
    <div className="space-y-0.5 p-2 pt-5 pb-5">
      {/* Introduction 选项 */}
      <button
        type="button"
        onClick={() => setSelectedChapter('intro')}
        className={cn(
          'w-full text-left px-2 py-1.5 rounded-sm text-sm transition-all',
          selectedChapter === 'intro'
            ? 'bg-accent text-accent-foreground font-medium'
            : 'hover:bg-accent/50 text-muted-foreground hover:text-foreground'
        )}
      >
        <div className="flex items-baseline gap-1.5">
          <span className="flex-shrink-0">Introduction</span>
        </div>
      </button>
      
      {/* 分隔线 */}
      <div className="h-px bg-border my-2" />
      
      {/* 章节列表 */}
      {chaptersData.chapters.map((chapter) => (
        <button
          key={chapter.chapter_number}
          type="button"
          data-chapter={chapter.chapter_number}
          onClick={() => setSelectedChapter(chapter.chapter_number)}
          className={cn(
            'w-full text-left px-2 py-1.5 rounded-sm text-sm transition-all',
            selectedChapter === chapter.chapter_number
              ? 'bg-accent text-accent-foreground font-medium'
              : 'hover:bg-accent/50 text-muted-foreground hover:text-foreground'
          )}
        >
          <div className="flex items-baseline gap-1.5">
            <span className="flex-shrink-0">Ch.{chapter.chapter_number}</span>
            {chapter.title && (
              <span className="truncate text-xs opacity-90">{chapter.title}</span>
            )}
          </div>
        </button>
      ))}
    </div>
  ) : (
    <div className="p-4 text-sm text-muted-foreground text-center">
      No chapters found
    </div>
  )

  // 主内容
  const mainContent = contentLoading ? (
    <div className="flex items-center justify-center py-16">
      <Spinner size="lg" />
    </div>
  ) : chapterContent ? (
    <article className="prose prose-gray dark:prose-invert max-w-none">
      <ReactMarkdown
        components={{
          h1: ({ ...props }) => (
            <h1 className="scroll-m-20 text-4xl font-extrabold tracking-tight text-balance mb-8" {...props} />
          ),
          p: ({ ...props }) => (
            <p className="leading-7 [&:not(:first-child)]:mt-6" {...props} />
          ),
        }}
      >
        {chapterContent}
      </ReactMarkdown>
    </article>
  ) : (
    <div className="flex items-center justify-center h-full text-sm text-muted-foreground">
      Select a chapter to view
    </div>
  )

  return (
    <ViewerLayout
      navTitle="Chapters"
      navContent={navContent}
      mainContent={mainContent}
      currentIndex={typeof selectedChapter === 'number' ? selectedChapter - 1 : -1}
      totalCount={totalChapters}
      currentLabel={selectedChapter === 'intro' ? 'Intro' : undefined}
    />
  )
}
