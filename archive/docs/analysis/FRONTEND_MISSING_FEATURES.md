# 前端缺失功能与API接口设计

**最后更新**: 2026-02-12  
**目的**: 详细列出前端缺失的核心功能，设计对应的API接口和数据结构

---

## 📊 总体评估

### 前端完成度

| Step | UI页面 | 数据展示 | 核心功能 | 完成度 |
|------|--------|---------|---------|--------|
| **Step 1: Import** | ✅ 完整 | ✅ 完整 | ✅ 完整 | **95%** |
| **Step 2: Script** | ✅ 完整 | ❌ **缺失** | 🟡 部分 | **40%** |
| **Step 3: Novel** | ✅ 完整 | ❌ **缺失** | 🟡 部分 | **35%** |
| **Step 4: Alignment** | ✅ 完整 | ⚠️ **假数据** | ❌ 缺失 | **30%** |

**平均完成度**: **50%**

---

## 🔴 P0 - 核心缺失功能

### 1. Step 2: 分段结果展示

#### 用户需求
点击某一集，查看该集的分段结果：
- 分段列表（12个分段）
- 每个分段的内容、类型（A/B/C）、时间范围
- ABC类型分布统计

#### 前端缺失
- ❌ 没有分段结果查看页面
- ❌ 没有API调用逻辑

#### 后端数据
✅ 已生成：`analyst/script_analysis/ep01_segmentation_latest.json`

#### 需要的API
```typescript
// API: 获取单集分段结果
GET /api/v2/projects/{project_id}/analyst/script_analysis/{episode_id}/segmentation

Response:
{
  "episode_id": "ep01",
  "total_segments": 12,
  "segments": [
    {
      "segment_id": "seg001",
      "content": "末日降临，公路求生。",
      "category": "A",
      "start_time": 0.0,
      "end_time": 2.5,
      "srt_range": [1, 1]
    },
    ...
  ],
  "abc_distribution": {
    "A": 2,
    "B": 9,
    "C": 1
  },
  "metadata": {
    "llm_provider": "deepseek",
    "total_cost": 0.08
  }
}
```

#### 前端组件设计
```typescript
// 新增页面：ScriptSegmentationResultPage.tsx
<ScriptSegmentationResultPage episodeId="ep01">
  {/* ABC分布统计 */}
  <Card>
    <CardTitle>ABC Distribution</CardTitle>
    <CardContent>
      <Badge variant="blue">A: 2 (17%)</Badge>
      <Badge variant="green">B: 9 (75%)</Badge>
      <Badge variant="purple">C: 1 (8%)</Badge>
    </CardContent>
  </Card>
  
  {/* 分段列表 */}
  <SegmentList>
    {segments.map(seg => (
      <SegmentCard
        key={seg.segment_id}
        category={seg.category}
        timeRange={`${seg.start_time}s - ${seg.end_time}s`}
        content={seg.content}
      />
    ))}
  </SegmentList>
</ScriptSegmentationResultPage>
```

**导航方式**：
- 从 Step2ScriptAnalysisPage 的集数卡片点击 "View Results" 按钮
- 路由：`/project/{id}/workflow/step_2_script/{episode_id}/result`

---

### 2. Step 2: Hook检测结果展示

#### 用户需求
查看ep01的Hook检测结果：
- 是否检测到Hook
- Hook结束位置（45.6秒）
- 置信度（92%）
- Hook包含的分段内容

#### 前端缺失
- ❌ 没有Hook结果展示区域

#### 后端数据
✅ 已生成：`analyst/script_analysis/ep01_hook_latest.json`

#### 需要的API
```typescript
// API: 获取Hook检测结果
GET /api/v2/projects/{project_id}/analyst/script_analysis/ep01/hook

Response:
{
  "episode_id": "ep01",
  "has_hook": true,
  "hook_end_time": 45.6,
  "body_start_index": 15,
  "confidence": 0.92,
  "hook_segments": [
    {
      "segment_id": "hook_001",
      "content": "末日降临，公路求生...",
      "start_time": 0.0,
      "end_time": 10.5
    }
  ]
}
```

