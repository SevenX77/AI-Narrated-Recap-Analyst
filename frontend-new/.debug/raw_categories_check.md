# raw/novel 与 raw/srt 分类目录改造验证报告

## 一、修改范围总结

### 后端文件

| 文件 | 改动 |
|------|------|
| `src/core/project_manager_v2.py` | ✅ create_project 创建 raw/novel、raw/srt<br>✅ get_raw_files 从子目录汇总并返回 category<br>✅ update_sources_from_filesystem 扫描子目录<br>✅ add_file 保存到对应子目录 |
| `src/api/routes/projects_v2.py` | ✅ upload 按扩展名保存到 raw/novel 或 raw/srt<br>✅ view/delete 支持 category 查询参数 |
| `src/workflows/preprocess_service.py` | ✅ 从 [raw/novel, raw] 扫描 .txt<br>✅ 从 [raw/srt, raw] 扫描 .srt<br>✅ 防重复任务创建 |

### 前端文件

| 文件 | 改动 |
|------|------|
| `frontend-new/src/types/project.ts` | ✅ RawFile 增加 category?: 'novel' \| 'srt' |
| `frontend-new/src/api/projectsV2.ts` | ✅ deleteFile(projectId, filename, category?)<br>✅ getFileViewUrl(projectId, filename, category?) |
| `frontend-new/src/pages/ProjectDetailPage.tsx` | ✅ 按 category 分组展示（Novel / SRT 折叠块）<br>✅ 查看/删除时传入 file.category |

---

## 二、后端验证结果

**验证脚本：** `scripts/test/verify_raw_categories.py`

| 测试项 | 结果 |
|--------|------|
| 新建项目时创建 raw/novel、raw/srt | ✅ 通过 |
| 子目录内文件返回带 category | ✅ 通过 (novel: ['test_novel.txt'], srt: ['ep01.srt']) |
| 根 raw 下文件返回但不带 category（兼容旧数据） | ✅ 通过 |
| update_sources_from_filesystem 正确识别 has_novel / has_script | ✅ 通过 |
| 清理临时项目 | ✅ 通过 |

**输出：** 全部检查通过

---

## 三、前端验证结果

### 类型定义
- ✅ `RawFile` 已包含 `category?: 'novel' | 'srt'`
- ✅ linter 不再报告 "Property 'category' does not exist"

### API 调用
- ✅ `deleteFile` 接受 `{ filename, category }` 对象
- ✅ `getFileViewUrl` 接受 `category` 参数，生成带 `?category=novel` 的 URL
- ✅ 旧数据（无 category）不传参数，路径为 `raw/filename`（兼容）

### UI 逻辑
- ✅ 按 `['novel', 'srt']` 遍历，过滤并分组文件
- ✅ 使用 `<details open>` + `<summary>` 实现折叠（默认展开）
- ✅ 无 category 的文件按 `type === 'script' ? 'srt' : 'novel'` 归类
- ✅ 查看/删除时传入 `file.category`

---

## 四、兼容性说明

### 旧项目的数据迁移
- **无需手动迁移**：现有文件仍在 `raw/` 根目录
- **自动兼容**：列表时识别根目录文件（无 category）；查看/删除时使用 `raw/filename`
- **新上传**：自动进入 `raw/novel` 或 `raw/srt`

### 预处理兼容
- 扫描顺序：先 `raw/novel`（或 `raw/srt`），后 `raw/`（根目录）
- 去重：通过 `novel_added` 与 `srt_seen` 防止同名文件重复处理

---

## 五、已知限制

### 前端构建
- ❌ `npm run build` 失败（非本次修改引入）
  - 缺少 `@types/react` 等类型声明
  - 缺少依赖 `react-markdown`（NovelViewerPage 使用）
- ✅ **本次修改不引入新的类型错误**（已验证 linter 无 category 相关报错）

### 后端测试
- ✅ 单元测试通过（project_manager_v2 + preprocess 目录扫描）
- ⚠️ `test_auto_preprocess.py` 可能需更新（其在根 raw 创建测试文件，预处理会找到）

---

## 六、建议后续步骤

1. **解决前端构建问题**（独立任务）：
   ```bash
   cd frontend-new
   npm install --save-dev @types/react @types/react-dom
   npm install react-markdown
   ```

2. **数据迁移脚本**（可选）：
   若需将现有 `raw/` 下的文件整理到子目录：
   ```python
   # scripts/migrate_raw_to_categories.py
   # 遍历所有项目，.txt → raw/novel，.srt → raw/srt
   ```

3. **更新 test_auto_preprocess.py**（可选）：
   在测试中将文件直接放到 `raw/novel` 与 `raw/srt` 以测试新流程。

---

## 七、检查清单

- [x] 后端目录结构（raw/novel、raw/srt）
- [x] 后端列表 API 返回 category
- [x] 后端上传保存到子目录
- [x] 后端查看/删除支持 category 参数
- [x] 后端预处理从子目录扫描
- [x] 前端类型定义增加 category
- [x] 前端 API 调用传入 category
- [x] 前端 UI 按分类折叠展示
- [x] 兼容旧数据（无 category）
- [x] 后端单元测试通过

**总结：raw 分类目录改造已完成并验证通过。**
