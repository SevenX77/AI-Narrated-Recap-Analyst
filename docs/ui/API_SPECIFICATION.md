# API接口规范文档

**版本**: v2.0 ⭐ (推荐使用)  
**基础URL**: `http://localhost:8000/api`  
**WebSocket URL**: `ws://localhost:8000/ws`  
**日期**: 2026-02-11

> **📌 重要更新 (2026-02-11)**:  
> - ✅ **V2 API** 已上线，提供完整的项目生命周期管理和自动预处理功能  
> - ✅ **PreprocessService** 后台服务，自动识别文件类型并执行相应处理  
> - ✅ **实时状态追踪**，前端可实时监控预处理进度  
> - ⚠️ **V1 API** 已废弃，建议迁移到 V2  
>
> **V2 vs V1 对比**:
> | 功能 | V1 | V2 |
> |------|----|----|
> | 自动预处理 | ❌ 需手动触发 | ✅ 上传即处理 |
> | 状态追踪 | ❌ 无状态 | ✅ 实时状态 |
> | 文件增量上传 | ❌ | ✅ |
> | 元数据管理 | 基础 | 完整 |
> | 推荐使用 | ⚠️ 废弃 | ✅ 推荐 |

---

## 目录

1. [通用规范](#1-通用规范)
2. [项目管理 API V2](#2-项目管理-api-v2) ⭐ 推荐
3. [项目管理 API V1](#3-项目管理-api-v1) ⚠️ 已废弃
4. [工作流执行 API](#4-工作流执行-api)
5. [结果查询 API](#5-结果查询-api)
6. [工件管理 API](#6-工件管理-api)
7. [WebSocket 协议](#7-websocket-协议)
8. [错误处理](#8-错误处理)

---

## 1. 通用规范

### 1.1 请求头

```http
Content-Type: application/json
Accept: application/json
```

### 1.2 响应格式

**成功响应**:
```json
{
  "success": true,
  "data": { /* 实际数据 */ },
  "message": "操作成功"
}
```

**错误响应**:
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "参数验证失败",
    "details": {
      "field": "project_name",
      "reason": "项目名不能为空"
    }
  }
}
```

### 1.3 HTTP状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 409 | 资源冲突（如项目名重复） |
| 500 | 服务器内部错误 |

### 1.4 分页参数

```typescript
interface PaginationParams {
  page: number      // 页码，从1开始
  page_size: number // 每页数量，默认20，最大100
}

interface PaginatedResponse<T> {
  success: true
  data: {
    items: T[]
    total: number
    page: number
    page_size: number
    total_pages: number
  }
}
```

---

## 2. 项目管理 API V2 ⭐

> **推荐使用 V2 API**，提供完整的项目生命周期管理和自动预处理功能。

### 2.1 获取项目列表

**请求**:
```http
GET /api/v2/projects
```

**查询参数**:
```typescript
{
  page?: number          // 页码，默认1
  page_size?: number     // 每页数量，默认20
}
```

**响应**:
```json
{
  "items": [
    {
      "id": "project_001",
      "name": "序列公路求生",
      "description": "末日升级题材",
      "status": "completed",
      "created_at": "2026-02-10T10:00:00Z",
      "updated_at": "2026-02-11T08:30:00Z",
      "sources": {
        "has_novel": true,
        "has_script": true,
        "novel_chapters": 50,
        "script_episodes": 5
      },
      "workflow_stages": {
        "import": { "status": "completed" },
        "metadata": { "status": "completed" },
        "segmentation": { "status": "completed" },
        "annotation": { "status": "completed" }
      }
    }
  ],
  "total": 12,
  "page": 1,
  "page_size": 20
}
```

---

### 2.2 获取项目统计信息

**请求**:
```http
GET /api/v2/projects/stats
```

**响应**:
```json
{
  "total_projects": 12,
  "active_projects": 8,
  "completed_projects": 4,
  "total_chapters": 500,
  "total_episodes": 60
}
```

---

### 2.3 创建项目

**请求**:
```http
POST /api/v2/projects
Content-Type: application/json
```

**请求体**:
```json
{
  "name": "序列公路求生",
  "description": "末日升级题材小说"
}
```

**响应**:
```json
{
  "id": "project_002",
  "name": "序列公路求生",
  "description": "末日升级题材小说",
  "status": "draft",
  "created_at": "2026-02-11T10:00:00Z",
  "sources": {
    "has_novel": false,
    "has_script": false,
    "novel_chapters": 0,
    "script_episodes": 0
  }
}
```

---

### 2.4 获取项目详情

**请求**:
```http
GET /api/v2/projects/{project_id}
```

**响应**:
```json
{
  "id": "project_001",
  "name": "序列公路求生",
  "description": "末日升级题材",
  "status": "completed",
  "created_at": "2026-02-10T10:00:00Z",
  "updated_at": "2026-02-11T08:30:00Z",
  "sources": {
    "has_novel": true,
    "has_script": true,
    "novel_chapters": 50,
    "script_episodes": 5
  },
  "workflow_stages": {
    "import": { 
      "status": "completed",
      "started_at": "2026-02-10T10:00:00Z",
      "completed_at": "2026-02-10T10:05:00Z"
    },
    "preprocess": {
      "status": "completed",
      "started_at": "2026-02-10T10:05:00Z",
      "completed_at": "2026-02-10T10:30:00Z"
    }
  }
}
```

---

### 2.5 获取项目完整元数据

**请求**:
```http
GET /api/v2/projects/{project_id}/meta
```

**响应**: 包含完整的项目配置、文件列表、处理结果等详细信息

---

### 2.6 上传文件（自动预处理）⭐

**请求**:
```http
POST /api/v2/projects/{project_id}/files
Content-Type: multipart/form-data
```

**表单数据**:
```typescript
{
  files: File[]              // 文件列表（.txt, .srt）
  auto_preprocess?: boolean  // 是否自动预处理，默认 true
}
```

**响应**:
```json
{
  "message": "文件上传成功",
  "files_uploaded": [
    {
      "filename": "novel.txt",
      "size": 1024000,
      "type": "novel",
      "path": "data/projects/project_001/raw/novel/novel.txt"
    },
    {
      "filename": "ep01.srt",
      "size": 52000,
      "type": "script",
      "path": "data/projects/project_001/raw/srt/ep01.srt"
    }
  ],
  "auto_preprocess": true,
  "preprocess_status": "pending"
}
```

**说明**:
- 上传的文件会自动触发 `PreprocessService`
- 系统自动识别文件类型（.txt → Novel, .srt → Script）
- 后台异步执行预处理（不阻塞响应）
- 使用 `/preprocess-status` 接口追踪处理进度

---

### 2.7 手动触发预处理

**请求**:
```http
POST /api/v2/projects/{project_id}/preprocess
```

**响应**:
```json
{
  "message": "预处理已触发",
  "status": "pending"
}
```

---

### 2.8 获取预处理状态 ⭐

**请求**:
```http
GET /api/v2/projects/{project_id}/preprocess-status
```

**响应**:
```json
{
  "preprocess_stage": {
    "status": "running",  // "pending" | "running" | "completed" | "failed"
    "started_at": "2026-02-11T10:05:00Z",
    "completed_at": null,
    "error": null
  },
  "novel_stage": {
    "status": "completed",
    "chapters_processed": 50,
    "chapters_total": 50,
    "current_step": "annotation"
  },
  "script_stage": {
    "status": "running",
    "episodes_processed": 3,
    "episodes_total": 5,
    "current_step": "segmentation"
  }
}
```

**前端使用**:
```typescript
// React Query 自动刷新示例
const { data } = useQuery({
  queryKey: ['preprocess-status', projectId],
  queryFn: () => api.getPreprocessStatus(projectId),
  refetchInterval: (data) => {
    // 如果正在处理，每3秒刷新一次
    return data?.preprocess_stage.status === 'running' ? 3000 : false
  }
})
```

---

### 2.9 获取原始文件列表

**请求**:
```http
GET /api/v2/projects/{project_id}/files
```

**响应**:
```json
{
  "novel_files": [
    {
      "filename": "novel.txt",
      "size": 1024000,
      "uploaded_at": "2026-02-10T10:00:00Z"
    }
  ],
  "srt_files": [
    {
      "filename": "ep01.srt",
      "size": 52000,
      "uploaded_at": "2026-02-10T10:00:00Z"
    },
    {
      "filename": "ep02.srt",
      "size": 48000,
      "uploaded_at": "2026-02-10T10:00:00Z"
    }
  ]
}
```

---

### 2.10 获取章节列表

**请求**:
```http
GET /api/v2/projects/{project_id}/chapters
```

**响应**:
```json
{
  "chapters": [
    {
      "number": 1,
      "title": "第一章 诡异来袭",
      "start_line": 1,
      "end_line": 150,
      "word_count": 3200,
      "segmented": true,
      "annotated": true
    }
  ],
  "total": 50
}
```

---

### 2.11 获取集数列表

**请求**:
```http
GET /api/v2/projects/{project_id}/episodes
```

**响应**:
```json
{
  "episodes": [
    {
      "name": "ep01",
      "entry_count": 120,
      "word_count": 2500,
      "segmented": true
    }
  ],
  "total": 5
}
```

---

### 2.12 删除项目

**请求**:
```http
DELETE /api/v2/projects/{project_id}
```

**响应**:
```json
{
  "message": "项目删除成功",
  "deleted_project_id": "project_001"
}
```

---

## 3. 项目管理 API V1 ⚠️

> **⚠️ V1 API 已废弃**，仅用于向后兼容。新项目请使用 V2 API。

### 3.1 获取项目列表

**请求**:
```http
GET /api/projects
```

**查询参数**:
```typescript
{
  page?: number          // 页码，默认1
  page_size?: number     // 每页数量，默认20
  status?: string        // 状态筛选: "active" | "completed" | "failed"
  search?: string        // 搜索关键词（项目名）
  sort_by?: string       // 排序字段: "created_at" | "updated_at" | "name"
  sort_order?: string    // 排序方向: "asc" | "desc"
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "project_id": "proj_001",
        "name": "末哥超凡公路",
        "description": "玄幻小说分析项目",
        "status": "completed",
        "created_at": "2026-02-08T10:30:00Z",
        "updated_at": "2026-02-10T14:22:00Z",
        "stats": {
          "novel_chapters": 10,
          "script_episodes": 5,
          "quality_score": 88,
          "last_workflow": "novel_processing"
        },
        "files": {
          "novel": "novel.txt",
          "scripts": ["ep01.srt", "ep02.srt", "ep03.srt"]
        }
      }
    ],
    "total": 12,
    "page": 1,
    "page_size": 20,
    "total_pages": 1
  }
}
```

---

### 2.2 创建项目

**请求**:
```http
POST /api/projects
Content-Type: application/json
```

**请求体**:
```json
{
  "name": "天命桃花",
  "description": "仙侠小说分析项目",
  "metadata": {
    "genre": "仙侠",
    "author": "未知",
    "tags": ["修仙", "桃花", "逆天改命"]
  }
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "project_id": "proj_002",
    "name": "天命桃花",
    "description": "仙侠小说分析项目",
    "status": "active",
    "created_at": "2026-02-10T15:00:00Z",
    "paths": {
      "root": "data/projects/proj_002",
      "raw": "data/projects/proj_002/raw",
      "novel": "data/projects/proj_002/novel",
      "script": "data/projects/proj_002/script",
      "alignment": "data/projects/proj_002/alignment"
    }
  },
  "message": "项目创建成功"
}
```

---

### 2.3 获取项目详情

**请求**:
```http
GET /api/projects/{project_id}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "project_id": "proj_001",
    "name": "末哥超凡公路",
    "description": "玄幻小说分析项目",
    "status": "completed",
    "created_at": "2026-02-08T10:30:00Z",
    "updated_at": "2026-02-10T14:22:00Z",
    
    "files": {
      "novel": {
        "filename": "novel.txt",
        "size": 348672,
        "uploaded_at": "2026-02-08T10:32:00Z"
      },
      "scripts": [
        {
          "filename": "ep01.srt",
          "size": 45678,
          "uploaded_at": "2026-02-08T11:00:00Z"
        }
      ]
    },
    
    "workflows": [
      {
        "workflow_id": "wf_001",
        "type": "novel_processing",
        "status": "completed",
        "started_at": "2026-02-08T10:35:00Z",
        "completed_at": "2026-02-08T11:20:00Z",
        "duration_seconds": 2700,
        "result": {
          "chapters_processed": 10,
          "quality_score": 88
        }
      }
    ],
    
    "stats": {
      "novel": {
        "total_chapters": 10,
        "total_characters": 126966,
        "avg_chapter_length": 12696
      },
      "script": {
        "total_episodes": 5,
        "total_duration_seconds": 1280,
        "avg_episode_duration": 256
      },
      "processing": {
        "total_token_used": 245678,
        "total_cost_usd": 2.45,
        "total_time_seconds": 3600
      }
    }
  }
}
```

---

### 2.4 上传文件

**请求**:
```http
POST /api/projects/{project_id}/upload
Content-Type: multipart/form-data
```

**表单数据**:
```typescript
{
  file: File               // 文件对象
  file_type: string        // "novel" | "script"
  episode_number?: number  // script类型必填（如1, 2, 3）
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "file_id": "file_001",
    "filename": "ep01.srt",
    "file_type": "script",
    "episode_number": 1,
    "size": 45678,
    "path": "data/projects/proj_001/raw/ep01.srt",
    "uploaded_at": "2026-02-10T15:30:00Z"
  },
  "message": "文件上传成功"
}
```

---

### 2.5 删除项目

**请求**:
```http
DELETE /api/projects/{project_id}
```

**查询参数**:
```typescript
{
  delete_files?: boolean  // 是否删除文件，默认false（仅标记删除）
}
```

**响应**:
```json
{
  "success": true,
  "message": "项目已删除"
}
```

---

## 3. 工作流执行 API

### 3.1 启动工作流

**请求**:
```http
POST /api/workflows/execute
Content-Type: application/json
```

**请求体**:
```json
{
  "project_id": "proj_001",
  "workflow_type": "novel_processing",
  "config": {
    "llm_provider": "claude",
    "max_concurrency": 10,
    "enable_system_analysis": true,
    "enable_functional_tags": false,
    "chapters": [1, 2, 3, 4, 5]  // 可选，指定处理章节
  }
}
```

**工作流类型**:
```typescript
type WorkflowType = 
  | "novel_processing"      // Novel处理工作流
  | "script_processing"     // Script处理工作流
  | "alignment"             // 对齐分析工作流
  | "full_pipeline"         // 完整流程
