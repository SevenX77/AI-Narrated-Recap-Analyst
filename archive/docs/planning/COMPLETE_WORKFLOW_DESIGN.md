# 完整工作流设计

**最后更新**: 2026-02-12  
**目的**: 详细说明每一步的前端功能→后端工具工作流→data结果存储

---

## 📊 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React)                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ Step 1   │  │ Step 2   │  │ Step 3   │  │ Step 4   │        │
│  │ Import   │→ │ Script   │→ │ Novel    │→ │Alignment │        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
└───────────────────────┬─────────────────────────────────────────┘
                        ↓ HTTP/WebSocket
┌─────────────────────────────────────────────────────────────────┐
│                     Backend API (FastAPI)                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ /api/v2/projects/{project_id}/                           │   │
│  │  ├─ POST /files (上传)                                  │   │
│  │  ├─ GET /workflow-state (状态)                          │   │
│  │  ├─ POST /workflow/{step_id}/start (启动)               │   │
│  │  └─ WS /ws (实时更新)                                   │   │
│  └──────────────────────────────────────────────────────────┘   │
└───────────────────────┬─────────────────────────────────────────┘
                        ↓ 调用
┌─────────────────────────────────────────────────────────────────┐
│                  Workflows & Tools (Python)                      │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐    │
│  │ Preprocess     │  │ Script         │  │ Novel          │    │
│  │ Service        │  │ Processing     │  │ Processing     │    │
│  └────────────────┘  └────────────────┘  └────────────────┘    │
└───────────────────────┬─────────────────────────────────────────┘
                        ↓ 写入/读取
┌─────────────────────────────────────────────────────────────────┐
│                    Data Storage (JSON Files)                     │
│  ┌────────┐  ┌────────────┐  ┌──────────┐  ┌─────────┐         │
│  │ raw/   │→ │ processed/ │→ │analysis/ │→ │reports/ │         │
│  └────────┘  └────────────┘  └──────────┘  └─────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Step 1: Import - 文件导入与标准化

### 前端功能

**页面**: `Step1ImportPage.tsx`

**UI组件**:
```typescript
<Step1ImportPage>
  <FileUploadZone 
    accept=".txt,.srt"
    multiple={true}
    onUpload={handleFileUpload}
  />
  
  <FileList>
    {/* Novel文件 */}
    <FileItem 
      name="序列公路求生.txt"
      status="imported"
      size="500KB"
      type="novel"
    />
    
    {/* Script文件 */}
    <FileItem 
      name="ep01.srt"
      status="processing"
      progress={45}
      type="script"
    />
  </FileList>
  
  <PreprocessStatus>
    <StatusBadge status="running" />
    <ProgressBar value={45} />
    <TaskList>
      <Task name="Novel: 章节检测" status="completed" />
      <Task name="Script: ep01.srt 文本提取" status="running" progress={45} />
    </TaskList>
  </PreprocessStatus>
</Step1ImportPage>
```

**用户操作**:
1. 拖拽文件或点击上传
2. 自动识别文件类型（.txt → Novel, .srt → Script）
3. 实时显示预处理进度

**API调用**:
```typescript
// 上传文件
const formData = new FormData();
formData.append('file', file);

await fetch(`/api/v2/projects/${projectId}/files`, {
  method: 'POST',
  body: formData
});

// 轮询预处理状态（或使用WebSocket）
const status = await fetch(`/api/v2/projects/${projectId}/preprocess-status`);
```

---

### 后端工作流

**触发方式**: 文件上传后自动触发

**服务**: `PreprocessService` (异步后台任务)

**工具链**:

#### Novel预处理
```python
PreprocessService.process_novel(project_id, file_path)
    ↓
1. NovelImporter.execute(novel_path)
   - 编码检测 (chardet)
   - 转换为UTF-8
   - 保存到 processed/novel/standardized.txt
    ↓
2. NovelMetadataExtractor.execute(standardized_text)
   - 提取标题、作者、字数
   - 保存到 processed/novel/metadata.json
    ↓
3. NovelChapterDetector.execute(standardized_text)
   - 检测章节边界（正则表达式）
   - 提取章节标题
   - 保存到 processed/novel/chapters.json
```

