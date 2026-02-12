# 命名规范

**最后更新**: 2026-02-12  
**目的**: 统一前端、后端、数据存储的命名方式

---

## 🎯 核心原则

1. **一致性优先**: 同一概念在所有地方使用相同命名
2. **语言规范**: 遵循各语言的命名惯例
3. **自动转换**: 使用工具自动转换（Pydantic alias, TypeScript transformer）

---

## 📦 数据类型命名

### 1. 项目ID (Project ID)

| 层级 | 命名 | 示例 | 说明 |
|------|------|------|------|
| **数据文件** | `project_id` | `project_001` | 目录名、文件名 |
| **后端Python** | `project_id` | `project_id: str` | 变量名、参数名 |
| **后端API** | `project_id` | `/api/v2/projects/{project_id}` | URL路径参数 |
| **前端TypeScript** | `projectId` | `const projectId: string` | 变量名（camelCase） |

**Pydantic 转换**:
```python
class ProjectMeta(BaseModel):
    id: str = Field(..., alias="project_id")  # API接收 project_id，内部用 id
    
    class Config:
        populate_by_name = True  # 允许两种名称
```

---

### 2. 集数ID (Episode ID) ⭐ 重点

#### 统一格式：`ep{XX}` (两位数字，补零)

| 层级 | 命名 | 示例 | 说明 |
|------|------|------|------|
| **原始文件** | `ep{XX}.srt` | `ep01.srt`, `ep02.srt` | 用户上传的文件名 |
| **数据文件** | `ep{XX}` | `ep01.json`, `ep01-imported.md` | 文件名前缀 |
| **后端Python** | `episode_id: str` | `episode_id = "ep01"` | 变量名（snake_case） |
| **后端API** | `episode_id` | `/episodes/{episode_id}/start` | URL路径参数 |
| **前端TypeScript** | `episodeId` | `const episodeId = "ep01"` | 变量名（camelCase） |
| **meta.json** | `episode_id` | `"episodes": ["ep01", "ep02"]` | 数组元素 |

#### ❌ 禁止使用的命名

- ~~`episode`~~ (太通用，不明确)
- ~~`ep_01`~~ (下划线不统一)
- ~~`episode_01`~~ (太长)
- ~~`1`~~ (纯数字不直观)

#### ✅ 代码示例

**后端 Python**:
```python
def process_episode(project_id: str, episode_id: str):
    """
    Args:
        project_id: 项目ID (如 "project_001")
        episode_id: 集数ID (如 "ep01", "ep02")
    """
    # 文件路径
    srt_path = f"data/projects/{project_id}/raw/srt/{episode_id}.srt"
    result_path = f"data/projects/{project_id}/analysis/script/{episode_id}_latest.json"
```

**前端 TypeScript**:
```typescript
interface Episode {
  episodeId: string;  // "ep01", "ep02"
  name: string;
  status: EpisodeStatus;
}

// API调用（自动转换为 episode_id）
const response = await fetch(`/api/v2/projects/${projectId}/episodes/${episodeId}/start`, {
  method: 'POST',
  body: JSON.stringify({ episodeId })  // 自动序列化为 episode_id
});
```

**Pydantic 自动转换**:
```python
class EpisodeInfo(BaseModel):
    episode_id: str  # API接收 episode_id 或 episodeId
    name: str
    status: str
    
    class Config:
        populate_by_name = True
        alias_generator = lambda x: x  # 保持snake_case
```

---

### 3. 章节ID (Chapter ID)

#### 统一格式：`chapter_{XXX}` (三位数字，补零)

| 层级 | 命名 | 示例 | 说明 |
|------|------|------|------|
| **数据文件** | `chapter_{XXX}` | `chapter_001.json` | 文件名前缀 |
| **后端Python** | `chapter_id: str` | `chapter_id = "chapter_001"` | 变量名 |
| **后端API** | `chapter_id` | `/chapters/{chapter_id}` | URL路径参数 |
| **前端TypeScript** | `chapterId` | `const chapterId = "chapter_001"` | 变量名 |
| **meta.json** | `chapter_id` | `"id": "chapter_001"` | JSON字段 |

#### ✅ 代码示例

**后端 Python**:
```python
def process_chapter(project_id: str, chapter_id: str):
    """
    Args:
        chapter_id: 章节ID (如 "chapter_001", "chapter_010")
    """
    result_path = f"data/projects/{project_id}/analysis/novel/{chapter_id}_latest.json"
```

---

### 4. 步骤ID (Step ID)

#### 统一格式：`step_{N}_{name}`

| 层级 | 命名 | 示例 | 说明 |
|------|------|------|------|
| **后端Python** | `step_id: str` | `step_id = "step_2_script"` | 变量名 |
| **后端API** | `step_id` | `/workflow/{step_id}/start` | URL路径参数 |
| **前端TypeScript** | `stepId` | `const stepId = "step_2_script"` | 变量名 |
| **meta.json** | `step_id` | `"step_2_script": {...}` | JSON字段名 |