```

**配置参数**:
```typescript
// Novel Processing Config
interface NovelProcessingConfig {
  llm_provider: "claude" | "deepseek"
  max_concurrency: number  // 1-20
  enable_system_analysis: boolean
  enable_functional_tags: boolean
  chapters?: number[]  // 可选，指定处理章节
}

// Script Processing Config
interface ScriptProcessingConfig {
  llm_provider: "claude" | "deepseek"
  enable_hook_detection: boolean
  enable_abc_classification: boolean
  episodes?: number[]  // 可选，指定处理集数
}

// Alignment Config
interface AlignmentConfig {
  llm_provider: "claude" | "deepseek"
  alignment_mode: "sentence" | "paragraph"
  min_confidence: number  // 0.0 - 1.0
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "task_id": "task_20260210_150045_abc123",
    "workflow_type": "novel_processing",
    "status": "started",
    "started_at": "2026-02-10T15:00:45Z",
    "estimated_duration_seconds": 3600,
    "estimated_cost_usd": 2.50,
    "websocket_url": "ws://localhost:8000/ws/progress/task_20260210_150045_abc123"
  },
  "message": "工作流已启动，请通过WebSocket监听进度"
}
```

---

### 3.2 查询工作流状态

**请求**:
```http
GET /api/workflows/{task_id}/status
```

**响应**:
```json
{
  "success": true,
  "data": {
    "task_id": "task_20260210_150045_abc123",
    "workflow_type": "novel_processing",
    "status": "running",
    "progress": 0.45,
    "current_stage": "novel_annotation",
    "current_step": "处理第5章标注...",
    
    "started_at": "2026-02-10T15:00:45Z",
    "elapsed_seconds": 1350,
    "estimated_remaining_seconds": 1650,
    
    "metrics": {
      "token_used": 125430,
      "token_total_estimate": 250000,
      "cost_usd": 1.25,
      "estimated_total_cost": 2.50
    },
    
    "stages": [
      {
        "name": "novel_import",
        "status": "completed",
        "progress": 1.0,
        "duration_seconds": 2
      },
      {
        "name": "novel_metadata_extraction",
        "status": "completed",
        "progress": 1.0,
        "duration_seconds": 15
      },
      {
        "name": "novel_chapter_detection",
        "status": "completed",
        "progress": 1.0,
        "duration_seconds": 1
      },
      {
        "name": "novel_segmentation",
        "status": "completed",
        "progress": 1.0,
        "duration_seconds": 800
      },
      {
        "name": "novel_annotation",
        "status": "running",
        "progress": 0.5,
        "duration_seconds": 532
      }
    ]
  }
}
```

---

### 3.3 取消工作流

**请求**:
```http
POST /api/workflows/{task_id}/cancel
```

**响应**:
```json
{
  "success": true,
  "message": "工作流已取消"
}
```

---

### 3.4 获取工作流日志

**请求**:
```http
GET /api/workflows/{task_id}/logs
```

**查询参数**:
```typescript
{
  level?: string      // 日志级别: "debug" | "info" | "warning" | "error"
  tail?: number       // 返回最后N行，默认100
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "task_id": "task_20260210_150045_abc123",
    "logs": [
      {
        "timestamp": "2026-02-10T15:00:45.123Z",
        "level": "info",
        "message": "工作流启动",
        "context": {
          "workflow_type": "novel_processing"
        }
      },
      {
        "timestamp": "2026-02-10T15:01:30.456Z",
        "level": "info",
        "message": "章节分段完成",
        "context": {
          "chapter": 1,
          "segments": 11
        }
      }
    ],
    "total": 1523,
    "tail": 100
  }
}
```

---

## 4. 结果查询 API

### 4.1 获取Novel处理结果

**请求**:
```http
GET /api/results/{project_id}/novel
```

**查询参数**:
```typescript
{
  chapter?: number        // 可选，指定章节
  include_content?: boolean  // 是否包含完整内容，默认false
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "project_id": "proj_001",
    "metadata": {
      "title": "末哥超凡公路",
      "author": "未知",
      "tags": ["玄幻", "系统流", "末世"],
      "summary": "一个关于末世超凡力量的故事..."
    },
    
    "chapters": [
      {
        "chapter_number": 1,
        "title": "第一章：末世降临",
        "character_count": 12696,
        "
        "segmentation": {
          "total_segments": 11,
          "class_distribution": {
            "A": 3,  // 设定
            "B": 7,  // 事件
            "C": 1   // 系统
          },
          "segments": [
            {
              "segment_id": 1,
              "class_type": "B",
              "line_start": 1,
              "line_end": 5,
              "title": "收音机播报上沪沦陷",
              "content": "收音机中传来紧急播报...",  // 仅当include_content=true时返回
              "tags": {
                "priority": "P0",
                "narrative_function": "开局设定",
                "location": "车内",
                "time": "上午"
              }
            }
          ]
        },
        
        "annotation": {
          "event_timeline": {
            "events": [
              {
                "event_id": "E001",
                "event_summary": "收音机播报上沪沦陷",
                "related_segments": [1],
                "location": "车内",
                "time": "上午",
                "characters": ["陈峰"]
              }
            ]
          },
          "setting_library": {
            "settings": [
              {
                "setting_id": "S001",
                "category": "世界观",
                "content": "末世爆发，上沪沦陷",
                "acquisition_time": "BF",  // Before/BT/After
                "related_events": ["E001"]
              }
            ]
          }
        },
        
        "quality": {
          "segmentation_score": 95,
          "annotation_score": 90,
          "overall_score": 92
        }
      }
    ],
    
    "system_catalog": {
      "novel_type": "系统流玄幻",
      "categories": [
        {
          "category_id": "SC001",
          "name": "物资系统",
          "elements": ["食物", "水", "药品", "武器"],
          "tracking_strategy": "quantity"
        }
      ]
    },
    
    "quality_report": {
      "overall_score": 88,
      "encoding_correct": true,
      "chapter_complete": true,
      "segmentation_reasonable": true,
      "issues": [],
      "suggestions": []
    }
  }
}
```

---

### 4.2 获取Script处理结果

**请求**:
```http
GET /api/results/{project_id}/script
```

**查询参数**:
```typescript
{
  episode?: number        // 可选，指定集数
  include_content?: boolean  // 是否包含完整内容，默认false
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "project_id": "proj_001",
    "episodes": [
      {
        "episode_number": 1,
        "duration_seconds": 256,
        "srt_entries": 48,
        
        "hook_detection": {
          "has_hook": true,
          "hook_duration_seconds": 45.6,
          "body_start_time": "00:00:45,600",
          "confidence": 0.9,
          "analysis": {
            "world_building": ["末世设定", "超凡力量"],
            "game_mechanics": ["系统觉醒"],
            "items": [],
            "plot_events": ["上沪沦陷"]
          }
        },
        
        "segmentation": {
          "total_segments": 15,
          "class_distribution": {
            "A": 1,   // 设定
            "B": 14,  // 事件
            "C": 0    // 系统
          },
          "segments": [
            {
              "segment_id": 1,
              "class_type": "A",
              "sentence_start": 1,
              "sentence_end": 3,
              "title": "末世背景介绍",
              "content": "收音机播报上沪沦陷...",
              "srt_time_start": "00:00:00,000",
              "srt_time_end": "00:00:15,320"
            }
          ]
        },
        
        "quality": {
          "timeline_continuous": true,
          "text_complete": true,
          "segmentation_reasonable": true,
          "overall_score": 85
        }
      }
    ]
  }
}
```

---

### 4.3 获取对齐分析结果

**请求**:
```http
GET /api/results/{project_id}/alignment
```

**查询参数**:
```typescript
{
  episode?: number  // 可选，指定集数
  chapter?: number  // 可选，指定章节
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "project_id": "proj_001",
    "alignments": [
      {
        "episode_number": 1,
        "novel_chapters": [1, 2],
        
        "alignment_pairs": [
          {
            "novel_segment": {
              "chapter": 1,
              "segment_id": 1,
              "class_type": "B",
              "content": "收音机播报上沪沦陷..."
            },
            "script_segment": {
              "episode": 1,
              "segment_id": 1,
              "class_type": "A",
              "content": "末世爆发，上沪沦陷..."
            },
            "alignment_type": "paraphrase",
            "confidence": 0.92,
            "changes": {
              "rewrite_strategy": "简化+改写",
              "content_preserved": 0.85,
              "emotional_consistency": 0.90
            }
          }
        ],
        
        "coverage": {
          "event_coverage": 0.85,  // 85%
          "setting_coverage": 1.0,  // 100%
          "events_covered": 17,
          "events_total": 20,
          "settings_covered": 5,
          "settings_total": 5
        },
        
        "statistics": {
          "total_pairs": 42,
          "alignment_types": {
            "exact": 5,
            "paraphrase": 28,
            "summarize": 7,
            "expand": 2,
            "none": 0
          },
          "avg_confidence": 0.88
        },
        
        "quality": {
          "alignment_score": 90,
          "coverage_score": 85,
          "overall_score": 87
        }
      }
    ]
  }
}
```

---

### 4.4 导出结果

**请求**:
```http
POST /api/results/{project_id}/export
Content-Type: application/json
```

**请求体**:
```json
{
  "export_type": "novel" | "script" | "alignment" | "full",
  "format": "json" | "pdf" | "excel",
  "options": {
    "include_content": true,
    "include_stats": true,
    "chapters": [1, 2, 3],  // 可选
    "episodes": [1, 2]      // 可选
  }
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "export_id": "export_20260210_160000",
    "download_url": "/api/artifacts/export_20260210_160000/download",
    "format": "pdf",
    "size_bytes": 1024576,
    "created_at": "2026-02-10T16:00:00Z",
    "expires_at": "2026-02-17T16:00:00Z"  // 7天后过期
  },
  "message": "导出任务已创建"
}
```

---

## 5. 工件管理 API

### 5.1 获取工件列表

**请求**:
```http
GET /api/artifacts
```

**查询参数**:
```typescript
{
  project_id?: string
  artifact_type?: string  // "segmentation" | "annotation" | "alignment" | "report"
  page?: number
  page_size?: number
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "artifact_id": "artifact_001",
        "project_id": "proj_001",
        "artifact_type": "segmentation",
        "filename": "chapter_01_segmentation.json",
        "size_bytes": 45678,
        "version": "v1",
        "created_at": "2026-02-10T14:30:00Z",
        "metadata": {
          "chapter": 1,
          "segments": 11,
          "quality_score": 95
        }
      }
    ],
    "total": 50,
    "page": 1,
    "page_size": 20
  }
}
```

---

### 5.2 下载工件

**请求**:
```http
GET /api/artifacts/{artifact_id}/download
```

**响应**:
```
Content-Type: application/json | application/pdf | application/vnd.ms-excel
Content-Disposition: attachment; filename="chapter_01_segmentation.json"