#### Script预处理
```python
PreprocessService.process_script(project_id, file_path)
    ↓
1. SrtImporter.execute(srt_path)
   - 解析SRT格式
   - 验证时间轴
   - 保存到 processed/script/{episode_id}.json
    ↓
2. SrtTextExtractor.execute(srt_entries)
   - 提取纯文本
   - LLM添加标点符号
   - 修正错别字
   - 保存到 processed/script/{episode_id}-imported.md
```

**配置**:
```python
PreprocessConfig(
    novel_encoding_detection=True,
    script_text_extraction=True,
    use_llm_for_punctuation=True,
    llm_provider="deepseek"  # 低成本
)
```

**成本**: ~$0.02-0.04 / 集（仅标点修复）

---

### Data存储结果

**写入路径**:
```
data/projects/{project_id}/
├── raw/
│   ├── novel/
│   │   └── 序列公路求生.txt              # 用户上传
│   └── srt/
│       ├── ep01.srt                      # 用户上传
│       └── ep02.srt
│
├── processed/
│   ├── novel/
│   │   ├── standardized.txt              # ✅ Step 1输出
│   │   ├── metadata.json                 # ✅ Step 1输出
│   │   │   {
│   │   │     "title": "序列公路求生",
│   │   │     "author": "末哥超凡",
│   │   │     "total_chars": 500000,
│   │   │     "chapter_count": 50
│   │   │   }
│   │   └── chapters.json                 # ✅ Step 1输出
│   │       [
│   │         {
│   │           "id": "chapter_001",
│   │           "title": "第一章 末日降临",
│   │           "start_line": 1,
│   │           "end_line": 150
│   │         },
│   │         ...
│   │       ]
│   │
│   └── script/
│       ├── ep01.json                     # ✅ Step 1输出
│       │   {
│       │     "episode_id": "ep01",
│       │     "total_entries": 146,
│       │     "entries": [...]
│       │   }
│       ├── ep01-imported.md              # ✅ Step 1输出
│       │   末日降临，公路求生。苏烈独自...
│       └── episodes.json                 # ✅ Step 1输出
│           [
│             {
│               "episode_id": "ep01",
│               "name": "第一集",
│               "status": "imported"
│             },
│             ...
│           ]
│
└── meta.json
    {
      "phase_i_analyst": {
        "step_1_import": {
          "status": "completed",              # ✅ 状态更新
          "novel_imported": true,
          "novel_chapter_count": 50,
          "script_imported": true,
          "script_episodes": ["ep01", "ep02"]
        }
      }
    }
```

**状态更新**:
```python
# 更新 meta.json
meta.phase_i_analyst.step_1_import.status = PhaseStatus.COMPLETED
meta.phase_i_analyst.step_1_import.novel_imported = True
meta.phase_i_analyst.step_1_import.novel_chapter_count = 50
meta.phase_i_analyst.step_1_import.script_episodes = ["ep01", "ep02", ...]
project_manager_v2.save_project_meta(meta)
```

---

## 🎯 Step 2: Script Analysis - 脚本分析

### 前端功能

**页面**: `Step2ScriptAnalysisPage.tsx`

**UI组件**:
```typescript
<Step2ScriptAnalysisPage>
  {/* 开始按钮 */}
  <StartButton 
    disabled={!canStart}
    onClick={handleStart}
  >
    Start Analysis
  </StartButton>
  
  {/* 配置选项 */}
  <ConfigPanel>
    <Switch label="Enable Hook Detection (ep01)" checked={true} />
    <Switch label="Enable ABC Classification" checked={true} />
    <Select label="LLM Provider" value="deepseek" />
  </ConfigPanel>
  
  {/* 集数列表 */}
  <EpisodeList>
    <EpisodeCard 
      episodeId="ep01"
      status="running"
      progress={45}
      currentTask="Segmenting script..."
    />
    <EpisodeCard 
      episodeId="ep02"
      status="pending"
    />
  </EpisodeList>
  
  {/* 实时日志 */}
  <LogViewer logs={workflowLogs} />
</Step2ScriptAnalysisPage>
```

**用户操作**:
1. 点击 "Start Analysis" 按钮
2. 查看实时进度和日志
3. 可单独启动/停止某一集

**API调用**:
```typescript
// 启动整体分析
await fetch(`/api/v2/projects/${projectId}/workflow/step_2_script/start`, {
  method: 'POST'
});

// 启动单集
await fetch(`/api/v2/projects/${projectId}/episodes/${episodeId}/start`, {
  method: 'POST'
});

// 停止单集
await fetch(`/api/v2/projects/${projectId}/episodes/${episodeId}/stop`, {
  method: 'POST'
});
```

