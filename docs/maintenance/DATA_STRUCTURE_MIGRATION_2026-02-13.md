# 数据结构迁移记录 2026-02-13

**状态**: ✅ 完成  
**执行时间**: 2026-02-13  
**类型**: 系统性重构

---

## 📋 迁移概述

### 迁移目标
统一Phase I Analyst Workflow的数据存储结构，采用四步工作流模型：
1. **Import** - 导入与标准化
2. **Script Analysis** - 脚本分析
3. **Novel Analysis** - 小说分析
4. **Alignment** - 对齐分析

### 核心变更

#### 1. 目录结构调整
```
旧结构:
data/projects/{project_id}/
├── raw/
│   ├── novel/
│   └── srt/              ❌ 旧名称
├── processed/            ❌ 废弃
│   ├── novel/
│   └── script/
└── alignment/            ❌ 顶层，废弃

新结构:
data/projects/{project_id}/
├── raw/
│   ├── novel/
│   └── script/           ✅ 从srt改名
└── analyst/              ✅ 新增，所有Phase I数据
    ├── import/
    │   ├── novel/
    │   └── script/
    ├── script_analysis/
    │   └── history/
    ├── novel_analysis/
    │   └── history/
    └── alignment/
        └── history/
```

#### 2. 文件命名规范
```
旧命名:
- processed/novel/segmented/chapter_001.json
- processed/novel/annotated/chapter_001.json
- processed/script/segmented/ep01.json
- alignment/chapter_001_to_ep01.json

新命名:
- analyst/novel_analysis/chapter_001_segmentation_latest.json
- analyst/novel_analysis/chapter_001_annotation_latest.json
- analyst/script_analysis/ep01_segmentation_latest.json
- analyst/alignment/chapter_001_ep01_alignment_latest.json
```

---

## 🔧 修改清单

### 1. 文档更新 (3个文件)

| 文件 | 修改内容 | 状态 |
|------|---------|------|
| `docs/WORKFLOW_REFERENCE.md` | 更新数据存储结构说明 | ✅ |
| `docs/PROJECT_STRUCTURE.md` | 更新目录结构图 | ✅ |
| `docs/workflows/PHASE_I_COMPLETE_GUIDE.md` | 更新路径引用 | ✅ |

### 2. 核心代码 (1个文件)

| 文件 | 修改内容 | 状态 |
|------|---------|------|
| `src/core/project_manager_v2.py` | 路径配置：<br>- `raw/srt/` → `raw/script/`<br>- 创建 `analyst/` 目录结构<br>- 更新 `get_chapters()`, `get_episodes()`, `get_raw_files()` | ✅ |

### 3. Workflow层 (1个文件)

| 文件 | 修改内容 | 状态 |
|------|---------|------|
| `src/workflows/preprocess_service.py` | - `raw_srt_dir` → `raw_script_dir`<br>- 输出到 `analyst/import/` | ✅ |

### 4. Tools层 (0个文件)

✅ 无需修改 - Tools层未直接使用旧路径

### 5. API路由 (3个文件)

| 文件 | 修改内容 | 状态 |
|------|---------|------|
| `src/api/routes/projects_v2.py` | - `get_processed_file` → `get_analyst_file`<br>- `processed/` → `analyst/`<br>- `srt` → `script` category | ✅ |
| `src/api/routes/analyst_results.py` | 已使用新路径 | ✅ |
| `src/api/routes/workflow_state.py` | - `raw_srt_dir` → `raw_script_dir` | ✅ |

### 6. 前端 (0个文件)

✅ 无需修改 - 前端通过API访问，无直接路径引用

---

## 🛠️ 迁移工具

### 数据迁移脚本
创建了 `scripts/migrate_data_structure.py` 用于迁移现有项目数据：

```bash
# 迁移单个项目（预览模式）
python scripts/migrate_data_structure.py --project-id project_001 --dry-run

# 迁移单个项目（执行）
python scripts/migrate_data_structure.py --project-id project_001

# 迁移所有项目
python scripts/migrate_data_structure.py --all
```