[文件内容流]
```

---

### 5.3 删除工件

**请求**:
```http
DELETE /api/artifacts/{artifact_id}
```

**响应**:
```json
{
  "success": true,
  "message": "工件已删除"
}
```

---

## 6. WebSocket 协议

### 6.1 连接

**URL**:
```
ws://localhost:8000/ws/progress/{task_id}
```

**连接示例 (JavaScript)**:
```javascript
const ws = new WebSocket(`ws://localhost:8000/ws/progress/${taskId}`)

ws.onopen = () => {
  console.log('WebSocket连接已建立')
}

ws.onmessage = (event) => {
  const message = JSON.parse(event.data)
  handleProgressUpdate(message)
}

ws.onerror = (error) => {
  console.error('WebSocket错误:', error)
}

ws.onclose = () => {
  console.log('WebSocket连接已关闭')
}
```

---

### 6.2 消息格式

#### 进度更新消息
```json
{
  "type": "progress",
  "task_id": "task_20260210_150045_abc123",
  "timestamp": 1707574845123,
  "status": "running",
  
  "progress": 0.45,
  "stage": "novel_annotation",
  "current_step": "处理第5章标注...",
  
  "metrics": {
    "token_used": 125430,
    "token_total_estimate": 250000,
    "cost_usd": 1.25,
    "estimated_total_cost": 2.50,
    "elapsed_seconds": 1350,
    "estimated_remaining_seconds": 1650
  },
  
  "logs": [
    {
      "timestamp": "2026-02-10T15:25:35.123Z",
      "level": "info",
      "message": "第5章标注完成"
    }
  ]
}
```

#### 完成消息
```json
{
  "type": "completed",
  "task_id": "task_20260210_150045_abc123",
  "timestamp": 1707577845123,
  "status": "completed",
  "progress": 1.0,
  
  "result": {
    "workflow_type": "novel_processing",
    "success": true,
    "chapters_processed": 10,
    "quality_score": 88,
    "output_path": "data/projects/proj_001/novel"
  },
  
  "metrics": {
    "total_token_used": 245678,
    "total_cost_usd": 2.45,
    "total_duration_seconds": 3000
  }
}
```

#### 错误消息
```json
{
  "type": "error",
  "task_id": "task_20260210_150045_abc123",
  "timestamp": 1707575845123,
  "status": "failed",
  "progress": 0.35,
  
  "error": {
    "code": "LLM_API_ERROR",
    "message": "LLM API调用失败",
    "stage": "novel_segmentation",
    "details": {
      "chapter": 4,
      "retry_count": 3,
      "last_error": "HTTP 429: Rate limit exceeded"
    }
  }
}
```

#### 日志消息
```json
{
  "type": "log",
  "task_id": "task_20260210_150045_abc123",
  "timestamp": 1707574900123,
  
  "log": {
    "timestamp": "2026-02-10T15:15:00.123Z",
    "level": "warning",
    "message": "章节3分段耗时较长",
    "context": {
      "chapter": 3,
      "duration_seconds": 120
    }
  }
}
```

---

### 6.3 心跳机制

**客户端 → 服务端 (每30秒)**:
```json
{
  "type": "ping"
}
```

**服务端 → 客户端**:
```json
{
  "type": "pong",
  "timestamp": 1707574845123
}
```

---

## 7. 错误处理

### 7.1 错误码定义

| 错误码 | HTTP状态 | 说明 |
|--------|---------|------|
| `VALIDATION_ERROR` | 400 | 请求参数验证失败 |
| `PROJECT_NOT_FOUND` | 404 | 项目不存在 |
| `PROJECT_NAME_CONFLICT` | 409 | 项目名重复 |
| `FILE_TOO_LARGE` | 400 | 文件过大（>50MB） |
| `UNSUPPORTED_FILE_TYPE` | 400 | 不支持的文件类型 |
| `WORKFLOW_NOT_FOUND` | 404 | 工作流任务不存在 |
| `WORKFLOW_ALREADY_RUNNING` | 409 | 工作流正在运行中 |
| `LLM_API_ERROR` | 500 | LLM API调用失败 |
| `STORAGE_ERROR` | 500 | 文件存储错误 |
| `INTERNAL_ERROR` | 500 | 服务器内部错误 |

### 7.2 错误响应示例

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "参数验证失败",
    "details": {
      "field": "workflow_type",
      "reason": "工作流类型无效",
      "allowed_values": ["novel_processing", "script_processing", "alignment"]
    },
    "timestamp": "2026-02-10T15:30:00Z",
    "request_id": "req_abc123"
  }
}
```

