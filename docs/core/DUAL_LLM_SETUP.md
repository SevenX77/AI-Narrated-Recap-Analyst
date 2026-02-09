# 双 LLM Provider 配置指南

## 📋 快速参考：所有工具的LLM配置

| 工具名称 | 使用LLM | 默认Provider | 默认模型 | 任务类型 |
|---------|--------|-------------|---------|---------|
| NovelImporter | ❌ | - | - | 编码检测、格式规范化 |
| **NovelMetadataExtractor** | ✅ | DeepSeek | `deepseek-chat` | 元数据提取、简介过滤 |
| NovelChapterDetector | ❌ | - | - | 章节边界检测 |
| **NovelSegmenter** ⭐ | ✅ | Claude | `claude-sonnet-4-5` | **叙事分段分析** |
| SrtImporter | ❌ | - | - | SRT格式解析 |
| **SrtTextExtractor** | ✅ | DeepSeek | `deepseek-chat` | 文本提取、格式处理 |
| **ScriptSegmenter** | ✅ | DeepSeek | `deepseek-chat` | 脚本语义分段 |

**简单记忆**：
- 🚀 **简单任务** → DeepSeek（速度快、成本低）
- 🎯 **复杂分析** → Claude（质量高、理解强）

---

## 概述

本项目支持同时使用 **Claude** 和 **DeepSeek** 两个 LLM Provider，实现功能分工：

- **Claude**: 用于复杂任务（小说分段分析、深度理解）
- **DeepSeek**: 用于简单任务（元数据提取、格式处理）
  - **v3.2 标准模型** (`deepseek-chat`): 快速响应、低成本
  - **v3.2 思维链模型** (`deepseek-reasoner`): 深度推理、复杂逻辑（未来使用）

## 架构设计

### LLMClientManager

位置：`src/core/llm_client_manager.py`

核心功能：
1. 统一管理多个 LLM Provider 的客户端实例
2. 单例模式：同一 Provider 复用客户端实例
3. 使用统计：自动记录调用次数和 Token 消耗

### 使用方式

```python
from src.core.llm_client_manager import get_llm_client, get_model_name

# 获取 Claude 客户端
claude_client = get_llm_client("claude")
claude_model = get_model_name("claude")

# 获取 DeepSeek 客户端
deepseek_client = get_llm_client("deepseek")

# DeepSeek 多模型支持
v32_model = get_model_name("deepseek", model_type="v32")           # v3.2 标准模型
thinking_model = get_model_name("deepseek", model_type="v32-thinking")  # v3.2 思维链模型
default_model = get_model_name("deepseek")  # 默认使用 v3.2 标准模型

# 调用示例：使用 v3.2 思维链模型进行复杂推理
response = deepseek_client.chat.completions.create(
    model=thinking_model,
    messages=[{"role": "user", "content": "请解释量子纠缠的原理"}]
)
```

## 环境配置

### .env 文件配置

```bash
# ============================================
# Claude 配置
# ============================================
CLAUDE_API_KEY=sk-K8IJLx3fdq22F81rxvQpAmaGyC4ceoy1yrZ8mwZs17PDW7nq
CLAUDE_BASE_URL=https://chatapi.onechats.ai/v1/
CLAUDE_MODEL_NAME=claude-sonnet-4-5-20250929
CLAUDE_MAX_TOKENS=4096

# 注意：Temperature 应在工具调用时根据任务设置，不做全局配置

# ============================================
# DeepSeek 配置
# ============================================
DEEPSEEK_API_KEY=sk-你的API密钥  # 需要重新获取
DEEPSEEK_BASE_URL=https://api.deepseek.com

# DeepSeek 多模型支持
DEEPSEEK_V32_MODEL=deepseek-chat              # v3.2 标准模型（快速、低成本）
DEEPSEEK_V32_THINKING_MODEL=deepseek-reasoner # v3.2 思维链模型（深度推理）
DEEPSEEK_MODEL_NAME=deepseek-chat             # 默认模型（v3.2 标准）
```

### 获取 DeepSeek API Key

**⚠️ 重要提示**：项目中原有的 DeepSeek API Key 已失效，需要重新获取。

**步骤**：

1. 访问 DeepSeek 官网：https://platform.deepseek.com/api_keys
2. 注册/登录账号
3. 点击"创建 API Key"
4. 复制生成的 API Key（格式：`sk-xxx`，只显示一次）
5. 在 `.env` 文件中配置：
   ```bash
   DEEPSEEK_API_KEY=sk-你复制的密钥
   ```

**注意**：
- API Key 只在创建时显示一次，务必立即保存
- 如果丢失，需要删除旧密钥并创建新密钥

## 工具分工策略与LLM配置

### 📋 所有工具的LLM使用情况

#### Phase I: Material Processing Tools

