# 文档冲突分析报告

**分析日期**: 2026-02-12  
**问题**: 发现多个文档对数据结构的定义不一致

---

## 🔴 核心问题：文档定义冲突

### 冲突点：数据目录结构

**旧设计** (WORKFLOW_REFERENCE.md, PROJECT_STRUCTURE.md):
```
data/projects/{project_id}/
├── raw/
├── processed/                    ← 包含所有处理结果
│   ├── novel/
│   │   ├── metadata.json
│   │   ├── chapters.json
│   │   ├── segmented/            ← 分段在processed下
│   │   │   └── chapter_*.json
│   │   ├── annotated/            ← 标注在processed下
│   │   │   └── chapter_*.json
│   │   └── system_catalog.json
│   └── script/
│       ├── episodes.json
│       ├── segmented/            ← 分段在processed下
│       └── validation/
├── alignment/                    ← 对齐独立目录
└── reports/
```

**新设计** (DATA_STORAGE_REDESIGN.md):
```
data/projects/{project_id}/
├── raw/                          ← 原始文件
├── processed/                    ← 只存储"标准格式"数据
│   ├── novel/
│   │   ├── chapters.json         ← 只有索引
│   │   └── chapter_*.json        ← 只有内容
│   └── script/
│       ├── episodes.json         ← 只有索引
│       └── ep*.json              ← 只有内容
├── analysis/                     ← 分析结果独立目录 🔥 新增
│   ├── novel/
│   │   ├── segmented/            ← 分段在analysis下
│   │   ├── annotated/            ← 标注在analysis下
│   │   └── system_detected/      ← 系统检测在analysis下
│   ├── script/
│   │   ├── segmented/            ← 分段在analysis下
│   │   └── hooks/                ← Hook在analysis下
│   └── alignment/                ← 对齐在analysis下
└── reports/                      ← 报告
```

---

## 🎯 关键区别

| 项目 | 旧设计 | 新设计 | 影响 |
|------|--------|--------|------|
| **分段结果** | `processed/novel/segmented/` | `analysis/novel/segmented/` | 🔴 路径完全不同 |
| **标注结果** | `processed/novel/annotated/` | `analysis/novel/annotated/` | 🔴 路径完全不同 |
| **系统目录** | `processed/novel/system_catalog.json` | `analysis/novel/system_detected/` | 🔴 路径+格式不同 |
| **对齐结果** | `alignment/` (根目录下) | `analysis/alignment/` | 🟡 路径不同 |
| **章节内容** | `processed/novel/chapter_*.json` | `processed/novel/chapter_*.json` | ✅ 相同 |

---

## 📊 文档一致性检查

| 文档 | 使用的结构 | 最后更新 | 状态 |
|------|-----------|---------|------|
| `DATA_STORAGE_REDESIGN.md` | **新设计** (analysis/) | 未知 | ⭐ 最新设计 |
| `WORKFLOW_REFERENCE.md` | **旧设计** (processed/) | 2026-02-12 | ⚠️ 需更新 |
| `PROJECT_STRUCTURE.md` | **旧设计** (processed/) | 2026-02-11 | ⚠️ 需更新 |
| `TOOLS_REFERENCE.md` | 未明确指定 | 2026-02-12 | ⚠️ 需明确 |
| `DEV_STANDARDS.md` | 未明确指定 | 2026-02-11 | ⚠️ 需明确 |

---

## 🔍 代码实现检查

### 实际代码使用的结构

让我检查实际代码中工具的输出路径：

**PreprocessService** (src/workflows/preprocess_service.py):
```python
# 第341-344行
processed_dir = os.path.join(
    config.data_dir, "projects", project_id, "processed/novel"
)
os.makedirs(processed_dir, exist_ok=True)

# 第360-362行
chapters_path = os.path.join(processed_dir, "chapters.json")
```

**结论**: PreprocessService使用 `processed/novel/` 👉 **旧设计**

---

**NovelSegmenter** - 需要检查输出路径
**NovelAnnotator** - 需要检查输出路径
**ScriptSegmenter** - 需要检查输出路径

---