**标准步骤ID列表**:
- `step_1_import` - 文件导入与标准化
- `step_2_script` - Script分析
- `step_3_novel` - Novel分析
- `step_4_alignment` - 对齐分析

---

### 5. 状态字段 (Status)

#### 统一格式：`status` (所有层级相同)

**标准状态值**:
```python
class PhaseStatus(str, Enum):
    LOCKED = "locked"        # 依赖未满足
    READY = "ready"          # 可以开始
    RUNNING = "running"      # 执行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"        # 失败
    CANCELLED = "cancelled"  # 已取消
```

---

### 6. 进度字段 (Progress)

| 层级 | 命名 | 类型 | 说明 |
|------|------|------|------|
| **后端Python** | `overall_progress` | `float` | 整体进度（0-100） |
| **后端API** | `overall_progress` | `number` | JSON响应 |
| **前端TypeScript** | `overallProgress` | `number` | 变量名 |

---

## 🔧 自动转换工具

### Pydantic Alias (后端)

```python
from pydantic import BaseModel, Field

class Episode(BaseModel):
    episode_id: str = Field(..., description="集数ID，如 ep01")
    episode_name: str = Field(..., alias="name")  # 接受 name，存为 episode_name
    
    class Config:
        populate_by_name = True  # 允许两种名称

# 使用
episode = Episode(episode_id="ep01", name="第一集")
episode.model_dump()  # {"episode_id": "ep01", "episode_name": "第一集"}
episode.model_dump(by_alias=True)  # {"episode_id": "ep01", "name": "第一集"}
```

### TypeScript Transformer (前端)

```typescript
// 自动转换 snake_case ↔ camelCase
import { camelCase, snakeCase } from 'lodash';

// API请求时转换
function toSnakeCase(obj: any): any {
  if (Array.isArray(obj)) return obj.map(toSnakeCase);
  if (obj !== null && typeof obj === 'object') {
    return Object.keys(obj).reduce((acc, key) => {
      acc[snakeCase(key)] = toSnakeCase(obj[key]);
      return acc;
    }, {} as any);
  }
  return obj;
}

// API响应时转换
function toCamelCase(obj: any): any {
  if (Array.isArray(obj)) return obj.map(toCamelCase);
  if (obj !== null && typeof obj === 'object') {
    return Object.keys(obj).reduce((acc, key) => {
      acc[camelCase(key)] = toCamelCase(obj[key]);
      return acc;
    }, {} as any);
  }
  return obj;
}

// 封装API调用
async function apiCall(url: string, data: any) {
  const response = await fetch(url, {
    method: 'POST',
    body: JSON.stringify(toSnakeCase(data))
  });
  return toCamelCase(await response.json());
}
```

---

## 📝 迁移检查清单

### 后端代码

- [ ] 所有函数参数使用 `episode_id: str`（不是 `episode` 或 `ep`）
- [ ] 文件路径使用 `{episode_id}.srt`（如 `ep01.srt`）
- [ ] API路由使用 `/{episode_id}`
- [ ] Pydantic模型添加 `populate_by_name = True`

### 前端代码

- [ ] TypeScript接口使用 `episodeId: string`
- [ ] 变量命名使用 `episodeId`（不是 `episode` 或 `ep`）
- [ ] API调用使用转换函数

### 数据文件

- [ ] 文件名使用 `ep01.srt`, `ep01.json`
- [ ] meta.json 中数组使用 `["ep01", "ep02"]`
- [ ] 不使用纯数字或其他格式

---

## 🚨 常见错误

### 错误1: 命名不一致
```python
# ❌ 错误
def process(ep: str):  # 参数名太短
    path = f"episode_{ep}.srt"  # 格式不统一

# ✅ 正确
def process(episode_id: str):
    path = f"{episode_id}.srt"  # "ep01.srt"
```

### 错误2: 前端未转换
```typescript
// ❌ 错误
const data = { episode_id: "ep01" };  // 前端应该用 camelCase

// ✅ 正确
const data = { episodeId: "ep01" };
apiCall('/start', data);  // 自动转换为 episode_id
```

### 错误3: 文件名不规范
```bash
# ❌ 错误
ep_01.srt  # 下划线不统一
episode01.srt  # 太长
1.srt  # 纯数字不直观

# ✅ 正确
ep01.srt  # 简洁、统一、直观
```

---

## 📚 参考

- [PEP 8 - Python命名规范](https://peps.python.org/pep-0008/)
- [Google TypeScript Style Guide](https://google.github.io/styleguide/tsguide.html)
- [Pydantic Field Aliases](https://docs.pydantic.dev/latest/usage/model_config/#alias-generator)

---

**最后更新**: 2026-02-12  
**维护者**: Project Team
