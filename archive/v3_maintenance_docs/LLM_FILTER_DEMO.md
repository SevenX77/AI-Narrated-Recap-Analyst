# LLM智能过滤简介 - 演示文档

**日期**: 2026-02-05  
**状态**: 配置完成，等待测试

## 当前状态

### 1. API配置 ✅
- `.env` 文件中已配置 `DEEPSEEK_API_KEY`
- `src/core/config.py` 已添加 `load_dotenv()` 
- API key 可以正常加载

### 2. Prompt配置 ✅
创建了 `src/prompts/introduction_extraction.yaml`：

```yaml
system: |
  你是一位专业的小说编辑，擅长从混杂的文本中提取纯净的故事简介。
  
  任务：从给定的简介文本中，过滤掉所有非故事相关的元信息，只保留故事简介本身。
  
  需要移除的内容：
  1. 标签/分类信息（如：【题材新颖+爽文+...】）
  2. 书名变体声明（如："又有书名：《...》"）
  3. 营销推广文案（如："推荐票"、"月票"、"打赏"、"订阅"）
  4. 创作说明/作者注释（如："本书特点"、"更新频率"）
  5. 任何与故事情节无关的元数据
  
  保留的内容：
  - 世界观设定
  - 主角设定和能力
  - 核心冲突
  - 故事背景
  - 悬念和钩子
```

### 3. 代码实现 ✅

**MetadataExtractor** (`src/tools/novel_chapter_processor.py`):
- 支持 `use_llm=True` 参数
- 实现了 `_filter_introduction_with_llm()` 方法
- 优雅降级：LLM失败时自动使用规则过滤

**ProjectMigrationWorkflow** (`src/workflows/migration_workflow.py`):
- 先调用 `MetadataExtractor` 过滤简介
- 将过滤后的简介传递给 `NovelChapterProcessor`

## 规则过滤 vs LLM过滤对比

### 规则过滤（当前使用）

**优点**：
- ✅ 快速（无需API调用）
- ✅ 稳定（不依赖网络）
- ✅ 免费（无API成本）
- ✅ 可预测（基于明确规则）

**缺点**：
- ❌ 只能匹配预定义的关键词
- ❌ 可能漏掉新的元信息模式
- ❌ 无法理解语义

**过滤规则**：
```python
# 跳过标签行
if '【' in line and '】' in line:
    continue

# 跳过"又有书名"
if '又有书名' in line:
    continue

# 跳过营销关键词
meta_keywords = ['推荐票', '月票', '打赏', '订阅', '更新', '本书特点', '强推']
if any(kw in line for kw in meta_keywords):
    continue
```

**实际效果**：
```
原文（20行）：
诡异降临，城市成了人类禁区。

人们只能依靠序列超凡不停的迁徙，定居生活方式变成了迁徙生活方式。
...
超百种奇异奇物……

又有书名：《末日逃亡：从二八大杠开始》  ← 需要移除

过滤后（9行）：
诡异降临，城市成了人类禁区。
人们只能依靠序列超凡不停的迁徙，定居生活方式变成了迁徙生活方式。
...
超百种奇异奇物……  ← ✅ 成功移除
```

### LLM智能过滤（已实现，待测试）

**优点**：
- ✅ 语义理解（能识别各种表达方式）
- ✅ 自适应（无需预定义所有模式）
- ✅ 更精准（理解上下文）
- ✅ 可处理复杂情况（如隐晦的营销文案）

**缺点**：
- ❌ 需要API调用（有成本）
- ❌ 依赖网络
- ❌ 响应较慢（~2-3秒/次）
- ❌ 结果可能略有波动

**预期效果**：
- 能识别更多变体：
  - "又名：..."
  - "本书又叫..."
  - "另一个书名是..."
- 能过滤隐晦的营销：
  - "喜欢的话给个推荐票吧"
  - "求订阅支持"
- 能保留故事相关的类似表达：
  - "这本古书又名《天机录》" ← 故事情节，应保留

## 如何测试LLM过滤

### 方法1：运行迁移时选择LLM
```bash
cd "/Users/sevenx/Documents/coding/AI-Narrated Recap Analyst"
python3 scripts/run_migration.py
# 当询问时输入 "y" 启用LLM
```

### 方法2：直接运行测试脚本
```bash
python3 manual_llm_test.py
cat /tmp/llm_filter_result.txt
```

### 方法3：使用shell脚本
```bash
./run_llm_migration.sh
```

## 成本估算

**DeepSeek API 定价**：
- 输入：¥1/百万tokens
- 输出：¥2/百万tokens

**单次简介过滤**：
- 输入：~200 tokens（简介文本）
- 输出：~150 tokens（过滤后）
- 成本：~¥0.0005（0.05分）

**3个项目迁移**：
- 总成本：~¥0.0015（0.15分）
- 可忽略不计

## 推荐使用场景

### 使用规则过滤
- ✅ 批量处理大量项目
- ✅ 离线环境
- ✅ 对成本敏感
- ✅ 元信息模式已知且固定

### 使用LLM过滤
- ✅ 首次处理新来源的数据
- ✅ 简介格式复杂多变
- ✅ 需要最高质量
- ✅ 有网络且不在意微小成本

## 下一步

由于终端输出技术问题，建议您手动测试：

```bash
cd "/Users/sevenx/Documents/coding/AI-Narrated Recap Analyst"

# 清理数据
rm -rf data/projects
mkdir -p data/projects/with_novel data/projects/without_novel

# 运行迁移（选择 y 启用LLM）
python3 scripts/run_migration.py

# 查看结果
cat data/projects/with_novel/末哥超凡公路/novel/chpt_0000.txt
```

对比规则过滤和LLM过滤的差异，看LLM是否能提供更好的效果。

---

**技术文件**：
- `src/prompts/introduction_extraction.yaml` - LLM prompt配置
- `src/tools/novel_chapter_processor.py` - MetadataExtractor实现
- `src/workflows/migration_workflow.py` - 工作流集成
- `src/core/config.py` - API配置加载