---

### 后端工作流

**触发方式**: 用户点击 "Start Analysis"

**工作流**: `ScriptProcessingWorkflow`

**Phase设计**:

```python
async def _execute_script_workflow(project_id: str):
    """批量处理所有SRT文件"""
    
    # 1. 加载项目和集数列表
    meta = project_manager_v2.get_project(project_id)
    episodes = meta.phase_i_analyst.step_1_import.script_episodes
    
    # 2. 配置
    config = ScriptProcessingConfig(
        enable_hook_detection=True,       # ep01启用
        enable_abc_classification=True,
        segmentation_provider="deepseek",
        min_quality_score=70
    )
    
    # 3. 逐集处理
    for i, episode_id in enumerate(episodes):
        # 更新状态
        await broadcast_progress(
            project_id, "step_2_script",
            progress=(i / len(episodes)) * 100,
            current_task=f"Processing {episode_id} ({i+1}/{len(episodes)})"
        )
        
        # 执行Workflow
        result = await process_single_episode(
            project_id, episode_id, config
        )
        
        # 保存结果
        save_episode_result(project_id, episode_id, result)
    
    # 4. 完成
    meta.phase_i_analyst.step_2_script.status = PhaseStatus.COMPLETED
    project_manager_v2.save_project_meta(meta)
```

**单集处理流程**:
```python
def process_single_episode(project_id, episode_id, config):
    """
    Phase 1: SRT导入（已在Step 1完成，跳过）
    Phase 2: 文本提取（已在Step 1完成，跳过）
    Phase 3: Hook检测（仅ep01）
    Phase 4: 语义分段 + ABC分类
    Phase 5: 质量验证
    """
    
    # 读取预处理结果
    srt_entries = load_json(f"processed/script/{episode_id}.json")
    extracted_text = load_text(f"processed/script/{episode_id}-imported.md")
    
    # Phase 3: Hook检测（仅ep01）
    hook_result = None
    if episode_id == "ep01" and config.enable_hook_detection:
        hook_result = HookDetector.execute(
            extracted_text=extracted_text,
            novel_intro=load_novel_intro(project_id)
        )
        # 保存Hook结果
        artifact_manager.save_artifact(
            content=hook_result.model_dump(),
            artifact_type=f"{episode_id}_hook",
            base_dir=f"analysis/script"
        )
    
    # Phase 4: 语义分段 + ABC分类（Two-Pass）
    segmentation_result = ScriptSegmenter.execute(
        extracted_text=extracted_text,
        srt_entries=srt_entries["entries"],
        enable_abc_classification=config.enable_abc_classification,
        provider=config.segmentation_provider
    )
    # 保存分段结果
    artifact_manager.save_artifact(
        content=segmentation_result.model_dump(),
        artifact_type=f"{episode_id}_segmentation",
        base_dir=f"analysis/script"
    )
    
    # Phase 5: 质量验证
    validation_result = ScriptValidator.execute(
        srt_entries=srt_entries,
        segmentation_result=segmentation_result
    )
    # 保存验证结果
    artifact_manager.save_artifact(
        content=validation_result.model_dump(),
        artifact_type=f"{episode_id}_validation",
        base_dir=f"analysis/script"
    )
    
    return {
        "episode_id": episode_id,
        "hook_result": hook_result,
        "segmentation_result": segmentation_result,
        "validation_result": validation_result
    }
```

**配置**:
```python
ScriptProcessingConfig(
    enable_hook_detection=True,       # ep01启用Hook检测
    enable_abc_classification=True,   # 启用ABC分类
    segmentation_provider="deepseek", # DeepSeek降低成本
    text_extraction_provider="deepseek",
    min_quality_score=70,
    retry_on_error=True,
    max_retries=3
)
```

**成本**: 
- ep01（含Hook）: ~$0.19
- ep02-10（无Hook）: ~$0.09/集
- 10集总计: ~$2.00

---

### Data存储结果