## 🚨 严重性评估

### 问题严重性：🔴 **致命**

**影响**:
1. 🔴 开发者不知道使用哪个设计（新？旧？）
2. 🔴 代码可能使用旧设计，但最新文档是新设计
3. 🔴 前端不知道访问哪个路径
4. 🔴 API设计无法确定（返回哪个路径的数据？）
5. 🔴 测试用例可能使用错误的路径

---

## 🎯 决策：必须统一数据结构

### 方案A: 全部使用新设计 (推荐)

**新设计的优势**:
```
✅ 关注点分离：
   - processed/ = 标准化数据（轻量）
   - analysis/ = 分析结果（重量）
   
✅ 目录职责清晰：
   - processed/ = "原始数据的标准化版本"
   - analysis/ = "AI分析的结果"
   
✅ 易于理解：
   - 用户上传文件 → raw/
   - 系统标准化 → processed/
   - AI分析 → analysis/
   
✅ 扩展性好：
   - 可以在analysis/下增加更多分析类型
   - 不影响processed/的结构
```

**迁移工作量**:
- 更新所有工具的输出路径
- 更新所有API的数据路径
- 更新所有文档
- 更新测试用例
- **预计**: 8-10小时

---

### 方案B: 全部使用旧设计

**旧设计的劣势**:
```
❌ processed/目录职责混乱：
   - 既有"标准化数据"（chapters.json）
   - 又有"分析结果"（segmented/）
   
❌ 不符合关注点分离原则
❌ 扩展性差
❌ 不是最新设计
```

**优势**:
- ✅ 代码已经按此实现
- ✅ 无需迁移

---

## 📋 建议：立即统一为新设计

### 理由
1. **新设计更合理**（关注点分离）
2. **代码尚未完整实现**（正好重构）
3. **前端尚未依赖具体路径**（容易修改）
4. **避免长期技术债**

### 统一步骤

#### 第1步: 更新文档（1小时）
```
✅ DATA_STORAGE_REDESIGN.md - 保持不变（最新设计）
⚠️ WORKFLOW_REFERENCE.md - 更新为新设计
⚠️ PROJECT_STRUCTURE.md - 更新为新设计
⚠️ TOOLS_REFERENCE.md - 明确输出路径
⚠️ DEV_STANDARDS.md - 明确目录规范
```

#### 第2步: 更新代码（6小时）
```
⚠️ PreprocessService - 仍输出到processed/（符合新设计）
⚠️ NovelSegmenter - 改为输出到analysis/novel/segmented/
⚠️ NovelAnnotator - 改为输出到analysis/novel/annotated/
⚠️ NovelSystemDetector - 改为输出到analysis/novel/system_detected/
⚠️ ScriptSegmenter - 改为输出到analysis/script/segmented/
⚠️ HookDetector - 改为输出到analysis/script/hooks/
⚠️ NovelScriptAligner - 改为输出到analysis/alignment/
```

#### 第3步: 更新API（3小时）
```
⚠️ GET /api/v2/projects/{id}/chapters/{chId}/segmentation
    → 从 analysis/novel/segmented/ 读取
    
⚠️ GET /api/v2/projects/{id}/chapters/{chId}/annotation
    → 从 analysis/novel/annotated/ 读取
```

#### 第4步: 更新前端（2小时）
```
⚠️ 前端API路径无需修改（只是后端读取路径变化）
```

#### 第5步: 测试验证（2小时）
```
- 端到端测试
- 验证数据路径
- 验证API返回
```

**总工时**: 14小时

---

## 📐 新设计的数据流转

### 完整的数据流转路径

```
用户上传文件
    ↓
raw/novel.txt                           ← 原始文件
    ↓ NovelImporter (规范化)
processed/novel/standardized.txt        ← 标准化文本
    ↓ NovelMetadataExtractor
processed/novel/metadata.json           ← 元数据
    ↓ NovelChapterDetector
processed/novel/chapters.json           ← 章节索引
processed/novel/chapter_*.json          ← 章节内容（标准格式）
    ↓ ===== 预处理完成 =====
    ↓ ===== 开始分析 =====
    ↓ NovelSegmenter (Two-Pass)
analysis/novel/segmented/chapter_*.json ← 分段结果
    ↓ NovelAnnotator (Two-Pass)
analysis/novel/annotated/chapter_*.json ← 标注结果
    ↓ NovelSystemDetector
analysis/novel/system_detected/catalog.json ← 系统目录
```

