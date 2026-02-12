# SrtImporter - SRT导入工具

## 职责 (Responsibility)

读取、解析并规范化SRT字幕文件，自动检测编码、验证时间轴格式、修复常见格式错误，保存到项目标准位置。

**所属阶段**: 素材导入（Phase 0）
**工具链位置**: 工具链起点 → SrtImporter → SrtTextExtractor

## 接口定义 (Interface)

### 函数签名

```python
def execute(
    self,
    source_file: Union[str, Path],
    project_name: str,
    episode_name: Optional[str] = None,
    save_to_disk: bool = True,
    include_entries: bool = True
) -> SrtImportResult
```

### 输入参数

| 参数 | 类型 | 默认值 | 说明 |
|-----|------|--------|------|
| `source_file` | `str \| Path` | 必填 | 原始SRT文件路径 |
| `project_name` | `str` | 必填 | 项目名称 |
| `episode_name` | `str` | `None` | 集数名称（如 "ep01"，不提供则从文件名推断） |
| `save_to_disk` | `bool` | `True` | 是否保存到磁盘 |
| `include_entries` | `bool` | `True` | 是否在返回结果中包含SRT条目列表 |

### 输出结果

**类型**: `SrtImportResult`

**结构**:
```python
SrtImportResult(
    saved_path: str,                    # 保存路径
    original_path: str,                 # 原始文件路径
    project_name: str,                  # 项目名称
    episode_name: str,                  # 集数名称
    encoding: str,                      # 文件编码
    entry_count: int,                   # SRT条目数
    total_duration: str,                # 总时长（SRT格式）
    file_size: int,                     # 文件大小（字节）
    normalization_applied: List[str],   # 应用的规范化操作
    entries: Optional[List[SrtEntry]] = None  # SRT条目列表（可选）
)
```

**SrtEntry 结构**:
```python
SrtEntry(
    index: int,           # 序号
    start_time: str,      # 起始时间（HH:MM:SS,mmm）
    end_time: str,        # 结束时间（HH:MM:SS,mmm）
    text: str             # 字幕文本
)
```

## 实现逻辑 (Logic)

### 核心流程

1. **文件验证**
   - 检查文件是否存在
   - 检查文件大小（最大 20MB）

2. **编码检测**
   - 优先使用 `chardet` 库检测编码
   - 读取前 10KB 进行检测
   - 置信度阈值：0.7

3. **读取文件**
   - 尝试使用检测到的编码读取
   - 失败时尝试降级编码列表
   - 最终降级：`utf-8` + 忽略错误

4. **规范化处理**
   - **去除BOM标记**
   - **统一换行符**：`\r\n` → `\n`
   - **修复时间轴格式**：`->` 或 `=>` → `-->`

5. **解析SRT格式**
   - 按空行分割块
   - 每块解析：序号、时间轴、文本
   - 跳过不完整的块

6. **验证SRT质量**
   - 检查最小条目数（10条）
   - 检查时间轴连续性（警告级别）

7. **保存到项目目录**
   - 创建目录结构：`data/projects/{project_name}/raw/`
   - 保存为：`{episode_name}.srt`

### SRT格式标准

```
1
00:00:01,000 --> 00:00:03,500
第一句字幕

2
00:00:03,500 --> 00:00:06,000
第二句字幕
```

**格式要求**:
1. 序号（整数）
2. 时间轴（`HH:MM:SS,mmm --> HH:MM:SS,mmm`）
3. 字幕文本（可多行）
4. 空行分隔

## 依赖关系 (Dependencies)

### Schema 依赖

**位置**: `src/core/schemas_script.py`

- `SrtImportResult` - 导入结果
- `SrtEntry` - SRT条目

### 外部库依赖

**可选依赖**:
- `chardet` - 编码检测（推荐）
  - 如果不可用，使用降级策略

### 无Tool依赖

本工具是工具链起点，不依赖其他工具。

## 代码示例 (Usage Example)

```python
from src.tools.srt_importer import SrtImporter

# 初始化工具
importer = SrtImporter()

# 基础用法
result = importer.execute(
    source_file="分析资料/字幕/ep01.srt",
    project_name="末哥超凡公路",
    episode_name="ep01"
)

# 访问结果
print(f"保存路径：{result.saved_path}")
print(f"条目数：{result.entry_count}")
print(f"总时长：{result.total_duration}")
print(f"应用的规范化：{result.normalization_applied}")

# 访问SRT条目
if result.entries:
    for entry in result.entries[:5]:
        print(f"{entry.index}: {entry.start_time} - {entry.end_time}")
        print(f"  {entry.text}")

# 内存模式（不保存到磁盘）
result = importer.execute(
    source_file="分析资料/字幕/ep01.srt",
    project_name="末哥超凡公路",
    episode_name="ep01",
    save_to_disk=False,
    include_entries=True
)
# 在内存中使用 result.entries
```