**写入路径**:
```
data/projects/{project_id}/
├── analysis/
│   └── script/
│       ├── ep01_hook_latest.json                 # ✅ Step 2输出（ep01专属）
│       │   {
│       │     "episode_id": "ep01",
│       │     "has_hook": true,
│       │     "hook_end_time": 45.6,
│       │     "confidence": 0.92
│       │   }
│       │
│       ├── ep01_segmentation_latest.json         # ✅ Step 2输出
│       │   {
│       │     "episode_id": "ep01",
│       │     "total_segments": 12,
│       │     "segments": [
│       │       {
│       │         "segment_id": "seg001",
│       │         "content": "末日降临，公路求生。",
│       │         "category": "A",  // A=设定, B=事件, C=系统
│       │         "start_time": 0.0,
│       │         "end_time": 2.5
│       │       },
│       │       ...
│       │     ]
│       │   }
│       │
│       ├── ep01_validation_latest.json           # ✅ Step 2输出
│       │   {
│       │     "episode_id": "ep01",
│       │     "quality_score": 85,
│       │     "issues": [],
│       │     "suggestions": ["..."]
│       │   }
│       │
│       ├── ep02_segmentation_latest.json         # ✅ Step 2输出
│       │
│       └── history/                              # 历史版本
│           ├── ep01_hook_v20260212_180000.json
│           ├── ep01_segmentation_v20260212_180100.json
│           └── ...
│
└── meta.json
    {
      "phase_i_analyst": {
        "step_2_script": {
          "status": "completed",                  # ✅ 状态更新
          "total_episodes": 5,
          "completed_episodes": 5,
          "episodes_status": {
            "ep01": {
              "status": "completed",
              "has_hook": true,
              "quality_score": 85
            },
            "ep02": {
              "status": "completed",
              "quality_score": 82
            }
          }
        }
      }
    }
```

---

## 🎯 Step 3: Novel Analysis - 小说分析

### 前端功能

**页面**: `Step3NovelAnalysisPage.tsx`

**UI组件**:
```typescript
<Step3NovelAnalysisPage>
  {/* 开始按钮 */}
  <StartButton onClick={handleStart}>
    Start Analysis
  </StartButton>
  
  {/* 配置 */}
  <ConfigPanel>
    <InputNumber label="Chapter Range" value={[1, 10]} />
    <InputNumber label="Max Concurrent" value={3} />
    <Switch label="Enable System Analysis" checked={true} />
    <Select label="LLM Provider" value="claude" />
  </ConfigPanel>
  
  {/* 章节列表 */}
  <ChapterList>
    <ChapterCard 
      chapterId="chapter_001"
      title="第一章 末日降临"
      status="completed"
      qualityScore={88}
    />
    <ChapterCard 
      chapterId="chapter_002"
      status="running"
      progress={60}
      currentTask="Annotating chapter..."
    />
  </ChapterList>
</Step3NovelAnalysisPage>
```

**用户操作**:
1. 配置处理范围（前10章）
2. 点击 "Start Analysis"
3. 查看章节处理进度

---

### 后端工作流

**工作流**: `NovelProcessingWorkflow`

**Phase设计**:

```python
async def _execute_novel_workflow(project_id: str):
    """并行处理多个章节"""
    
    # 1. 加载章节列表
    chapters = load_json(f"processed/novel/chapters.json")
    target_chapters = chapters[0:10]  # 只处理前10章
    
    # 2. 配置
    config = NovelProcessingConfig(
        enable_parallel=True,
        max_concurrent_chapters=3,
        segmentation_provider="claude",
        annotation_provider="claude",
        enable_system_analysis=True
    )
    
    # 3. 并行处理章节
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = []
        for chapter in target_chapters:
            future = executor.submit(
                process_single_chapter,
                project_id, chapter, config
            )
            futures.append(future)
        
        # 等待所有章节完成
        for i, future in enumerate(as_completed(futures)):
            result = future.result()
            
            # 更新进度
            await broadcast_progress(
                project_id, "step_3_novel",
                progress=(i / len(target_chapters)) * 100
            )
    
    # 4. 系统元素分析（全书一次）
    if config.enable_system_analysis:
        system_catalog = NovelSystemAnalyzer.execute(
            annotated_chapters=load_all_annotated_chapters(project_id)
        )
        # 保存系统目录
        artifact_manager.save_artifact(
            content=system_catalog.model_dump(),
            artifact_type="system_catalog",
            base_dir=f"analysis/novel"
        )
    
    # 5. 完成
    meta.phase_i_analyst.step_3_novel.status = PhaseStatus.COMPLETED
    project_manager_v2.save_project_meta(meta)
```