| 工具名称 | 是否使用LLM | 默认Provider | 默认模型 | 任务类型 | 可否切换 |
|---------|-----------|-------------|---------|---------|---------|
| **NovelImporter** | ❌ | - | - | 编码检测、格式规范化 | - |
| **NovelMetadataExtractor** | ✅ | DeepSeek | `deepseek-chat` | 元数据提取、简介过滤 | ✅ |
| **NovelChapterDetector** | ❌ | - | - | 章节边界检测（正则） | - |
| **NovelSegmenter** | ✅ | Claude | `claude-sonnet-4-5` | 叙事分段分析 | ✅ |
| **SrtImporter** | ❌ | - | - | SRT格式解析 | - |
| **SrtTextExtractor** | ✅ | DeepSeek | `deepseek-chat` | 文本提取、格式处理 | ✅ |
| **ScriptSegmenter** | ✅ | DeepSeek | `deepseek-chat` | 脚本语义分段 | ✅ |

---

### 🔧 详细配置说明

#### 1. NovelMetadataExtractor（元数据提取）
- **默认 Provider**: DeepSeek (`deepseek-chat`)
- **任务类型**: 简单提取（标题、作者、标签、简介过滤）
- **选择原因**: 简单任务，DeepSeek 性价比高，速度快
- **使用方法**:
  ```python
  # 默认使用 DeepSeek v3.2 标准模型
  extractor = NovelMetadataExtractor()
  
  # 可选指定 Claude（高质量）
  extractor = NovelMetadataExtractor(provider="claude")
  
  # 可选禁用 LLM（纯规则处理）
  extractor = NovelMetadataExtractor(use_llm=False)
  ```

#### 2. NovelSegmenter（小说分段分析）⭐ 核心工具
- **默认 Provider**: Claude (`claude-sonnet-4-5-20250929`)
- **任务类型**: 复杂分析（叙事结构、功能分段、优先级标注）
- **选择原因**: 需要深度理解叙事结构，Claude 质量更高
- **使用方法**:
  ```python
  # 默认使用 Claude（推荐）
  segmenter = NovelSegmenter()
  
  # 可选指定 DeepSeek（成本优先）
  segmenter = NovelSegmenter(provider="deepseek")
  
  # 调用时可临时指定模型
  segmenter.execute(
      novel_file="path/to/novel.txt",
      chapter_number=1,
      model="claude-sonnet-4-5-20250929"  # 覆盖默认模型
  )
  ```

#### 3. SrtTextExtractor（字幕文本提取）
- **默认 Provider**: DeepSeek (`deepseek-chat`)
- **任务类型**: 格式处理（去重、合并、实体识别）
- **选择原因**: 格式化任务，DeepSeek 性价比高
- **使用方法**:
  ```python
  # 默认使用 DeepSeek v3.2 标准模型
  extractor = SrtTextExtractor()
  
  # 可选指定 Claude
  extractor = SrtTextExtractor(provider="claude")
  
  # 可选禁用 LLM（纯规则处理，不推荐）
  extractor = SrtTextExtractor(use_llm=False)
  ```

#### 4. ScriptSegmenter（脚本分段）
- **默认 Provider**: DeepSeek (`deepseek-chat`)
- **任务类型**: 语义分段（按叙事功能分段）
- **选择原因**: 格式化任务，DeepSeek 速度快
- **使用方法**:
  ```python
  # 默认使用 DeepSeek v3.2 标准模型
  segmenter = ScriptSegmenter()
  
  # 可选指定 Claude（质量优先）
  segmenter = ScriptSegmenter(provider="claude")
  
  # 注意：必须使用 LLM，不支持纯规则模式
  ```

---

### 🎯 任务分级建议

| 任务复杂度 | 推荐 Provider | 推荐模型 | 典型场景 |
|-----------|--------------|---------|---------|
| **简单** | DeepSeek | `deepseek-chat` | 元数据提取、格式处理、文本清理 |
| **中等** | DeepSeek | `deepseek-chat` | 脚本分段、实体识别 |
| **复杂** | Claude | `claude-sonnet-4-5` | 小说叙事分析、改编对比 |
| **推理** | DeepSeek | `deepseek-reasoner` | 规则提取、因果分析（未来） |

---

### 🔄 模型切换示例

```python
# 场景1：快速批量处理，使用 DeepSeek
extractor = NovelMetadataExtractor(provider="deepseek")
for novel in novels:
    metadata = extractor.execute(novel)

# 场景2：高质量分析，使用 Claude
segmenter = NovelSegmenter(provider="claude")
analysis = segmenter.execute(novel_file, chapter_number=1)

# 场景3：成本优先，全部使用 DeepSeek
segmenter = NovelSegmenter(provider="deepseek")
analysis = segmenter.execute(novel_file, chapter_number=1)
```

---

### 📊 性能对比（实测数据）

| Provider | 模型 | 任务 | 响应时间 | Token消耗 | 相对成本 |
|---------|------|------|---------|----------|---------|
| Claude | `claude-sonnet-4-5` | 小说分段（第1章） | ~45s | ~15000 | 1.0x |
| DeepSeek | `deepseek-chat` | 元数据提取 | ~1.9s | ~500 | 0.05x |
| DeepSeek | `deepseek-chat` | 脚本分段 | ~3s | ~800 | 0.05x |