---

## 8. API使用示例

### 8.1 完整工作流示例

```typescript
// 1. 创建项目
const project = await fetch('/api/projects', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    name: '新项目',
    description: '测试项目'
  })
}).then(r => r.json())

const projectId = project.data.project_id

// 2. 上传小说文件
const formData = new FormData()
formData.append('file', novelFile)
formData.append('file_type', 'novel')

await fetch(`/api/projects/${projectId}/upload`, {
  method: 'POST',
  body: formData
})

// 3. 启动Novel工作流
const workflow = await fetch('/api/workflows/execute', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    project_id: projectId,
    workflow_type: 'novel_processing',
    config: {
      llm_provider: 'claude',
      max_concurrency: 10,
      enable_system_analysis: true
    }
  })
}).then(r => r.json())

const taskId = workflow.data.task_id

// 4. 通过WebSocket监听进度
const ws = new WebSocket(`ws://localhost:8000/ws/progress/${taskId}`)

ws.onmessage = (event) => {
  const msg = JSON.parse(event.data)
  
  if (msg.type === 'progress') {
    console.log(`进度: ${(msg.progress * 100).toFixed(1)}%`)
    console.log(`当前阶段: ${msg.stage}`)
    console.log(`Token消耗: ${msg.metrics.token_used}`)
  }
  
  if (msg.type === 'completed') {
    console.log('工作流完成!')
    console.log(`质量评分: ${msg.result.quality_score}`)
    
    // 5. 查询结果
    loadResults(projectId)
  }
}

