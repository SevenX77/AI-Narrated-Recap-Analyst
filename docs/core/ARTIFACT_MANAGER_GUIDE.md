# ArtifactManager 工作原理详解

**最后更新**: 2026-02-12  
**核心策略**: Latest Pointer + Timestamped Versions  
**文件**: `src/core/artifact_manager.py`

---

## 🎯 设计目标

### 为什么需要 ArtifactManager？

在 AI 工作流中，我们会多次运行同一个工具（如 NovelSegmenter、ScriptSegmenter），每次运行可能：
- 使用不同的参数（如不同的LLM provider）
- 对结果不满意，需要重新运行
- 需要对比不同版本的结果

**问题**：
- ❌ 直接覆盖文件 → 丢失历史版本，无法回滚
- ❌ 手动命名版本 → 容易出错，难以管理
- ❌ 每次都创建新文件 → 不知道哪个是最新的

**解决方案**：
- ✅ 自动版本化管理
- ✅ 始终有明确的"最新版本"
- ✅ 保留历史记录，支持回滚

---

## 📋 核心策略：Latest Pointer + Timestamped Versions

### 策略说明

```
主目录（analyst/novel_analysis/）
├── chapter_001_segmentation_latest.json    # ⭐ Latest Pointer（始终指向最新版本）
│
└── history/                                # 📦 版本存档目录
    ├── chapter_001_segmentation_v20260212_180530.json    # 版本1
    ├── chapter_001_segmentation_v20260212_190000.json    # 版本2
    └── chapter_001_segmentation_v20260212_200000.json    # 版本3（最新）
```

**关键点**：
1. **Latest文件**（`*_latest.json`）：始终是最新版本的**副本**
2. **History目录**：保存所有历史版本（包括最新版本）
3. **时间戳命名**：`v{YYYYMMDD}_{HHMMSS}` 格式，确保唯一性和可排序

---

## 🔄 保存流程详解

### 调用方式

```python
from src.core.artifact_manager import artifact_manager

# 保存分段结果
segmentation_result = NovelSegmenter.execute(...)

artifact_manager.save_artifact(
    content=segmentation_result.model_dump(),
    artifact_type="chapter_001_segmentation",
    project_id="project_001",
    base_dir="data/projects/project_001/analyst/novel_analysis",
    extension="json"
)
```

### 内部执行步骤（5步）

#### Step 1: 生成文件名

```python
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")  # "20260212_180530"

version_filename = f"{artifact_type}_v{timestamp}.{extension}"
# → "chapter_001_segmentation_v20260212_180530.json"

latest_filename = f"{artifact_type}_latest.{extension}"
# → "chapter_001_segmentation_latest.json"
```

**路径生成**：
```python
latest_path = os.path.join(base_dir, latest_filename)
# → "data/projects/project_001/analyst/novel_analysis/chapter_001_segmentation_latest.json"

history_dir = os.path.join(base_dir, "history")
# → "data/projects/project_001/analyst/novel_analysis/history"

version_path = os.path.join(history_dir, version_filename)
# → "data/projects/project_001/analyst/novel_analysis/history/chapter_001_segmentation_v20260212_180530.json"
```

---

#### Step 2: 确保 history/ 目录存在

```python
os.makedirs(history_dir, exist_ok=True)
# 如果 history/ 不存在，创建它
# 如果已存在，不报错
```

**目录结构**：
```
data/projects/project_001/analyst/novel_analysis/
└── history/                              # ✅ 确保存在
```

---

#### Step 3: 清理主目录中的旧版本文件

**问题**：为什么需要这一步？

如果之前有代码直接在主目录保存版本文件（如 `chapter_001_segmentation_v20260211_100000.json`），这些文件会和 `_latest.json` 混在一起，造成混乱。

**解决**：自动将主目录中的旧版本文件移动到 `history/`