#### 前端组件设计
```typescript
// 在 ScriptSegmentationResultPage 中添加
<HookDetectionCard hookResult={hookResult}>
  <div className="flex items-center justify-between">
    <div>
      <Badge variant={hookResult.has_hook ? "success" : "secondary"}>
        {hookResult.has_hook ? "Hook Detected" : "No Hook"}
      </Badge>
      {hookResult.has_hook && (
        <div className="mt-2 text-sm">
          <p>Hook End: {hookResult.hook_end_time}s</p>
          <p>Confidence: {(hookResult.confidence * 100).toFixed(0)}%</p>
        </div>
      )}
    </div>
  </div>
  
  {/* Hook分段内容 */}
  {hookResult.hook_segments.map(seg => (
    <div className="border-l-4 border-orange-400 pl-3 mt-2">
      <p className="text-sm">{seg.content}</p>
      <p className="text-xs text-muted-foreground">
        {seg.start_time}s - {seg.end_time}s
      </p>
    </div>
  ))}
</HookDetectionCard>
```

---

### 3. Step 3: 章节分段结果展示

#### 用户需求
查看每章的分段结果：
- 段落列表（50个段落）
- 每个段落的内容、类型
- 段落统计（叙述40个、对话10个）

#### 前端缺失
- ❌ 没有章节列表侧边栏
- ❌ 没有分段结果查看页面

#### 后端数据
✅ 已生成：`analyst/novel_analysis/chapter_001_segmentation_latest.json`

#### 需要的API
```typescript
// API 1: 获取章节列表及状态
GET /api/v2/projects/{project_id}/analyst/novel_analysis/chapters

Response:
{
  "chapters": [
    {
      "chapter_id": "chapter_001",
      "chapter_title": "第一章 末日降临",
      "status": "completed",
      "quality_score": 88,
      "total_paragraphs": 50,
      "total_events": 15,
      "processed_at": "2026-02-12T20:00:00"
    },
    ...
  ]
}

// API 2: 获取单章分段结果
GET /api/v2/projects/{project_id}/analyst/novel_analysis/{chapter_id}/segmentation

Response:
{
  "chapter_id": "chapter_001",
  "chapter_title": "第一章 末日降临",
  "total_paragraphs": 50,
  "paragraphs": [
    {
      "paragraph_id": "p001",
      "content": "末日降临的那一天，苏烈正驾驶着卡车...",
      "category": "narrative",
      "char_count": 45
    },
    ...
  ],
  "category_distribution": {
    "narrative": 40,
    "dialogue": 8,
    "description": 1,
    "system": 1
  }
}
```

#### 前端组件设计
```typescript
// 新增页面：NovelSegmentationResultPage.tsx
<NovelSegmentationResultPage chapterId="chapter_001">
  {/* 左侧：章节列表 */}
  <ChapterSidebar>
    {chapters.map(ch => (
      <ChapterItem
        id={ch.chapter_id}
        title={ch.chapter_title}
        status={ch.status}
        qualityScore={ch.quality_score}
        onClick={() => selectChapter(ch.chapter_id)}
      />
    ))}
  </ChapterSidebar>
  
  {/* 右侧：分段结果 */}
  <div className="flex-1">
    {/* 段落类型统计 */}
    <Card>
      <CardTitle>Paragraph Distribution</CardTitle>
      <CardContent>
        <Badge>Narrative: 40 (80%)</Badge>
        <Badge>Dialogue: 8 (16%)</Badge>
        <Badge>System: 2 (4%)</Badge>
      </CardContent>
    </Card>
    
    {/* 段落列表 */}
    <ParagraphList>
      {paragraphs.map(p => (
        <ParagraphCard
          id={p.paragraph_id}
          content={p.content}
          category={p.category}
        />
      ))}
    </ParagraphList>
  </div>
</NovelSegmentationResultPage>
```

**导航方式**：
- 从 Step3NovelAnalysisPage 添加 "View Results" 按钮
- 路由：`/project/{id}/workflow/step_3_novel/result`

---

### 4. Step 3: 标注结果展示

#### 用户需求
查看每章的标注结果：
- **事件时间线**（15个事件）
- **设定库**（10个设定）
- 每个事件的详细信息（描述、时间、地点、参与者）

#### 前端缺失
- ❌ 没有标注结果展示页面

#### 后端数据
✅ 已生成：`analyst/novel_analysis/chapter_001_annotation_latest.json`

