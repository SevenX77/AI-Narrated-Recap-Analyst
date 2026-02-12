# NovelChapterDetector - 小说章节检测工具

## 职责 (Responsibility)

识别章节标题模式，提取章节序号和标题，计算章节位置信息，验证章节连续性。

**所属阶段**: 小说章节检测（Phase 0）
**工具链位置**: NovelImporter → NovelChapterDetector → NovelSegmenter

## 接口定义 (Interface)

### 函数签名

```python
def execute(
    self,
    novel_file: Union[str, Path],
    validate_continuity: bool = True
) -> List[ChapterInfo]
```

### 输入参数

| 参数 | 类型 | 默认值 | 说明 |
|-----|------|--------|------|
| `novel_file` | `str \| Path` | 必填 | 小说文件路径 |
| `validate_continuity` | `bool` | `True` | 是否验证章节连续性 |

### 输出结果

**类型**: `List[ChapterInfo]`

**ChapterInfo 结构**:
```python
ChapterInfo(
    number: int,          # 章节序号
    title: str,           # 章节标题
    start_line: int,      # 起始行号（标题所在行）
    end_line: int,        # 结束行号（下一章开始前）
    start_char: int,      # 起始字符位置
    end_char: int,        # 结束字符位置
    word_count: int       # 章节字数（不含标题）
)
```

## 实现逻辑 (Logic)

### 核心流程

1. **读取文件**
   - 使用 UTF-8 编码读取
   - 按行分割

2. **检测章节边界**
   - 遍历每一行
   - 尝试匹配章节标题模式
   - 提取章节号和标题

3. **验证章节连续性**（可选）
   - 检查章节号是否连续
   - 检查是否从第1章开始
   - 记录警告（不抛出异常）

4. **计算位置信息**
   - 确定每章的起止行号
   - 计算字符位置（累计每行长度 + 1）
   - 统计章节字数（不含标题行）

### 章节标题匹配模式

**优先级从高到低**：

1. `=== 第1章 标题 ===`
2. `=== 第1章 ===`
3. `第1章：标题`
4. `第1章 标题`
5. `Chapter 1: Title`

**正则表达式**：
```python
CHAPTER_PATTERNS = [
    r'^===\s*第\s*(\d+)\s*章\s*(.*)===',     # === 第1章 标题 ===
    r'^===\s*第\s*(\d+)\s*章\s*===',          # === 第1章 ===
    r'^第\s*(\d+)\s*章[：:\s]+(.+)',          # 第1章：标题
    r'^第\s*(\d+)\s*章\s*(.+)',               # 第1章 标题
    r'^Chapter\s+(\d+)[：:\s]*(.*)$',         # Chapter 1: Title
]
```

## 依赖关系 (Dependencies)

### Schema 依赖

**位置**: `src/core/schemas_novel.py`

- `ChapterInfo` - 章节信息

### 无Tool依赖

本工具不依赖其他工具。

## 代码示例 (Usage Example)

```python
from src.tools.novel_chapter_detector import NovelChapterDetector

# 初始化工具
detector = NovelChapterDetector()

# 检测章节
chapters = detector.execute(
    novel_file="data/projects/超凡公路/raw/novel.txt",
    validate_continuity=True
)

# 访问结果
print(f"检测到 {len(chapters)} 章")

# 遍历章节
for chapter in chapters:
    print(f"第 {chapter.number} 章：{chapter.title}")
    print(f"  行号：{chapter.start_line}-{chapter.end_line}")
    print(f"  字符位置：{chapter.start_char}-{chapter.end_char}")
    print(f"  字数：{chapter.word_count}")

# 提取特定章节内容
chapter_1 = chapters[0]
with open("data/projects/超凡公路/raw/novel.txt", 'r', encoding='utf-8') as f:
    content = f.read()
chapter_1_content = content[chapter_1.start_char:chapter_1.end_char]
print(chapter_1_content)
```

## 输出格式 (Output Format)

### JSON 输出示例

```json
[
  {
    "number": 1,
    "title": "车队第一铁律",
    "start_line": 10,
    "end_line": 125,
    "start_char": 852,
    "end_char": 8542,
    "word_count": 2850
  },
  {
    "number": 2,
    "title": "公路上的危险",
    "start_line": 125,
    "end_line": 250,
    "start_char": 8542,
    "end_char": 16234,
    "word_count": 3120
  }
]
```

## 错误处理 (Error Handling)

### 常见错误

1. **文件不存在**
   - 抛出 `FileNotFoundError`
   - 提示文件路径

2. **未检测到章节**
   - 抛出 `ValueError`
   - 提示检查章节标题格式

3. **章节不连续**（验证模式）
   - 记录警告日志
   - 不抛出异常（允许跳章节）

4. **不从第1章开始**（验证模式）
   - 记录警告日志
   - 不抛出异常

### 日志级别

- `INFO`: 检测进度、章节总数
- `WARNING`: 章节不连续、不从第1章开始
- `DEBUG`: 每个章节的检测详情

## 性能特征 (Performance)

### 处理速度

- **小文件（<1MB）**：<1秒
- **中文件（1-10MB）**：1-3秒
- **大文件（10-50MB）**：3-10秒

### 内存占用

- 读取文件：约 文件大小 × 1.2
- 章节列表：约 章节数 × 1KB

## 中文数字支持 (Chinese Number Support)

### 当前支持

- 单个中文数字：一、二、三...十
- 简单组合：十、百、千、万

### 待完善

- 复杂组合：二十三、一百零五等
- 需要完整的中文数字转换算法

### 映射表

```python
CN_NUM = {
    '零': 0, '一': 1, '二': 2, '三': 3, '四': 4,
    '五': 5, '六': 6, '七': 7, '八': 8, '九': 9,
    '十': 10, '百': 100, '千': 1000, '万': 10000
}
```

## 注意事项 (Notes)

### 章节标题格式

- 建议使用标准格式：`=== 第X章 标题 ===`
- 确保章节标题独占一行
- 避免标题中包含额外的空行

### 章节连续性

- 默认验证章节连续性
- 只记录警告，不阻止处理
- 某些小说可能故意跳章节（番外、插曲）

### 字符位置计算

- 行号是 0-based（内部）
- 输出时转换为 1-based
- 字符位置包含换行符（+1）

### 与其他工具的配合

1. **NovelImporter**：
   - 先导入并规范化
   - 再使用 NovelChapterDetector 检测

2. **NovelSegmenter**：
   - 使用检测结果提取章节内容
   - 按章节分段处理

## 扩展性 (Extensibility)

### 添加新的标题模式

在 `CHAPTER_PATTERNS` 列表中添加新的正则表达式：

```python
CHAPTER_PATTERNS = [
    # 现有模式
    r'^===\s*第\s*(\d+)\s*章\s*(.*)===',
    
    # 新增模式（示例）
    r'^【第\s*(\d+)\s*章】\s*(.+)',  # 【第1章】标题
]
```

### 自定义验证规则

重写 `_validate_continuity()` 方法以实现自定义验证逻辑。

---

**最后更新**: 2026-02-09
**实现状态**: ✅ 已完成并测试