```python
import glob

# 查找主目录中的旧版本文件（匹配 *_v*.json 模式）
pattern = os.path.join(base_dir, f"{artifact_type}_v*.{extension}")
# → "data/projects/project_001/analysis/novel/chapter_001_segmentation_v*.json"

existing_versions_in_root = glob.glob(pattern)
# → ["data/.../chapter_001_segmentation_v20260211_100000.json", ...]

moved_count = 0
for old_version in existing_versions_in_root:
    # 只移动主目录中的版本文件（不移动 history/ 中的）
    if os.path.dirname(old_version) == base_dir:
        dest_path = os.path.join(history_dir, os.path.basename(old_version))
        shutil.move(old_version, dest_path)
        moved_count += 1

logger.debug(f"Moved {moved_count} old version(s) to history/")
```

**效果**：
```
执行前:
analyst/novel_analysis/
├── chapter_001_segmentation_latest.json
├── chapter_001_segmentation_v20260211_100000.json    # ⚠️ 旧版本文件（混乱）
└── history/

执行后:
analyst/novel_analysis/
├── chapter_001_segmentation_latest.json
└── history/
    └── chapter_001_segmentation_v20260211_100000.json    # ✅ 移动到history/
```

---

#### Step 4: 保存新版本到 history/

```python
with open(version_path, 'w', encoding='utf-8') as f:
    if extension == "json":
        json.dump(content, f, ensure_ascii=False, indent=2)
    else:
        f.write(str(content))
```

**写入内容**（示例）：
```json
// history/chapter_001_segmentation_v20260212_180530.json
{
  "chapter_id": "chapter_001",
  "total_paragraphs": 50,
  "paragraphs": [
    {
      "paragraph_id": "p001",
      "content": "末日降临的那一天，苏烈正驾驶着卡车...",
      "category": "narrative"
    },
    ...
  ],
  "metadata": {
    "segmented_at": "2026-02-12T18:05:30",
    "tool": "NovelSegmenter",
    "llm_provider": "claude",
    "total_cost": 0.15
  }
}
```

---

#### Step 5: 更新主目录的 latest 文件

```python
shutil.copy2(version_path, latest_path)
# 将 history/chapter_001_segmentation_v20260212_180530.json
# 复制到 chapter_001_segmentation_latest.json
```

**为什么用 copy2 而不是 move？**
- `copy2` 保留文件元数据（修改时间、权限等）
- 保留 history/ 中的版本文件，同时更新 latest 文件

**最终结果**：
```
analyst/novel_analysis/
├── chapter_001_segmentation_latest.json              # ⭐ 最新版本（副本）
│   内容与 history/chapter_001_segmentation_v20260212_180530.json 完全相同
│
└── history/
    ├── chapter_001_segmentation_v20260211_100000.json
    ├── chapter_001_segmentation_v20260212_180530.json    # ⭐ 最新版本（原件）
    └── ...
```

---

#### Step 6: 记录日志并返回

```python
logger.info(f"Saved artifact [{project_id}]: {version_filename} (updated latest)")
return version_path
# 返回版本文件的路径（history/ 中的路径）
```

**日志输出**：
```
INFO: Saved artifact [project_001]: chapter_001_segmentation_v20260212_180530.json (updated latest)
```

---

## 📖 读取流程详解

### 调用方式

```python
# 读取最新版本
result = artifact_manager.load_latest_artifact(
    artifact_type="chapter_001_segmentation",
    base_dir="data/projects/project_001/analyst/novel_analysis",
    extension="json"
)
```

### 内部执行步骤

```python
def load_latest_artifact(artifact_type: str, base_dir: str, extension: str = "json"):
    # 1. 构建 latest 文件路径
    latest_path = os.path.join(base_dir, f"{artifact_type}_latest.{extension}")
    # → "data/.../analysis/novel/chapter_001_segmentation_latest.json"
    
    # 2. 检查文件是否存在
    if not os.path.exists(latest_path):
        return None  # 文件不存在，返回 None
    
    # 3. 读取文件
    with open(latest_path, 'r', encoding='utf-8') as f:
        if extension == "json":
            return json.load(f)  # 返回 dict
        return f.read()          # 返回 str
```

