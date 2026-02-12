import { useState, useMemo } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { projectsApiV2 } from '@/api/projectsV2'
import { Spinner } from '@/components/ui/spinner'
import { cn } from '@/lib/utils'
import { ViewerLayout } from '@/components/layout/ViewerLayout'

export default function ScriptViewerPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const [selectedEpisode, setSelectedEpisode] = useState<string | null>(null)

  if (!projectId) {
    return <div>Project ID not found</div>
  }

  // 获取集数列表
  const { data: episodesData, isLoading: episodesLoading } = useQuery({
    queryKey: ['project-episodes', projectId],
    queryFn: () => projectsApiV2.getEpisodes(projectId),
  })

  // 获取集数详情（包含entries和processed_text）
  const { data: episodeDetail, isLoading: contentLoading } = useQuery({
    queryKey: ['episode-detail', projectId, selectedEpisode],
    queryFn: () => projectsApiV2.getEpisodeDetail(projectId, selectedEpisode!),
    enabled: !!selectedEpisode,
  })

  // 获取Markdown格式的导入文本（句子级时间标注）
  const { data: importedScript } = useQuery({
    queryKey: ['episode-imported', projectId, selectedEpisode],
    queryFn: () => projectsApiV2.getImportedScript(projectId, selectedEpisode!),
    enabled: !!selectedEpisode,
  })

  // 解析markdown内容为结构化数据
  const parsedMarkdown = useMemo(() => {
    if (!importedScript) return null
    
    const lines = importedScript.split('\n').filter(line => line.trim())
    return lines.map((line, index) => {
      // 解析格式：[00:00:00,000 --> 00:00:02,733] 内容
      const match = line.match(/^\[([^\]]+)\s+-->\s+([^\]]+)\]\s+(.+)$/)
      if (match) {
        return {
          index,
          start_time: match[1],
          end_time: match[2],
          text: match[3]
        }
      }
      return null
    }).filter(Boolean)
  }, [importedScript])

  // 自动选择第一集
  if (episodesData && !selectedEpisode && episodesData.episodes.length > 0) {
    setSelectedEpisode(episodesData.episodes[0].episode_name)
  }

  const totalEpisodes = episodesData?.episodes.length || 0
  const currentIndex = episodesData?.episodes.findIndex(ep => ep.episode_name === selectedEpisode) ?? -1

  // 导航内容
  const navContent = episodesLoading ? (
    <div className="flex items-center justify-center py-8">
      <Spinner size="sm" />
    </div>
  ) : episodesData && episodesData.episodes.length > 0 ? (
    <div className="space-y-0.5 p-2 pt-5 pb-5">
      {episodesData.episodes.map((episode) => (
        <button
          key={episode.episode_name}
          type="button"
          data-episode={episode.episode_name}
          onClick={() => setSelectedEpisode(episode.episode_name)}
          className={cn(
            'w-full text-left px-2 py-1.5 rounded-sm text-sm transition-all font-mono',
            selectedEpisode === episode.episode_name
              ? 'bg-accent text-accent-foreground font-medium'
              : 'hover:bg-accent/50 text-muted-foreground hover:text-foreground'
          )}
          title={`${episode.episode_name} - ${episode.entry_count} entries`}
        >
          <div className="truncate">{episode.episode_name}</div>
        </button>
      ))}
    </div>
  ) : (
    <div className="p-4 text-sm text-muted-foreground text-center">
      No episodes found
    </div>
  )

  // 主内容
  const mainContent = contentLoading ? (
    <div className="flex items-center justify-center py-16">
      <Spinner size="lg" />
    </div>
  ) : episodeDetail ? (
    <>
      {/* 优先使用解析后的Markdown（句子级时间标注），fallback到entries */}
      {parsedMarkdown && parsedMarkdown.length > 0 ? (
        <div className="space-y-2">
          {parsedMarkdown.map((entry: any) => (
            <div key={entry.index} className="flex gap-4 hover:bg-muted/50 p-2 rounded-sm transition-colors">
              <div className="flex-shrink-0 w-[100px] md:w-[220px] font-mono text-xs text-muted-foreground select-none leading-7 flex flex-wrap gap-1 items-center">
                <div>[{entry.start_time}]</div>
                <div className='md:block hidden'>→</div>
                <div>[{entry.end_time}]</div>
              </div>
              <div className="flex-1 leading-7 min-w-0">
                {entry.text}
              </div>
            </div>
          ))}
        </div>
      ) : episodeDetail?.entries && episodeDetail.entries.length > 0 ? (
        <div className="space-y-2">
          {episodeDetail.entries.map((entry: any) => (
            <div key={entry.index} className="flex gap-4 hover:bg-muted/50 p-2 rounded-sm transition-colors">
              <div className="flex-shrink-0 w-[100px] md:w-[220px] font-mono text-xs text-muted-foreground select-none leading-7 flex flex-wrap gap-1 items-center">
                <div>[{entry.start_time}]</div>
                <div className='md:block hidden'>→</div>
                <div>[{entry.end_time}]</div>
              </div>
              <div className="flex-1 leading-7 min-w-0">
                {entry.text}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <article className="prose prose-gray dark:prose-invert max-w-none">
          <div className="leading-7 whitespace-pre-wrap">
            {episodeDetail.processed_text}
          </div>
        </article>
      )}
    </>
  ) : (
    <div className="flex items-center justify-center h-full text-sm text-muted-foreground">
      Select an episode to view
    </div>
  )

  return (
    <ViewerLayout
      navTitle="Episodes"
      navContent={navContent}
      mainContent={mainContent}
      currentIndex={currentIndex}
      totalCount={totalEpisodes}
    />
  )
}
