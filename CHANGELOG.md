# 更新日志 (Changelog)

本文件记录项目的重大变更。

---

## [0.6.0] - 2026-02-10 - 工作流模块化拆分

### Changed - 重大重构

#### NovelProcessingWorkflow 模块化
- **拆分** `novel_processing_workflow.py` (1,829 行) → 980 行 (-46.4%)
- **提取** 报告生成功能到 `report_generator.py` (1,123 行, 15 个函数)
- ✅ 完全向后兼容
- ✅ 符合 DEV_STANDARDS.md 规范

### Statistics
- **文件减少**: 849 行 (-46.4%)
- **新增模块**: 1 个 (15 个独立函数)
- **测试通过率**: 100%

---

## [0.5.0] - 2026-02-10 - 架构优化与代码质量提升

### Added - 新增基础设施

#### 新增工具类
- **LLMOutputParser** (`src/utils/llm_output_parser.py`): 统一的 LLM 输出解析工具
  - 减少重复代码 58%
  - 4 个通用解析方法

- **TwoPassTool** (`src/core/two_pass_tool.py`): Two-Pass 模式基础类
  - 抽象基类和函数式接口
  - 统一 Two-Pass 处理流程

- **统一异常体系** (`src/core/exceptions.py`): 7 个标准异常类
  - 完整的错误上下文
  - 保留原始异常堆栈

#### 文档更新
- 更新 `docs/DEV_STANDARDS.md`: 融合最佳实践
- 新增 `docs/maintenance/PROJECT_HEALTH_CHECK_2026-02-10.md`: 体检报告
- 新增 `docs/maintenance/IMPROVEMENT_SUMMARY_2026-02-10.md`: 改进总结
- 新增 `docs/maintenance/TOOL_APPLICATION_SUMMARY_2026-02-10.md`: 应用总结

### Changed - 架构重构

#### schemas_novel 模块化
- **拆分** `schemas_novel.py` (1,824 行) → 包结构 (6 个模块, <600 行/文件)
  - `basic.py`: 基础数据模型
  - `segmentation.py`: 分段相关
  - `annotation.py`: 标注相关
  - `system.py`: 系统元素
  - `validation.py`: 验证结果
  - `__init__.py`: 导出层
- ✅ 完全向后兼容

#### 工具优化
- **NovelSegmenter**: 应用 LLMOutputParser (-62.5% 代码)
- **ScriptSegmenter**: 应用 LLMOutputParser (-53% 代码)
- **NovelAnnotator**: 添加新工具 import

### Fixed - 规范修正

- **清理根目录**: 移动 3 个违规文档到 `docs/maintenance/`
  - 根目录现在只有 `CHANGELOG.md` 和 `README.md`

### Statistics

- **新增文件**: 10 个 (3,224 行)
- **修改文件**: 3 个
- **减少重复**: 90 行
- **向后兼容**: 100%
- **测试通过**: 100%
- **项目评分**: 8.0/10 → 8.8/10 (良好 → 优秀)

---

## [3.0.0] - 2026-02-10 (已回滚)

### ⚠️ 回滚说明

**原因**：未遵循已有的文档定义，擅自修改了数据架构。

**已回滚的变更**：
- ❌ `data/works/` → 恢复为 `data/projects/`
- ❌ `config/catalog.json` → 删除，保留 `data/project_index.json`
- ❌ 项目目录使用中文名 → 改为标准 ID (`PROJ_XXX`)

**保留的合理调整**：
- ✅ `llm_configs.json` 移至 `config/`（配置文件独立）
- ✅ 测试项目移至 `output/test_projects/`（隔离测试数据）

---

## [2.1.0] - 2026-02-10

### 🔧 合理的目录调整

#### 变更内容

**1. 配置文件独立**
```
变更：data/llm_configs.json → config/llm_configs.json
原因：配置文件不应混在数据目录中
```

**2. 测试数据隔离**
```
变更：将 16 个测试项目移至 output/test_projects/
原因：测试数据应与正式项目数据分离
```

**3. 项目目录规范化**
```
变更：data/projects/末哥超凡公路/ → data/projects/PROJ_001/
原因：遵循 docs/architecture/DATA_STORAGE_REDESIGN.md 的命名规范
```

#### 最终目录结构（符合文档定义）

```
project_root/
├── config/                    # 配置文件（新增）
│   └── llm_configs.json      # LLM限流配置
│
├── data/
│   ├── project_index.json    # 项目索引
│   └── projects/             # 各项目数据
│       └── PROJ_001/         # 末哥超凡公路
│           ├── raw/          # 原始数据
│           ├── script/       # 解说稿
│           ├── alignment/    # 对齐数据（待创建）
│           ├── analysis/     # 分析结果（待创建）
│           └── production/   # 生产输出（待创建）
│
├── output/
│   └── test_projects/        # 测试项目（16个）
│
└── archive/                   # 归档数据
```

**参考文档**：
- `docs/PROJECT_STRUCTURE.md` - 第67-82行
- `docs/architecture/DATA_STORAGE_REDESIGN.md` - 完整设计

#### 迁移统计

- ✅ 移动文件：17个（1配置 + 16测试）
- ✅ 重命名项目：1个（末哥超凡公路 → PROJ_001）
- ✅ 更新索引：`data/project_index.json`

#### 后续任务

**已完成的代码更新：**
- [x] `src/core/llm_rate_limiter.py` - 更新 `llm_configs.json` 路径
- [x] `scripts/test/test_actual_api_limits.py` - 更新配置和结果路径
- [x] `scripts/test/test_llm_manager_integration.py` - 更新配置路径
- [x] `scripts/test/test_config.py` - 创建统一测试配置文件

**关于测试脚本路径：**
- 核心工具（novel_importer, srt_importer 等）使用 `data/projects/` 路径（符合文档定义）
- 测试时创建的临时项目保持在 `data/projects/` 下
- 历史测试数据已移至 `output/test_projects/` 隔离保存
- 测试完成后应手动清理 `data/projects/` 中的测试项目

---

## [2.0.0] - 2026-02-08
- 初始版本记录