**注意**：
- ✅ 始终读取 `*_latest.json`（不读取 history/ 中的文件）
- ✅ 如果文件不存在，返回 `None`（不抛异常）

---

## 🎨 完整示例

### 场景：处理小说第1章，运行3次

#### 第1次运行（2026-02-12 18:00:00）

```python
# 运行 NovelSegmenter
result_1 = NovelSegmenter.execute(
    chapter_text="...",
    provider="claude"
)

# 保存结果
artifact_manager.save_artifact(
    content=result_1.model_dump(),
    artifact_type="chapter_001_segmentation",
    project_id="project_001",
    base_dir="data/projects/project_001/analyst/novel_analysis"
)
```

**生成的文件**：
```
analyst/novel_analysis/
├── chapter_001_segmentation_latest.json              # ⭐ 版本1
└── history/
    └── chapter_001_segmentation_v20260212_180000.json    # 版本1（原件）
```

---

#### 第2次运行（2026-02-12 19:00:00）- 参数调整

```python
# 使用不同的 LLM provider 重新运行
result_2 = NovelSegmenter.execute(
    chapter_text="...",
    provider="deepseek"  # 换了 provider
)

# 保存结果
artifact_manager.save_artifact(
    content=result_2.model_dump(),
    artifact_type="chapter_001_segmentation",
    project_id="project_001",
    base_dir="data/projects/project_001/analyst/novel_analysis"
)
```

**生成的文件**：
```
analyst/novel_analysis/
├── chapter_001_segmentation_latest.json              # ⭐ 版本2（覆盖）
└── history/
    ├── chapter_001_segmentation_v20260212_180000.json    # 版本1（保留）
    └── chapter_001_segmentation_v20260212_190000.json    # 版本2（新增）
```

**关键变化**：
- `latest.json` 被覆盖为版本2
- 版本1保留在 history/ 中

---

#### 第3次运行（2026-02-12 20:00:00）- 最终优化

```python
# 进一步优化，最终版本
result_3 = NovelSegmenter.execute(
    chapter_text="...",
    provider="claude",  # 换回 claude
    temperature=0.3     # 调整参数
)

# 保存结果
artifact_manager.save_artifact(
    content=result_3.model_dump(),
    artifact_type="chapter_001_segmentation",
    project_id="project_001",
    base_dir="data/projects/project_001/analyst/novel_analysis"
)
```

**最终文件结构**：
```
analyst/novel_analysis/
├── chapter_001_segmentation_latest.json              # ⭐ 版本3（当前使用）
└── history/
    ├── chapter_001_segmentation_v20260212_180000.json    # 版本1（claude）
    ├── chapter_001_segmentation_v20260212_190000.json    # 版本2（deepseek）
    └── chapter_001_segmentation_v20260212_200000.json    # 版本3（claude优化）
```

---

### 读取和对比

#### 读取最新版本（版本3）

```python
latest = artifact_manager.load_latest_artifact(
    artifact_type="chapter_001_segmentation",
    base_dir="data/projects/project_001/analyst/novel_analysis"
)

print(latest["metadata"]["llm_provider"])  # "claude"
print(latest["metadata"]["segmented_at"])  # "2026-02-12T20:00:00"
```

#### 回滚到版本1（手动）

```python
import json

# 读取历史版本
with open("data/.../history/chapter_001_segmentation_v20260212_180000.json", 'r') as f:
    version_1 = json.load(f)

# 对比
print(f"版本1 段落数: {version_1['total_paragraphs']}")
print(f"版本3 段落数: {latest['total_paragraphs']}")

# 如果版本1更好，可以手动复制回去
shutil.copy2(
    "data/.../history/chapter_001_segmentation_v20260212_180000.json",
    "data/.../analysis/novel/chapter_001_segmentation_latest.json"
)
```

---

## 🔍 文件命名规范

### artifact_type 的命名

**格式**：`{chapter_id}_{operation}` 或 `{episode_id}_{operation}`

**示例**：