**单章处理流程**:
```python
def process_single_chapter(project_id, chapter, config):
    """
    Phase 1: 章节导入（已在Step 1完成）
    Phase 2: 章节分段（Two-Pass）
    Phase 3: 章节标注（Three-Pass）
    Phase 4: 质量验证
    """
    
    chapter_id = chapter["id"]
    
    # 读取章节文本
    standardized_text = load_text(f"processed/novel/standardized.txt")
    chapter_text = extract_chapter_text(
        standardized_text,
        chapter["start_line"],
        chapter["end_line"]
    )
    
    # Phase 2: 章节分段（Two-Pass）
    segmentation_result = NovelSegmenter.execute(
        chapter_text=chapter_text,
        chapter_id=chapter_id,
        provider=config.segmentation_provider
    )
    # 保存分段结果
    artifact_manager.save_artifact(
        content=segmentation_result.model_dump(),
        artifact_type=f"{chapter_id}_segmentation",
        base_dir=f"analysis/novel"
    )
    
    # Phase 3: 章节标注（Three-Pass）
    annotation_result = NovelAnnotator.execute(
        segmented_chapter=segmentation_result,
        provider=config.annotation_provider
    )
    # 保存标注结果
    artifact_manager.save_artifact(
        content=annotation_result.model_dump(),
        artifact_type=f"{chapter_id}_annotation",
        base_dir=f"analysis/novel"
    )
    
    # Phase 4: 质量验证
    validation_result = NovelValidator.execute(
        annotation_result=annotation_result
    )
    # 保存验证结果
    artifact_manager.save_artifact(
        content=validation_result.model_dump(),
        artifact_type=f"{chapter_id}_validation",
        base_dir=f"analysis/novel"
    )
    
    return {
        "chapter_id": chapter_id,
        "segmentation_result": segmentation_result,
        "annotation_result": annotation_result,
        "validation_result": validation_result
    }
```

**成本**:
- 单章成本: ~$0.15
- 10章总计: ~$1.50

---

### Data存储结果

**写入路径**:
```
data/projects/{project_id}/
├── analysis/
│   └── novel/
│       ├── chapter_001_segmentation_latest.json     # ✅ Step 3输出
│       │   {
│       │     "chapter_id": "chapter_001",
│       │     "total_paragraphs": 50,
│       │     "paragraphs": [
│       │       {
│       │         "paragraph_id": "p001",
│       │         "content": "末日降临的那一天...",
│       │         "category": "narrative"
│       │       },
│       │       ...
│       │     ]
│       │   }
│       │
│       ├── chapter_001_annotation_latest.json       # ✅ Step 3输出
│       │   {
│       │     "chapter_id": "chapter_001",
│       │     "event_timeline": [
│       │       {
│       │         "event_id": "ev001",
│       │         "description": "苏烈驾车行驶在高速公路",
│       │         "timestamp": "Day 1, 10:00",
│       │         "participants": ["苏烈"]
│       │       },
│       │       ...
│       │     ],
│       │     "setting_library": [...]
│       │   }
│       │
│       ├── chapter_001_validation_latest.json       # ✅ Step 3输出
│       │
│       ├── chapter_002_segmentation_latest.json
│       ├── chapter_002_annotation_latest.json
│       │
│       ├── system_catalog_latest.json               # ✅ Step 3输出（全书）
│       │   {
│       │     "system_name": "序列公路求生系统",
│       │     "categories": {
│       │       "player_stats": [...],
│       │       "items": [...],
│       │       "skills": [...]
│       │     }
│       │   }
│       │
│       └── history/
│           └── ...
│
└── meta.json
    {
      "phase_i_analyst": {
        "step_3_novel": {
          "status": "completed",                    # ✅ 状态更新
          "total_chapters": 10,
          "completed_chapters": 10,
          "total_events": 150,
          "total_settings": 80,
          "novel_steps": {
            "chapter_001": {
              "status": "completed",
              "quality_score": 88
            },
            ...
          }
        }
      }
    }
```

---

## 🎯 Step 4: Alignment - 对齐分析

### 前端功能

**页面**: `Step4AlignmentPage.tsx`