**功能**:
- ✅ `raw/srt/` → `raw/script/`
- ✅ `processed/novel/` → `analyst/import/novel/` + `analyst/novel_analysis/`
- ✅ `processed/script/` → `analyst/import/script/` + `analyst/script_analysis/`
- ✅ `alignment/` → `analyst/alignment/`
- ✅ 文件重命名（`*_latest.json` 格式）
- ✅ 历史版本管理（保留到 `history/` 目录）
- ✅ Dry-run 模式

---

## 📊 影响范围

### 后端影响
- ✅ 项目创建：自动创建新目录结构
- ✅ 文件上传：保存到 `raw/script/` 而非 `raw/srt/`
- ✅ 预处理：输出到 `analyst/import/`
- ✅ 数据查询：从 `analyst/` 读取

### 前端影响
- ✅ 无需修改 - API层抽象屏蔽路径变化
- ⚠️ 缓存清理：建议清除浏览器缓存

### 兼容性
- ❌ 不兼容旧数据结构
- ✅ 提供迁移脚本支持
- ⚠️ 建议在测试环境先验证

---

## 🎯 验证步骤

### 1. 文档验证
```bash
# 检查文档一致性
grep -r "processed/" docs/ | grep -v "archive" | grep -v "MIGRATION"
grep -r "raw/srt" docs/ | grep -v "archive" | grep -v "MIGRATION"
```
**预期结果**: 无匹配（除归档和迁移文档）

### 2. 代码验证
```bash
# 检查代码中的旧路径引用
grep -r "processed/" src/ | grep -v ".pyc"
grep -r "raw/srt" src/ | grep -v ".pyc"
```
**预期结果**: 无匹配（除注释）

### 3. 功能测试
- [ ] 创建新项目
- [ ] 上传小说文件（检查保存到 `raw/novel/`）
- [ ] 上传脚本文件（检查保存到 `raw/script/`）
- [ ] 执行预处理（检查输出到 `analyst/import/`）
- [ ] 查看章节列表（从 `analyst/import/novel/chapters.json`）
- [ ] 查看集数列表（从 `analyst/import/script/episodes.json`）

### 4. 迁移验证
```bash
# 在测试项目上运行迁移（dry-run）
python scripts/migrate_data_structure.py --project-id test_project --dry-run

# 检查输出日志，确认迁移计划正确

# 执行实际迁移
python scripts/migrate_data_structure.py --project-id test_project

# 验证迁移结果
ls -la data/projects/test_project/
```

---

## ⚠️ 注意事项

### 1. 数据备份
**强烈建议**在迁移前备份 `data/projects/` 目录：
```bash
cp -r data/projects data/projects.backup.$(date +%Y%m%d)
```

### 2. 迁移时机
- ✅ 建议在系统维护窗口执行
- ⚠️ 迁移期间暂停新文件上传
- ⚠️ 通知用户可能的短暂服务中断

### 3. 回滚方案
如果迁移失败，可以：
1. 停止服务
2. 恢复备份：`mv data/projects.backup.YYYYMMDD data/projects`
3. 回滚代码到迁移前的commit
4. 重启服务

### 4. 已知问题
- ⚠️ 迁移脚本不处理正在进行中的workflow任务
- ⚠️ 需要手动清理旧的 `processed/` 和 `alignment/` 目录（如果非空）

---

## 📈 后续工作

### 短期（1周内）
- [ ] 在生产环境执行迁移
- [ ] 监控错误日志
- [ ] 收集用户反馈

### 中期（1个月内）
- [ ] 更新所有相关文档
- [ ] 添加自动化测试覆盖新路径
- [ ] 优化迁移脚本性能

### 长期
- [ ] 考虑数据库存储替代文件系统
- [ ] 实现数据版本管理
- [ ] 添加数据完整性检查工具

---

## 📚 相关文档

- `docs/WORKFLOW_REFERENCE.md` - 工作流与数据存储参考
- `docs/PROJECT_STRUCTURE.md` - 项目结构说明
- `docs/workflows/PHASE_I_COMPLETE_GUIDE.md` - Phase I 完整指南
- `scripts/migrate_data_structure.py` - 迁移脚本

---

**维护者**: Project Team  
**审核者**: 待定  
**批准者**: 待定

**最后更新**: 2026-02-13