#### 需要的API
```typescript
// API: 获取单章标注结果
GET /api/v2/projects/{project_id}/analyst/novel_analysis/{chapter_id}/annotation

Response:
{
  "chapter_id": "chapter_001",
  "event_timeline": [
    {
      "event_id": "ev001",
      "description": "苏烈驾车行驶在高速公路",
      "timestamp": "Day 1, 10:00",
      "location": "高速公路",
      "participants": ["苏烈"],
      "related_paragraphs": ["p001", "p003"]
    },
    ...
  ],
  "setting_library": [
    {
      "setting_id": "set001",
      "type": "world_rule",
      "content": "序列公路系统规则：玩家需要通过公路关卡...",
      "related_paragraphs": ["p002"]
    },
    ...
  ]
}
```

#### 前端组件设计
```typescript
// 在 NovelSegmentationResultPage 中添加Tab
<Tabs defaultValue="segmentation">
  <TabsList>
    <TabsTrigger value="segmentation">Segmentation</TabsTrigger>
    <TabsTrigger value="annotation">Annotation</TabsTrigger>
    <TabsTrigger value="system">System Elements</TabsTrigger>
  </TabsList>
  
  <TabsContent value="annotation">
    {/* 事件时间线 */}
    <Card>
      <CardTitle>Event Timeline</CardTitle>
      <CardContent>
        {eventTimeline.map(event => (
          <EventCard
            key={event.event_id}
            description={event.description}
            timestamp={event.timestamp}
            location={event.location}
            participants={event.participants}
          />
        ))}
      </CardContent>
    </Card>
    
    {/* 设定库 */}
    <Card>
      <CardTitle>Setting Library</CardTitle>
      <CardContent>
        {settingLibrary.map(setting => (
          <SettingCard
            key={setting.setting_id}
            type={setting.type}
            content={setting.content}
          />
        ))}
      </CardContent>
    </Card>
  </TabsContent>
</Tabs>
```

---

### 5. Step 3: 系统元素目录展示

#### 用户需求
查看全书的系统元素分析：
- 系统名称
- 分类（玩家属性、道具、技能）
- 每个元素的描述、首次出现位置

#### 前端缺失
- ❌ 没有系统元素查看页面

#### 后端数据
✅ 已生成：`analyst/novel_analysis/system_catalog_latest.json`

#### 需要的API
```typescript
// API: 获取系统元素目录
GET /api/v2/projects/{project_id}/analyst/novel_analysis/system_catalog

Response:
{
  "system_name": "序列公路求生系统",
  "categories": {
    "player_stats": [
      {
        "name": "生命值",
        "description": "玩家当前生命值",
        "first_appearance": "chapter_001",
        "mentions": ["chapter_001", "chapter_003"]
      }
    ],
    "items": [
      {
        "name": "强化卡车",
        "description": "可升级的载具",
        "first_appearance": "chapter_002"
      }
    ],
    "skills": [...]
  }
}
```

#### 前端组件设计
```typescript
// 在 NovelSegmentationResultPage 的第三个Tab
<TabsContent value="system">
  <SystemCatalogViewer catalog={systemCatalog}>
    {/* 系统名称 */}
    <h3>{catalog.system_name}</h3>
    
    {/* 分类展示 */}
    <Accordion>
      <AccordionItem value="player_stats">
        <AccordionTrigger>
          Player Stats ({catalog.categories.player_stats.length})
        </AccordionTrigger>
        <AccordionContent>
          {catalog.categories.player_stats.map(stat => (
            <SystemElementCard
              name={stat.name}
              description={stat.description}
              firstAppearance={stat.first_appearance}
            />
          ))}
        </AccordionContent>
      </AccordionItem>
      
      <AccordionItem value="items">
        <AccordionTrigger>Items</AccordionTrigger>
        <AccordionContent>...</AccordionContent>
      </AccordionItem>
    </Accordion>
  </SystemCatalogViewer>
</TabsContent>
```

---

### 6. Step 4: 对齐结果真实数据加载

#### 用户需求
查看对齐结果（UI已有，但用的是假数据）：
- Sankey图
- 对齐对列表
- 覆盖率统计

#### 前端缺失
- ❌ 使用 mockAlignments（假数据）
- ❌ 没有API调用逻辑