| artifact_type | 说明 | 生成的文件 |
|--------------|------|----------|
| `chapter_001_segmentation` | 第1章分段 | `chapter_001_segmentation_latest.json` |
| `chapter_001_annotation` | 第1章标注 | `chapter_001_annotation_latest.json` |
| `ep01_segmentation` | 第1集分段 | `ep01_segmentation_latest.json` |
| `ep01_hook` | 第1集Hook检测 | `ep01_hook_latest.json` |
| `system_catalog` | 系统目录 | `system_catalog_latest.json` |
| `chapter_001_ep01_alignment` | 第1章-第1集对齐 | `chapter_001_ep01_alignment_latest.json` |

**规则**：
- ✅ 使用下划线 `_` 连接
- ✅ 使用小写字母
- ✅ 使用标准ID格式（`chapter_001`, `ep01`）
- ❌ 不使用空格或特殊字符

---

## 🚨 常见错误和解决

### 错误1: 直接写入主目录（不使用 ArtifactManager）

```python
# ❌ 错误：直接保存文件
with open("data/.../analyst/novel_analysis/chapter_001_segmentation.json", 'w') as f:
    json.dump(result, f)
```

**问题**：
- 没有版本化管理
- 覆盖历史数据
- 无法回滚

**解决**：
```python
# ✅ 正确：使用 ArtifactManager
artifact_manager.save_artifact(
    content=result,
    artifact_type="chapter_001_segmentation",
    project_id=project_id,
    base_dir=f"{project_dir}/analysis/novel"
)
```

---

### 错误2: 手动创建版本文件名

```python
# ❌ 错误：手动命名版本
timestamp = datetime.now().isoformat()
filename = f"chapter_001_segmentation_{timestamp}.json"
# 问题：时间戳格式不统一，文件名包含冒号（Windows不支持）
```

**问题**：
- 时间戳格式不一致
- 文件名可能包含非法字符
- 没有统一的 latest 指针

**解决**：
```python
# ✅ 正确：让 ArtifactManager 自动处理
artifact_manager.save_artifact(...)
# 自动生成标准格式: chapter_001_segmentation_v20260212_180000.json
```

---

### 错误3: 读取 history/ 中的文件

```python
# ❌ 错误：直接读取版本文件
with open("data/.../history/chapter_001_segmentation_v20260212_180000.json", 'r') as f:
    result = json.load(f)
```

**问题**：
- 不知道哪个是最新版本
- 需要手动查找时间戳

**解决**：
```python
# ✅ 正确：读取 latest 文件
result = artifact_manager.load_latest_artifact(
    artifact_type="chapter_001_segmentation",
    base_dir=f"{project_dir}/analyst/novel_analysis"
)
```

**例外情况**（需要特定版本）：
```python
# 如果明确需要读取历史版本，可以手动读取
import glob
import json

# 列出所有版本
versions = glob.glob("data/.../history/chapter_001_segmentation_v*.json")
versions.sort()  # 按时间戳排序

# 读取第1个版本
with open(versions[0], 'r') as f:
    first_version = json.load(f)
```

---

## 🔧 高级用法

### 1. 对比多个版本

```python
import glob
import json

def compare_versions(artifact_type: str, base_dir: str):
    """对比artifact的所有版本"""
    
    history_dir = os.path.join(base_dir, "history")
    pattern = os.path.join(history_dir, f"{artifact_type}_v*.json")
    versions = sorted(glob.glob(pattern))
    
    for version_path in versions:
        with open(version_path, 'r') as f:
            data = json.load(f)
        
        timestamp = os.path.basename(version_path).split('_v')[1].split('.')[0]
        provider = data.get("metadata", {}).get("llm_provider", "unknown")
        paragraphs = data.get("total_paragraphs", 0)
        cost = data.get("metadata", {}).get("total_cost", 0)
        
        print(f"{timestamp} | {provider:10s} | {paragraphs:3d} paragraphs | ${cost:.2f}")

# 使用
compare_versions(
    artifact_type="chapter_001_segmentation",
    base_dir="data/projects/project_001/analyst/novel_analysis"
)
```

