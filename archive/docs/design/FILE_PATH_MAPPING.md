# 文件路径映射说明

## 📁 目录结构

```
data/projects/{project_id}/
├── raw/                    # 原始文件（用户上传）
│   ├── novel/             # 小说原文（.txt, .md, .pdf）
│   │   └── 序列公路求生：我在末日升级物资.txt
│   └── srt/               # 字幕文件（.srt）
│       ├── ep01.srt
│       ├── ep02.srt
│       └── ...
├── processed/             # 处理后的结构化数据
│   ├── novel/
│   │   ├── metadata.json
│   │   └── chapters.json
│   └── script/
│       ├── episodes_index.json
│       └── episodes/
│           ├── ep01.json
│           └── ...
├── analysis/              # 分析结果
│   ├── novel/
│   ├── script/
│   └── alignment/
└── reports/               # 报告输出
```

---

## 🔄 文件流转流程

### 1️⃣ 上传阶段

**前端 → 后端**

```
用户上传文件
  ↓
POST /api/v2/projects/{project_id}/upload
  ↓
根据文件类型分类保存：
  • .txt, .md, .pdf → raw/novel/
  • .srt           → raw/srt/
```

**相关代码：**
- **前端**：`ProjectDetailPage.tsx` - Upload Dialog
- **后端**：`src/api/routes/projects_v2.py:upload_files()`
- **后端**：`src/core/project_manager_v2.py:add_file()`

---

### 2️⃣ 预处理阶段

**后端自动处理**

```
监听文件上传事件
  ↓
PreprocessService.preprocess_project()
  ↓
扫描目录：
  • raw/novel/ → .txt 文件 → novel_segmenter → processed/novel/
  • raw/srt/   → .srt 文件 → script_segmenter → processed/script/
```

**相关代码：**
- **预处理入口**：`src/workflows/preprocess_service.py:preprocess_project()`
- **小说分段**：`src/tools/novel_segmenter.py`
- **脚本分段**：`src/tools/script_segmenter.py`

**输出文件：**
- `processed/novel/chapters.json` - 章节列表
- `processed/novel/metadata.json` - 小说元数据
- `processed/script/episodes_index.json` - 集数索引
- `processed/script/episodes/{episode}.json` - 单集详情

---

### 3️⃣ 查看阶段

**前端读取 processed 数据**

#### Novel Viewer

```
GET /api/v2/projects/{project_id}/chapters
  ↓ 读取 processed/novel/chapters.json
  ↓ 返回章节列表
  
GET /api/v2/projects/{project_id}/chapters/{chapter_number}
  ↓ 从 chapters.json 中提取指定章节内容
  ↓ 返回 markdown 格式
```

**前端组件**：`NovelViewerPage.tsx`

#### Script Viewer

```
GET /api/v2/projects/{project_id}/episodes
  ↓ 读取 processed/script/episodes_index.json
  ↓ 返回集数列表
  
GET /api/v2/projects/{project_id}/episodes/{episode_name}
  ↓ 读取 processed/script/episodes/{episode_name}.json
  ↓ 返回分段详情
```

**前端组件**：`ScriptViewerPage.tsx`

---

### 4️⃣ Raw 文件管理

**查看原始文件**

```
前端点击 "眼睛" 图标
  ↓
GET /api/v2/projects/{project_id}/files/{filename}/view?category={novel|srt}
  ↓
根据 category 读取：
  • category=novel → raw/novel/{filename}
  • category=srt   → raw/srt/{filename}
  • 无 category   → raw/{filename}（兼容旧数据）
  ↓
返回文件原始内容
```

**删除原始文件**

```
前端点击 "垃圾桶" 图标
  ↓
DELETE /api/v2/projects/{project_id}/files/{filename}?category={novel|srt}
  ↓
根据 category 删除对应路径文件
  ↓
触发 update_sources_from_filesystem() 更新项目元数据
```

**前端组件**：`ProjectDetailPage.tsx` - Raw Files Card

---

## 🔍 API 端点路径映射

| API 端点 | 读取路径 | 用途 |
|---------|---------|------|
| `GET /api/v2/projects/{id}/files` | `raw/novel/` + `raw/srt/` | 列出原始文件（带 category） |
| `GET /api/v2/projects/{id}/files/{name}/view?category=novel` | `raw/novel/{name}` | 查看小说原文 |
| `GET /api/v2/projects/{id}/files/{name}/view?category=srt` | `raw/srt/{name}` | 查看字幕文件 |
| `GET /api/v2/projects/{id}/chapters` | `processed/novel/chapters.json` | 获取章节列表 |
| `GET /api/v2/projects/{id}/chapters/{num}` | `processed/novel/chapters.json` | 获取章节内容 |
| `GET /api/v2/projects/{id}/episodes` | `processed/script/episodes_index.json` | 获取集数列表 |
| `GET /api/v2/projects/{id}/episodes/{name}` | `processed/script/episodes/{name}.json` | 获取集数详情 |

---

## 🛡️ 兼容性

### 旧项目（文件直接在 raw/ 根目录）

**后端自动兼容：**
1. **列表**：`get_raw_files()` 同时扫描 `raw/novel/`, `raw/srt/`, `raw/`（根目录）
2. **查看**：无 `category` 参数时，从 `raw/{filename}` 读取
3. **预处理**：扫描顺序为 `[raw/novel, raw]` 和 `[raw/srt, raw]`，避免重复处理

**前端自动兼容：**
1. 旧文件在列表中按 `type === 'script' ? 'srt' : 'novel'` 分类显示
2. 查看/删除时，无 `category` 字段则不传参数，后端使用根路径

---

## 📝 开发注意事项

### 新增文件相关功能时

1. **上传**：必须根据类型保存到 `raw/novel/` 或 `raw/srt/`
2. **列表**：通过 `project_manager_v2.get_raw_files()` 获取（已包含 category）
3. **查看/删除**：传入 `category` 参数以定位正确路径
4. **预处理**：通过 `PreprocessService` 自动处理，无需手动指定路径

### 测试建议

```bash
# 1. 创建新项目（自动创建 raw/novel, raw/srt）
POST /api/v2/projects

# 2. 上传文件（自动分类保存）
POST /api/v2/projects/{id}/upload

# 3. 验证文件列表带 category
GET /api/v2/projects/{id}/files

# 4. 验证预处理正确读取
POST /api/v2/projects/{id}/preprocess

# 5. 验证前端查看器正常工作
访问 /projects/{id}/novel
访问 /projects/{id}/script
```

---

## 🔧 故障排查

### 问题：前端显示文件但无法查看

**检查：**
1. 文件是否在正确的子目录（`raw/novel/` 或 `raw/srt/`）
2. `category` 参数是否正确传递
3. 后端日志中的文件路径

```bash
# 检查目录结构
ls -la data/projects/{project_id}/raw/novel/
ls -la data/projects/{project_id}/raw/srt/

# 检查 API 返回的 category
curl http://localhost:8000/api/v2/projects/{project_id}/files
```

### 问题：预处理找不到文件

**检查：**
1. 文件扩展名是否正确（.txt, .srt）
2. 文件是否在 `raw/novel/` 或 `raw/srt/` 子目录
3. `preprocess_service.py` 的扫描路径配置

```python
# 扫描路径配置
novel_dirs = [raw/novel, raw]  # 先扫描新目录，再扫描根目录（兼容）
srt_dirs = [raw/srt, raw]
```

---

**更新日期：** 2026-02-11  
**版本：** v2.0（引入 raw/novel 与 raw/srt 分类）