async function loadResults(projectId: string) {
  const results = await fetch(`/api/results/${projectId}/novel`)
    .then(r => r.json())
  
  console.log('处理结果:', results.data)
}
```

---

## 9. 性能建议

### 9.1 分页查询
对于大量数据，使用分页避免一次性加载：
```typescript
// 推荐
GET /api/projects?page=1&page_size=20

// 不推荐
GET /api/projects  // 可能返回数百个项目
```

### 9.2 按需加载内容
默认不返回完整内容，需要时才加载：
```typescript
// 列表页：不含内容（快速）
GET /api/results/proj_001/novel

// 详情页：含完整内容（慢速）
GET /api/results/proj_001/novel?chapter=1&include_content=true
```

### 9.3 WebSocket重连
实现自动重连机制：
```typescript
function connectWebSocket(taskId: string, retryCount = 0) {
  const ws = new WebSocket(`ws://localhost:8000/ws/progress/${taskId}`)
  
  ws.onclose = () => {
    if (retryCount < 5) {
      setTimeout(() => {
        connectWebSocket(taskId, retryCount + 1)
      }, 2000 * Math.pow(2, retryCount))  // 指数退避
    }
  }
  
  return ws
}
```

---

## 10. 变更日志

### v1.0 (2026-02-10)
- 初始版本
- 实现项目管理、工作流执行、结果查询API
- 实现WebSocket进度推送
- 实现工件管理API

---

**文档版本**: v1.0  
**最后更新**: 2026-02-10  
**维护者**: AI-Narrated Recap Analyst Team
