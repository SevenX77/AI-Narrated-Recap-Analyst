# Preprocess Service (自动预处理服务)

## 职责 (Responsibility)
`PreprocessService` 负责在文件上传后自动执行初始化处理流程，将原始文件（raw）转换为标准化的中间格式（processed），为后续的分析工作流做好准备。

## 接口 (Interface)

### 主要方法
`preprocess_project(project_id: str) -> Dict[str, Any]`

### 输入 (Input)
- `project_id` (str): 项目ID，用于定位数据目录。

### 输出 (Output)
返回处理结果统计字典：
```json
{
    "success": true,
    "novel_processed": true,
    "script_episodes_processed": 3,
    "errors": []
}
```

## 实现逻辑 (Implementation Logic)

### 1. Novel 处理链
针对 `raw/novel/` 或 `raw/` 下的 `.txt` 文件：
1. **导入 (NovelImporter)**: 检测文件编码，转换为 UTF-8，清理特殊字符。
2. **章节检测 (NovelChapterDetector)**: 识别章节标题，生成章节索引。
3. **元数据提取 (NovelMetadataExtractor)**: 调用 LLM (DeepSeek) 提取标题、作者、标签和简介。
4. **保存**: 结果保存至 `processed/novel/` (chapters.json, metadata.json)。

### 2. Script 处理链
针对 `raw/srt/` 或 `raw/` 下的 `.srt` 文件：
1. **导入 (SrtImporter)**: 解析 SRT 格式，提取时间戳和文本。
2. **文本提取 (SrtTextExtractor)**: 调用 LLM (DeepSeek) 合并碎片化字幕，添加标点符号，还原对话句子。
3. **保存**: 结果保存至 `processed/script/` (epXX.json, episodes.json)。

### 3. 状态管理
- 服务会实时更新 `ProjectManagerV2` 中的 `preprocess` 阶段状态（PENDING -> RUNNING -> COMPLETED/FAILED）。
- 每个子任务（如 "Novel: file.txt", "Script: ep01.srt"）的状态也会被追踪。

## 依赖 (Dependencies)
- **Tools**:
  - `NovelImporter`
  - `NovelChapterDetector`
  - `NovelMetadataExtractor`
  - `SrtImporter`
  - `SrtTextExtractor`
- **Managers**:
  - `ProjectManagerV2`: 用于更新项目状态和元数据。
- **Config**:
  - `config.data_dir`: 数据存储根目录。

## 示例代码 (Code Example)

```python
from src.workflows.preprocess_service import preprocess_service

# 触发预处理（通常在文件上传API中调用）
result = preprocess_service.preprocess_project("PROJ_001")

if result["success"]:
    print(f"预处理成功: {result}")
else:
    print(f"预处理失败: {result['errors']}")
```