**输出示例**：
```
20260212_180000 | claude     | 50 paragraphs | $0.15
20260212_190000 | deepseek   | 48 paragraphs | $0.05
20260212_200000 | claude     | 52 paragraphs | $0.16
```

---

### 2. 自动清理旧版本（待实现）

```python
def cleanup_old_versions(base_dir: str, keep_days: int = 30):
    """清理超过指定天数的旧版本"""
    
    import time
    from datetime import datetime, timedelta
    
    history_dir = os.path.join(base_dir, "history")
    cutoff_date = datetime.now() - timedelta(days=keep_days)
    
    for filename in os.listdir(history_dir):
        if not filename.endswith(".json"):
            continue
        
        # 提取时间戳
        # 格式: chapter_001_segmentation_v20260212_180000.json
        try:
            timestamp_str = filename.split('_v')[1].split('.')[0]
            file_date = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
            
            if file_date < cutoff_date:
                file_path = os.path.join(history_dir, filename)
                os.remove(file_path)
                print(f"Deleted old version: {filename}")
        except Exception as e:
            print(f"Failed to process {filename}: {e}")

# 使用
cleanup_old_versions(
    base_dir="data/projects/project_001/analyst/novel_analysis",
    keep_days=30
)
```

---

### 3. 导出版本历史

```python
def export_version_history(artifact_type: str, base_dir: str, output_path: str):
    """导出artifact的版本历史为CSV"""
    
    import csv
    import glob
    import json
    
    history_dir = os.path.join(base_dir, "history")
    pattern = os.path.join(history_dir, f"{artifact_type}_v*.json")
    versions = sorted(glob.glob(pattern))
    
    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Timestamp', 'Provider', 'Paragraphs', 'Cost', 'File'])
        
        for version_path in versions:
            with open(version_path, 'r') as f:
                data = json.load(f)
            
            timestamp = os.path.basename(version_path).split('_v')[1].split('.')[0]
            metadata = data.get("metadata", {})
            
            writer.writerow([
                timestamp,
                metadata.get("llm_provider", "unknown"),
                data.get("total_paragraphs", 0),
                metadata.get("total_cost", 0),
                os.path.basename(version_path)
            ])

# 使用
export_version_history(
    artifact_type="chapter_001_segmentation",
    base_dir="data/projects/project_001/analyst/novel_analysis",
    output_path="version_history.csv"
)
```

---

## 📊 性能考虑

### 磁盘空间

**估算**：
- 单个分段结果：~50KB
- 单个标注结果：~200KB
- 单章10个版本：~2.5MB
- 100章10个版本：~250MB

**优化建议**：
1. 定期清理旧版本（保留最近30天）
2. 压缩历史版本（使用 gzip）
3. 归档超过3个月的版本到备份存储

---

### 文件I/O性能

**当前实现**：
- 保存时间：~10ms（50KB JSON）
- 读取时间：~5ms

**优化建议**：
1. 使用内存缓存（Redis）存储 latest 版本
2. 异步保存 history 版本
3. 批量保存多个artifact

---

## 📋 总结

### ArtifactManager 的核心价值

| 问题 | ArtifactManager 的解决方案 |
|------|--------------------------|
| **不知道哪个是最新版本** | ✅ `*_latest.json` 始终指向最新 |
| **覆盖历史数据** | ✅ 所有版本保留在 `history/` |
| **版本命名混乱** | ✅ 统一的时间戳格式 `v{YYYYMMDD}_{HHMMSS}` |
| **无法回滚** | ✅ 可以从 history/ 恢复任意版本 |
| **对比版本困难** | ✅ 可以轻松读取和对比多个版本 |

### 使用建议

1. **始终使用 ArtifactManager**：不要手动创建版本文件
2. **读取 latest 文件**：不要直接读取 history/ 中的文件（除非明确需要特定版本）
3. **统一命名规范**：使用 `{id}_{operation}` 格式
4. **定期清理**：清理超过30天的旧版本
5. **记录元数据**：在保存的数据中包含 `metadata` 字段（tool、provider、cost等）

---

**最后更新**: 2026-02-12  
**维护者**: Project Team