**UI组件**:
```typescript
<Step4AlignmentPage>
  {/* 依赖检查 */}
  <DependencyCheck>
    <CheckItem label="Step 2: Script Analysis" status="completed" />
    <CheckItem label="Step 3: Novel Analysis" status="completed" />
  </DependencyCheck>
  
  {/* 开始按钮 */}
  <StartButton 
    disabled={!canStart}
    onClick={handleStart}
  >
    Start Alignment
  </StartButton>
  
  {/* 对齐进度 */}
  <AlignmentProgress>
    <PairCard 
      chapterId="chapter_001"
      episodeId="ep01"
      status="running"
      progress={60}
    />
  </AlignmentProgress>
</Step4AlignmentPage>
```

---

### 后端工作流

**工作流**: `AlignmentWorkflow` 🚧 待实现

**Phase设计**:

```python
async def _execute_alignment_workflow(project_id: str):
    """对齐Novel和Script"""
    
    # 1. 加载数据
    novel_annotations = load_novel_annotations(project_id)
    script_segmentations = load_script_segmentations(project_id)
    
    # 2. 配置
    config = AlignmentConfig(
        enable_hook_alignment=True,
        min_confidence_threshold=0.7,
        alignment_provider="claude"
    )
    
    # 3. 逐对处理
    for chapter, episode in zip(chapters, episodes):
        # Phase 1: 数据验证
        # Phase 2: Hook-Body分离
        # Phase 3: 句子级对齐
        # Phase 4: ABC类型匹配
        # Phase 5: 覆盖率分析
        
        alignment_result = NovelScriptAligner.execute(
            annotated_chapter=novel_annotations[chapter],
            script_segmentation=script_segmentations[episode],
            config=config
        )
        
        # 保存对齐结果
        artifact_manager.save_artifact(
            content=alignment_result.model_dump(),
            artifact_type=f"{chapter}_{episode}_alignment",
            base_dir=f"analysis/alignment"
        )
```

---

### Data存储结果

**写入路径**:
```
data/projects/{project_id}/
├── analysis/
│   └── alignment/
│       ├── chapter_001_ep01_alignment_latest.json   # ✅ Step 4输出
│       │   {
│       │     "chapter_id": "chapter_001",
│       │     "episode_id": "ep01",
│       │     "alignments": [
│       │       {
│       │         "script_segment_id": "seg001",
│       │         "novel_paragraph_id": "p001",
│       │         "confidence": 0.92,
│       │         "rewrite_strategy": "paraphrase"
│       │       },
│       │       ...
│       │     ],
│       │     "coverage": {
│       │       "event_coverage": 0.95,
│       │       "setting_coverage": 0.85
│       │     }
│       │   }
│       │
│       └── history/
│           └── ...
│
└── meta.json
    {
      "phase_i_analyst": {
        "step_4_alignment": {
          "status": "completed",                    # ✅ 状态更新
          "total_alignments": 10,
          "average_confidence": 0.89,
          "event_coverage_rate": 0.92
        }
      }
    }
```

---

## 📋 完整流程总结

### 数据流向

```
用户上传 (raw/)
    ↓
Step 1: 自动预处理 (processed/)
    ├─ Novel: standardized.txt, metadata.json, chapters.json
    └─ Script: ep01.json, ep01-imported.md, episodes.json
    ↓
Step 2 & 3: 用户启动分析 (analysis/)
    ├─ Script: ep01_segmentation, ep01_hook
    └─ Novel: chapter_001_segmentation, chapter_001_annotation, system_catalog
    ↓
Step 4: 对齐分析 (analysis/alignment/)
    └─ chapter_001_ep01_alignment
```

### 状态同步

```
前端 (UI状态)
    ↕ WebSocket
后端 (meta.json)
    ↕ 文件I/O
Data (JSON文件)
```

### 成本汇总

| Step | 工具 | 成本/单位 | 10单位总计 |
|------|------|----------|-----------|
| Step 1 | Preprocess | ~$0.02/集 | ~$0.20 |
| Step 2 | ScriptProcessing | ~$0.10/集 | ~$1.00 |
| Step 3 | NovelProcessing | ~$0.15/章 | ~$1.50 |
| Step 4 | Alignment | ~$0.12/对 | ~$1.20 |
| **总计** | - | - | **~$3.90** |

---

**最后更新**: 2026-02-12  
**下一步**: 实施目录清理和命名统一
