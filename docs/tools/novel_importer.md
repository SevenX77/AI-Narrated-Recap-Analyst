# NovelImporter - 小说导入工具

## 职责 (Responsibility)

读取并规范化小说文件，自动检测编码、统一格式，保存到项目标准位置。是小说处理工具链的起点。

**所属阶段**: 素材导入（Phase 0）
**工具链位置**: 工具链起点 → NovelImporter → NovelMetadataExtractor / NovelChapterDetector

## 接口定义 (Interface)

### 函数签名

```python
def execute(
    self, 
    source_file: Union[str, Path],
    project_name: str,
    save_to_disk: bool = True,
    include_content: bool = False
) -> NovelImportResult
```

### 输入参数

| 参数 | 类型 | 默认值 | 说明 |
|-----|------|--------|------|
| `source_file` | `str \| Path` | 必填 | 原始小说文件路径（任意位置） |
| `project_name` | `str` | 必填 | 项目名称（用于确定保存位置） |
| `save_to_disk` | `bool` | `True` | 是否保存到磁盘（False用于仅内存处理） |
| `include_content` | `bool` | `False` | 是否在返回结果中包含文本内容（用于Workflow内存传递） |

### 输出结果

**类型**: `NovelImportResult`

**结构**:
```python
NovelImportResult(
    saved_path: str,                    # 保存路径
    original_path: str,                 # 原始文件路径
    project_name: str,                  # 项目名称
    encoding: str,                      # 文件编码
    file_size: int,                     # 文件大小（字节）
    line_count: int,                    # 行数
    char_count: int,                    # 字符数
    has_bom: bool,                      # 是否包含BOM标记
    normalization_applied: List[str],   # 应用的规范化操作
    content: Optional[str] = None       # 文本内容（可选）
)
```

## 实现逻辑 (Logic)

### 核心流程

1. **文件验证**
   - 检查文件是否存在
   - 检查是否为文件（非目录）
   - 检查文件大小（最大 50MB）

2. **编码检测**
   - 优先使用 `chardet` 库检测编码
   - 读取前 10KB 进行检测
   - 置信度阈值：0.7

3. **读取文件**
   - 尝试使用检测到的编码读取
   - 失败时尝试降级编码列表：
     - `utf-8`
     - `gbk`
     - `gb2312`
     - `gb18030`
     - `big5`
     - `latin1`
   - 最终降级：`utf-8` + 忽略错误

4. **规范化处理**
   - **去除BOM标记**：移除 `\ufeff`
   - **统一换行符**：`\r\n` → `\n`，`\r` → `\n`
   - **合并多余空行**：连续多个空行 → 单个空行
   - **章节标题前添加空行**：便于区分章节
   - **去除首尾空白**

5. **内容验证**
   - 检查内容非空
   - 检查最小长度（100字符）
   - 检查有效行数（至少10行）

6. **保存到项目目录**
   - 创建目录结构：`data/projects/{project_name}/raw/`
   - 保存为：`novel.txt`
   - 使用 UTF-8 编码

## 依赖关系 (Dependencies)

### Schema 依赖

**位置**: `src/core/schemas_novel.py`

- `NovelImportResult` - 导入结果

### 外部库依赖

**可选依赖**:
- `chardet` - 编码检测（推荐）
  - 如果不可用，使用降级策略（假设 UTF-8，低置信度）

### 无Tool依赖

本工具是工具链起点，不依赖其他工具。

## 代码示例 (Usage Example)

```python
from src.tools.novel_importer import NovelImporter

# 初始化工具
importer = NovelImporter()

# 基础用法
result = importer.execute(
    source_file="分析资料/小说/超凡公路.txt",
    project_name="末哥超凡公路"
)

# 访问结果
print(f"保存路径：{result.saved_path}")
print(f"原始编码：{result.encoding}")
print(f"字符数：{result.char_count}")
print(f"应用的规范化：{result.normalization_applied}")

# 内存模式（不保存到磁盘）
result = importer.execute(
    source_file="分析资料/小说/超凡公路.txt",
    project_name="末哥超凡公路",
    save_to_disk=False,
    include_content=True
)
content = result.content
# 在内存中使用 content，不写入磁盘
```

## 输出格式 (Output Format)

### JSON 输出示例

```json
{
  "saved_path": "data/projects/末哥超凡公路/raw/novel.txt",
  "original_path": "分析资料/小说/超凡公路.txt",
  "project_name": "末哥超凡公路",
  "encoding": "gbk",
  "file_size": 2458300,
  "line_count": 8542,
  "char_count": 245830,
  "has_bom": false,
  "normalization_applied": [
    "unified_newlines",
    "merged_empty_lines",
    "added_chapter_spacing",
    "stripped_whitespace"
  ],
  "content": null
}
```

## 错误处理 (Error Handling)

### 常见错误

1. **文件不存在**
   - 抛出 `FileNotFoundError`
   - 提示文件路径

2. **文件过大**
   - 抛出 `ValueError`
   - 提示文件大小和限制

3. **所有编码尝试失败**
   - 使用 `utf-8` + 忽略错误
   - 记录警告日志
   - 返回编码：`utf-8 (with errors ignored)`

4. **内容验证失败**
   - 抛出 `ValueError`
   - 提示失败原因（空文件、内容过短、有效行数不足）

### 日志级别

- `INFO`: 处理进度、编码检测结果
- `WARNING`: 编码检测置信度低、降级编码、忽略错误
- `DEBUG`: 文件验证、规范化操作详情

## 配置常量 (Configuration)

### 可配置项

```python
MAX_FILE_SIZE_MB = 50              # 最大文件大小（MB）
MIN_CONTENT_LENGTH = 100           # 最小内容长度（字符）
ENCODING_CONFIDENCE_THRESHOLD = 0.7  # 编码检测置信度阈值
ENCODING_DETECT_BYTES = 10240      # 编码检测采样大小（10KB）

# 降级编码列表（按优先级）
FALLBACK_ENCODINGS = [
    'utf-8', 'gbk', 'gb2312', 
    'gb18030', 'big5', 'latin1'
]
```

## 性能特征 (Performance)

### 处理速度

- **小文件（<1MB）**：<1秒
- **中文件（1-10MB）**：1-3秒
- **大文件（10-50MB）**：3-10秒

### 内存占用

- **编码检测**：约 10KB
- **文件读取**：约 文件大小 × 1.5
- **规范化处理**：约 文件大小 × 2

## 规范化操作说明 (Normalization Details)

### removed_bom

移除 Unicode BOM 标记（`\ufeff`）

**影响**：
- 避免文本开头的隐藏字符
- 确保跨平台兼容性

### unified_newlines

统一换行符为 `\n`

**影响**：
- `\r\n`（Windows）→ `\n`
- `\r`（旧Mac）→ `\n`

### merged_empty_lines

合并连续空行为单个空行

**影响**：
- 减少文件大小
- 保持可读性

### added_chapter_spacing

在章节标题前添加空行

**影响**：
- 便于章节检测
- 提高可读性

### stripped_whitespace

去除首尾空白

**影响**：
- 移除文件开头和结尾的空行/空格
- 规范化文件结构

## 注意事项 (Notes)

### 编码检测

- `chardet` 库是可选依赖
- 如果不可用，使用降级策略（假设 UTF-8）
- 建议安装 `chardet`：`pip install chardet`

### 文件大小限制

- 默认最大 50MB
- 超大文件建议分章处理

### 保存位置

- 始终保存为：`data/projects/{project_name}/raw/novel.txt`
- 自动创建目录结构

---

**最后更新**: 2026-02-09
**实现状态**: ✅ 已完成并测试