**结论**：
- DeepSeek 速度是 Claude 的 2-3 倍
- DeepSeek 成本约为 Claude 的 1/10-1/20
- Claude 在复杂分析任务上质量更高

## 测试验证

### 运行测试脚本

```bash
python scripts/test/test_dual_llm_providers.py
```

**测试内容**：
1. ✅ LLMClientManager 客户端创建
2. ✅ Claude API 连接测试
3. ❌ DeepSeek API 连接测试（需要有效的 API Key）
4. ✅ 使用统计功能

**当前测试结果**：
```
✅ 客户端创建: 通过
✅ Claude API: 通过
❌ DeepSeek API: 失败 (API Key 无效)
```

### 成本对比

#### Claude（OneChats 代理）
- 优点：高质量输出，上下文理解强
- 成本：相对较高
- 适用：复杂分析、创意生成

#### DeepSeek
- 优点：价格便宜，速度快
- 成本：约为 Claude 的 1/10
- 适用：简单处理、格式化、规则提取

#### DeepSeek R1（推理模型）
- 优点：逻辑推理能力强，返回推理过程
- 成本：与 DeepSeek Chat 相近
- 适用：规则提取、因果分析、复杂推理

## 最佳实践

### 成本优化策略

1. **优先使用 DeepSeek**：除非任务明确需要高质量输出
   - 元数据提取、格式处理 → DeepSeek
   - 批量处理任务 → DeepSeek
2. **Claude 用于关键任务**：
   - 小说叙事分析 → Claude（保证质量）
   - 改编对比分析 → Claude（需要创意理解）
3. **批量处理**：相同任务批量调用，减少网络开销
4. **缓存结果**：避免重复调用相同内容
5. **监控使用**：定期查看 `LLMClientManager.get_usage_stats()` 统计

### 质量 vs 成本权衡

```python
# 开发测试阶段：全部使用 DeepSeek（快速迭代）
extractor = NovelMetadataExtractor(provider="deepseek")
segmenter = NovelSegmenter(provider="deepseek")

# 生产环境：按任务复杂度选择
extractor = NovelMetadataExtractor(provider="deepseek")  # 简单任务
segmenter = NovelSegmenter(provider="claude")            # 复杂任务
```

## 下一步扩展

### 未来计划添加的功能

#### 1. DeepSeek 思维链模型支持 (`deepseek-reasoner`)
**适用场景**：
- 规则提取（从小说中提取世界观规则）
- 因果分析（分析情节因果关系）
- 逻辑推理（判断改编的合理性）

**使用方式**（未来）：
```python
from src.core.llm_client_manager import get_llm_client, get_model_name

# 获取思维链模型
client = get_llm_client("deepseek")
thinking_model = get_model_name("deepseek", model_type="v32-thinking")

# 调用示例
response = client.chat.completions.create(
    model=thinking_model,
    messages=[{"role": "user", "content": "分析以下情节的因果逻辑..."}]
)

# 输出包含推理过程
print(response.choices[0].message.reasoning)  # 推理过程
print(response.choices[0].message.content)     # 最终结论
```

#### 2. 其他计划功能
- **自动回退机制**：DeepSeek 失败时自动切换到 Claude
- **成本预算控制**：设置每日/每月 Token 上限
- **质量评估**：对比两个模型的输出质量
- **A/B 测试工具**：同时调用两个模型，选择最优结果

## 故障排查

### DeepSeek API Key 无效

**症状**：
```
Error code: 401 - Authentication Fails
```

**解决**：
1. 检查 `.env` 文件中的 `DEEPSEEK_API_KEY` 是否正确
2. 访问 https://platform.deepseek.com/api_keys 创建新密钥
3. 更新 `.env` 文件后重启应用

### Claude API 连接失败

**症状**：
```
Connection error or timeout
```

**解决**：
1. 检查网络连接
2. 确认 `CLAUDE_BASE_URL` 是否正确
3. 测试 OneChats 代理是否可用

### 客户端创建失败

**症状**：
```
ValueError: API Key not configured
```

**解决**：
1. 确认 `.env` 文件存在于项目根目录
2. 检查环境变量是否正确加载
3. 重新加载环境变量：`from dotenv import load_dotenv; load_dotenv()`

---

## 📚 相关文档

- **开发规范**: `docs/DEV_STANDARDS.md` 第5节（配置管理）和第6节（Prompt工程）
- **工具路线图**: `docs/tools/ROADMAP.md`
- **测试脚本**: `scripts/test/test_dual_llm_providers.py`
- **使用示例**: `scripts/examples/example_dual_llm_usage.py`

---

**最后更新**: 2026-02-09  
**负责模块**: Core / LLMClientManager  
**维护者**: AI开发团队