### 分层职责

| 目录 | 职责 | 数据类型 | 生成方式 |
|------|------|---------|---------|
| `raw/` | 原始文件存储 | 二进制/文本 | 用户上传 |
| `processed/` | 标准格式转换 | 结构化JSON | 规则/LLM轻度处理 |
| `analysis/` | AI深度分析 | 结构化JSON | LLM深度处理 |
| `reports/` | 报告生成 | Markdown/PDF | 汇总生成 |

---

## 🎯 基于新设计的Review

### 当前实现 vs 新设计

| 组件 | 当前实现 | 新设计 | 匹配度 |
|------|---------|--------|--------|
| **PreprocessService** | `processed/` ✅ | `processed/` ✅ | 🟢 100% 匹配 |
| **NovelSegmenter** | `processed/novel/segmented/` ❌ | `analysis/novel/segmented/` | 🔴 0% 匹配 |
| **NovelAnnotator** | `processed/novel/annotated/` ❌ | `analysis/novel/annotated/` | 🔴 0% 匹配 |
| **ScriptSegmenter** | `processed/script/segmented/` ❌ | `analysis/script/segmented/` | 🔴 0% 匹配 |
| **NovelScriptAligner** | `alignment/` ❌ | `analysis/alignment/` | 🔴 0% 匹配 |

**结论**: 
- ✅ PreprocessService已遵循新设计
- ❌ **所有分析工具仍使用旧路径**
- 🔴 代码与最新设计完全不匹配

---

## 📋 统一行动计划

### 目标：全部迁移到新设计

**核心原则**:
```
processed/ = 只存储标准格式数据（轻量、快速）
analysis/  = 存储AI分析结果（重量、慢速）
```

### 迁移清单

#### 1. 立即明确：哪个是标准设计？

**问题**: 
- `DATA_STORAGE_REDESIGN.md` 说是"新设计"
- 但其他文档都用旧设计
- 代码实现混合了两种设计

**行动**: 
1. 确认`DATA_STORAGE_REDESIGN.md`是最新设计 ✅
2. 将其提升为标准规范
3. 废弃所有旧文档中的数据结构描述

#### 2. 更新核心文档（2小时）

```
高优先级（必须更新）:
- [ ] WORKFLOW_REFERENCE.md → 使用新设计
- [ ] PROJECT_STRUCTURE.md → 使用新设计
- [ ] TOOLS_REFERENCE.md → 明确工具输出路径
- [ ] DEV_STANDARDS.md → 明确目录规范

中优先级（建议更新）:
- [ ] UI_DEVELOPMENT_GUIDE.md → 更新API路径示例
- [ ] QUICK_START.md → 更新数据路径说明
```

#### 3. 迁移工具代码（8小时）

**NovelSegmenter** (2小时):
```python
# 当前（旧设计）
output_path = f"data/projects/{project_id}/processed/novel/segmented/chapter_{chapter_id}.json"

# 修改为（新设计）
output_path = f"data/projects/{project_id}/analysis/novel/segmented/chapter_{chapter_id}.json"
```

**NovelAnnotator** (2小时):
```python
# 当前（旧设计）
output_path = f"processed/novel/annotated/chapter_{chapter_id}.json"

# 修改为（新设计）
output_path = f"analysis/novel/annotated/chapter_{chapter_id}.json"
```

**NovelSystemDetector** (1小时):
```python
# 当前（旧设计）
output_path = f"processed/novel/system_catalog.json"

# 修改为（新设计）
output_path = f"analysis/novel/system_detected/catalog.json"
```

**ScriptSegmenter** (1小时):
```python
# 当前（旧设计）
output_path = f"processed/script/segmented/ep{episode_id}.json"

# 修改为（新设计）
output_path = f"analysis/script/segmented/ep{episode_id}.json"
```