## 输出格式 (Output Format)

### JSON 输出示例

```json
{
  "saved_path": "data/projects/末哥超凡公路/raw/ep01.srt",
  "original_path": "分析资料/字幕/ep01.srt",
  "project_name": "末哥超凡公路",
  "episode_name": "ep01",
  "encoding": "utf-8",
  "entry_count": 524,
  "total_duration": "00:25:32,450",
  "file_size": 45820,
  "normalization_applied": [
    "unified_newlines",
    "fixed_time_format"
  ],
  "entries": [
    {
      "index": 1,
      "start_time": "00:00:01,000",
      "end_time": "00:00:03,500",
      "text": "收音机里传来消息"
    }
  ]
}
```

## 错误处理 (Error Handling)

### 常见错误

1. **文件不存在**
   - 抛出 `FileNotFoundError`

2. **文件过大**
   - 抛出 `ValueError`
   - 提示文件大小和限制（20MB）

3. **编码检测失败**
   - 使用降级编码列表
   - 记录警告日志

4. **无有效SRT条目**
   - 抛出 `ValueError`
   - 提示检查SRT格式

5. **条目数过少**
   - 抛出 `ValueError`
   - 提示最小条目数（10条）

### 日志级别

- `INFO`: 处理进度、统计信息
- `WARNING`: 编码检测失败、时间轴不连续、解析失败的块
- `DEBUG`: 详细的解析过程

## 配置常量 (Configuration)

### 可配置项

```python
MAX_FILE_SIZE_MB = 20              # 最大文件大小（MB）
MIN_ENTRY_COUNT = 10               # 最小条目数
ENCODING_CONFIDENCE_THRESHOLD = 0.7  # 编码检测置信度阈值
ENCODING_DETECT_BYTES = 10240      # 编码检测采样大小（10KB）

# 降级编码列表
FALLBACK_ENCODINGS = [
    'utf-8', 'gbk', 'gb2312', 
    'gb18030', 'latin1'
]

# SRT时间戳格式正则
TIME_PATTERN = re.compile(
    r'(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})'
)
```

## 规范化操作说明 (Normalization Details)

### removed_bom

移除 Unicode BOM 标记（`\ufeff`）

### unified_newlines

统一换行符为 `\n`

### fixed_time_format

修复时间轴箭头格式：
- `->` → `-->`
- `=>` → `-->`
- 确保箭头两侧有空格

## 时间轴验证 (Timeline Validation)

### 连续性检查

检查相邻条目的时间是否连续：
- 前一条的结束时间 <= 当前条的起始时间

**如果不连续**:
- 统计不连续的数量
- 记录警告日志
- 不阻止处理（只是警告）

### 格式验证

验证时间戳格式：
- `HH:MM:SS,mmm`
- 例如：`00:12:34,567`

**如果格式错误**:
- 跳过该条目
- 记录警告日志

## 性能特征 (Performance)

### 处理速度

- **小文件（<1MB）**：<1秒
- **中文件（1-10MB）**：1-3秒
- **大文件（10-20MB）**：3-8秒

### 内存占用

- **编码检测**：约 10KB
- **文件读取**：约 文件大小 × 1.5
- **SRT解析**：约 条目数 × 500 字节

## 常见SRT格式问题处理

### 问题1：时间轴箭头格式不统一

**原始**:
```
1
00:00:01,000->00:00:03,500
字幕
```

**修复后**:
```
1
00:00:01,000 --> 00:00:03,500
字幕
```

### 问题2：编码问题导致乱码

**解决**:
- 使用 `chardet` 自动检测编码
- 尝试多种编码降级
- 最终使用 `utf-8` + 忽略错误

### 问题3：缺少空行分隔

**解决**:
- 按 `\n\n` 分割块
- 自动处理缺少空行的情况

## 注意事项 (Notes)

### 集数名称推断

- 如果不提供 `episode_name`，从文件名推断
- 示例：`ep01.srt` → `ep01`

### 保存位置

- 始终保存为：`data/projects/{project_name}/raw/{episode_name}.srt`
- 自动创建目录结构

### 与 NovelImporter 的对比

| 特性 | SrtImporter | NovelImporter |
|-----|-------------|---------------|
| 文件类型 | SRT字幕 | 小说文本 |
| 格式解析 | SRT三段式 | 纯文本 |
| 最大文件大小 | 20MB | 50MB |
| 规范化操作 | BOM+换行+时间轴 | BOM+换行+章节空行 |
| 输出结构 | 条目列表 | 纯文本 |

---

**最后更新**: 2026-02-09
**实现状态**: ✅ 已完成并测试