#### 后端数据
⚠️ 待生成：`analyst/alignment/chapter_001_ep01_alignment_latest.json`

#### 需要的API
```typescript
// API 1: 获取对齐对列表
GET /api/v2/projects/{project_id}/analyst/alignment/pairs

Response:
{
  "pairs": [
    {
      "chapter_id": "chapter_001",
      "episode_id": "ep01",
      "status": "completed",
      "quality_score": 90
    }
  ]
}

// API 2: 获取单对的对齐详情
GET /api/v2/projects/{project_id}/analyst/alignment/{chapter_id}/{episode_id}

Response:
{
  "chapter_id": "chapter_001",
  "episode_id": "ep01",
  "alignments": [
    {
      "script_segment_id": "seg002",
      "novel_paragraph_id": "p001",
      "confidence": 0.92,
      "rewrite_strategy": "paraphrase",
      "script_content": "苏烈独自驾驶着卡车...",
      "novel_content": "末日降临的那一天，苏烈正驾驶着卡车..."
    },
    ...
  ],
  "coverage": {
    "event_coverage": 0.95,
    "setting_coverage": 0.85,
    "total_novel_paragraphs": 50,
    "total_script_segments": 12,
    "aligned_paragraphs": 47,
    "aligned_segments": 11
  },
  "type_matching": {
    "A_to_A": 2,
    "B_to_B": 8,
    "C_to_C": 1,
    "mismatches": 0
  }
}
```

#### 前端组件更新
```typescript
// 更新 Step4AlignmentPage.tsx
export function Step4AlignmentPage({ projectId, stepState }: Props) {
  // ❌ 删除 mockAlignments
  // const mockAlignments = [...]
  
  // ✅ 使用真实数据
  const { data: alignmentResult } = useQuery({
    queryKey: ['alignment-result', projectId, 'chapter_001', 'ep01'],
    queryFn: () => projectsApiV2.getAlignmentResult(projectId, 'chapter_001', 'ep01'),
    enabled: stepState.status === 'completed'
  })
  
  // 渲染真实数据
  return (
    <div>
      <AlignmentSankeyDiagram
        novelNodes={transformNovelData(alignmentResult.alignments)}
        scriptNodes={transformScriptData(alignmentResult.alignments)}
        links={transformLinks(alignmentResult.alignments)}
      />
      
      <CoverageStats coverage={alignmentResult.coverage} />
      
      <AlignmentList alignments={alignmentResult.alignments} />
    </div>
  )
}
```

---

## 📊 API接口汇总

### 新增API端点（11个）

#### Step 2: Script Analysis
```
1. GET /api/v2/projects/{id}/analyst/script_analysis/{episode_id}/segmentation
   → 获取分段结果

2. GET /api/v2/projects/{id}/analyst/script_analysis/{episode_id}/hook
   → 获取Hook检测结果（仅ep01）

3. GET /api/v2/projects/{id}/analyst/script_analysis/{episode_id}/validation
   → 获取质量报告

4. GET /api/v2/projects/{id}/analyst/script_analysis/summary
   → 获取汇总统计（所有集数的ABC分布、平均质量等）
```

#### Step 3: Novel Analysis
```
5. GET /api/v2/projects/{id}/analyst/novel_analysis/chapters
   → 获取章节列表及状态

6. GET /api/v2/projects/{id}/analyst/novel_analysis/{chapter_id}/segmentation
   → 获取单章分段结果

7. GET /api/v2/projects/{id}/analyst/novel_analysis/{chapter_id}/annotation
   → 获取单章标注结果（事件时间线+设定库）

8. GET /api/v2/projects/{id}/analyst/novel_analysis/system_catalog
   → 获取系统元素目录

9. GET /api/v2/projects/{id}/analyst/novel_analysis/{chapter_id}/validation
   → 获取质量报告
```

#### Step 4: Alignment
```
10. GET /api/v2/projects/{id}/analyst/alignment/pairs
    → 获取所有对齐对列表

11. GET /api/v2/projects/{id}/analyst/alignment/{chapter_id}/{episode_id}
    → 获取单对的对齐详情
```

---

## 🎨 前端新增页面