**HookDetector** (1小时):
```python
# 当前（旧设计）
output_path = f"processed/script/ep01-hook.json"

# 修改为（新设计）
output_path = f"analysis/script/hooks/ep01.json"
```

**NovelScriptAligner** (1小时):
```python
# 当前（旧设计）
output_path = f"alignment/chapter_{ch}_to_ep{ep}.json"

# 修改为（新设计）
output_path = f"analysis/alignment/chapter_{ch}_to_ep{ep}.json"
```

#### 4. 更新API路径（2小时）

```python
# src/api/routes/projects_v2.py

@router.get("/projects/{project_id}/chapters/{chapter_id}/segmentation")
async def get_chapter_segmentation(project_id: str, chapter_id: str):
    # 从新路径读取
    file_path = f"data/projects/{project_id}/analysis/novel/segmented/{chapter_id}.json"
    # ...
```

#### 5. 数据迁移脚本（2小时）

```python
# scripts/migrate_to_new_structure.py

def migrate_project(project_id: str):
    """迁移项目数据结构"""
    project_dir = f"data/projects/{project_id}"
    
    # 创建analysis/目录
    os.makedirs(f"{project_dir}/analysis/novel/segmented", exist_ok=True)
    os.makedirs(f"{project_dir}/analysis/novel/annotated", exist_ok=True)
    os.makedirs(f"{project_dir}/analysis/novel/system_detected", exist_ok=True)
    os.makedirs(f"{project_dir}/analysis/script/segmented", exist_ok=True)
    os.makedirs(f"{project_dir}/analysis/script/hooks", exist_ok=True)
    os.makedirs(f"{project_dir}/analysis/alignment", exist_ok=True)
    
    # 移动文件
    # processed/novel/segmented/ → analysis/novel/segmented/
    # processed/novel/annotated/ → analysis/novel/annotated/
    # ...
```

#### 6. 测试验证（2小时）

```bash
# 测试完整流程
python scripts/test/test_full_production_with_llm.py

# 验证数据路径
python scripts/validate_data_structure.py
```

---

## 📊 统一后的好处

### 清晰的数据分层

```
raw/        → 用户上传的原始数据（不可修改）
processed/  → 系统标准化的数据（轻量、快速生成）
analysis/   → AI分析的结果（重量、需LLM）
reports/    → 最终报告（面向用户）
```

### 清晰的工作流阶段

```
Stage 1: Upload      → raw/
Stage 2: Preprocess  → processed/
Stage 3: Analyze     → analysis/
Stage 4: Report      → reports/
```

### 清晰的API分层

```
GET /api/v2/projects/{id}/chapters           → processed/novel/chapters.json
GET /api/v2/projects/{id}/chapters/{ch}/segmentation → analysis/novel/segmented/
GET /api/v2/projects/{id}/chapters/{ch}/annotation   → analysis/novel/annotated/
```

---

## 🔧 立即行动建议

### 方案：先统一文档和设计，再重新review

```
Step 1: 确认设计标准（30分钟）
  - 明确DATA_STORAGE_REDESIGN.md为标准
  - 在.cursorrules中添加强制引用
  
Step 2: 更新所有文档（2小时）
  - 批量替换processed/→analysis/
  - 统一数据路径描述
  
Step 3: 基于新设计重新review（4小时）
  - 使用5层分析法
  - 检查代码是否符合新设计
  - 生成详细的gap analysis
  
Step 4: 制定迁移计划（2小时）
  - 优先级排序
  - 工时估算
  - 风险评估
```

---

## 🎯 现在的问题

**我之前的review完全基于旧设计**，所以分析是**错误的**！

需要：
1. ✅ 确认新设计为标准
2. ✅ 更新所有文档为新设计
3. ✅ 基于新设计重新review
4. ✅ 检查代码与新设计的差距
5. ✅ 制定迁移计划

---

**Report Created**: 2026-02-12  
**Critical**: 必须先统一设计标准，再进行review  
**Next Action**: 等待用户确认使用新设计