### 页面1: Script分段结果查看
- **路由**: `/project/{id}/workflow/step_2_script/{episode_id}/result`
- **组件**: `ScriptSegmentationResultPage.tsx`
- **功能**: 展示分段、Hook检测、质量报告

### 页面2: Novel分段+标注结果查看
- **路由**: `/project/{id}/workflow/step_3_novel/result`
- **组件**: `NovelAnalysisResultPage.tsx`
- **功能**: 展示分段、标注（事件+设定）、系统元素

### 页面3: 对齐结果查看
- **路由**: `/project/{id}/workflow/step_4_alignment/result`
- **组件**: `AlignmentResultPage.tsx`（已有UI，需连接真实数据）
- **功能**: Sankey图、对齐列表、覆盖率统计

---

## 📝 Markdown文件决策

### 最终决定

| 文件 | 用途 | 决策 | 原因 |
|------|------|------|------|
| `novel-imported.md` | NovelViewer展示原文 | ✅ **保留** | Viewer需要，ReactMarkdown渲染 |
| `ep01-imported.md` | ScriptViewer展示 | ❌ **删除** | 前端可直接使用JSON，减少冗余 |

### 修改方案

#### 1. 删除Script Markdown生成
```python
# src/tools/srt_text_extractor.py

def execute(self, srt_entries: List[SrtEntry], ...):
    """提取SRT文本"""
    
    # 提取纯文本
    extracted_text = self._extract_text(srt_entries)
    
    # ❌ 删除：不再生成markdown
    # markdown_content = self._format_as_markdown(srt_entries)
    # save_text(markdown_content, f"{output_dir}/{episode_id}-imported.md")
    
    # ✅ 只返回JSON
    return SrtTextExtractionResult(
        episode_id=episode_id,
        extracted_text=extracted_text,
        timestamp_mapping={...}
    )
```

#### 2. 更新前端ScriptViewer
```typescript
// frontend-new/src/pages/ScriptViewerPage.tsx

// ❌ 删除：不再读取markdown
// const { data: importedScript } = useQuery({
//   queryFn: async () => {
//     const response = await fetch(`.../${episodeId}-imported.md`)
//     return response.text()
//   }
// })

// ✅ 直接使用JSON
const { data: episodeDetail } = useQuery({
  queryKey: ['episode-detail', projectId, selectedEpisode],
  queryFn: () => projectsApiV2.getEpisodeDetail(projectId, selectedEpisode!),
  enabled: !!selectedEpisode,
})

// 渲染
{episodeDetail.entries.map(entry => (
  <div key={entry.index} className="flex gap-4">
    <div className="font-mono text-xs text-muted-foreground">
      [{entry.start_time} → {entry.end_time}]
    </div>
    <div className="text-sm">{entry.text}</div>
  </div>
))}
```

---

## 📋 实施优先级

### 🔴 P0 - 立即实施（本周）

1. **补全API接口**（2天）
   - [ ] 实现11个新API端点
   - [ ] 测试API返回数据

2. **实现结果展示页面**（3天）
   - [ ] ScriptSegmentationResultPage
   - [ ] NovelAnalysisResultPage（含3个Tab）
   - [ ] 连接Step4真实数据

3. **删除Script Markdown**（1天）
   - [ ] 更新SrtTextExtractor
   - [ ] 更新ScriptViewer
   - [ ] 测试验证

### 🟡 P1 - 短期优化（下周）

1. **优化数据汇总**
   - [ ] 后端添加汇总API
   - [ ] 前端使用汇总数据

2. **添加导航按钮**
   - [ ] Step2/3 添加 "View Results" 按钮
   - [ ] 路由配置

### 🔵 P2 - 长期优化（2周）

1. **目录结构迁移**
   - [ ] 执行迁移脚本
   - [ ] 更新所有代码路径

---

## 🎯 预期效果

实施P0后：
- **用户可见内容**: 20% → 90% (+350%)
- **前端完成度**: 50% → 85% (+70%)
- **文件冗余**: -5个markdown文件
- **用户体验**: 大幅提升（可以看到所有分析结果）

---

**最后更新**: 2026-02-12  
**核心结论**: 
1. ❌ 删除 Script Markdown（前端用JSON）
2. ✅ 保留 Novel Markdown（Viewer需要）
3. 🔴 **最重要：补全11个API接口 + 3个结果展示页面**
