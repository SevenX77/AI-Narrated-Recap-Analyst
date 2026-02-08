# Archive Index - 末哥超凡公路 Novel 处理结果

## 归档原因

重新设计novel处理流程：
1. 拆分chpt_0000.md简介为独立文件
2. 分段分析结果放置在novel文件夹下（chpt_XXXX.md）
3. 功能分析结果放置在functional_analysis下（chpt_XXXX_functional_analysis.json）
4. 使用 DeepSeek R1 模型（推理能力更强）
5. 实现版本管理规则（_latest.json指针 + 时间戳版本）

## 归档内容

### v2_old_functional_analysis_20260207/

**归档时间**: 2026-02-07  
**原路径**: `novel/functional_analysis/`  
**内容**: 使用 DeepSeek V3 + 复杂Prompt 生成的分析结果  

**问题**:
- DeepSeek V3 过度聚合（段落1达480字）
- 未正确识别时间转折（"几个月前"）
- 准确率不稳定（33%）

**包含文件**:
- 第1-9章完整分段分析.md（V3生成，有过度聚合问题）
- chpt_0001-0009_functional_analysis.json
- batch_analysis_summary_20260207_191727.json
- stability_test/（V3稳定性测试，33%准确率）
- prompt_optimization_test/（Prompt优化测试，100%准确率但prompt过于复杂）
- r1_test/（R1测试，100%准确率，简化prompt）
- MODEL_COMPARISON_REPORT.md（V3 vs R1 对比报告）

### v2_old_segmentation_20260207/

**归档时间**: 2026-02-07  
**原路径**: `novel/segmentation_analysis/`  
**内容**: 旧版分段分析工具（NovelSegmentationTool）的输出  

**问题**:
- 基于硬规则分段（非LLM驱动）
- 粒度太细（自然段级别）
- 不适合人类理解

**包含文件**:
- chpt_0001_analysis_test.json
- processing_report.json

### v2_merged_chapters_20260207/

**归档时间**: 2026-02-07  
**原路径**: `novel/`  
**内容**: 10章合并的章节文件  

**问题**:
- 文件过大（每个1200-1400行）
- 不便于单章处理
- 简介（chpt_0000.md）未拆分

**包含文件**:
- chpt_0001-0010.md
- chpt_0011-0020.md
- chpt_0021-0030.md
- chpt_0031-0040.md
- chpt_0041-0050.md

---

## 新版设计（V3）

### 目录结构
```
novel/
├── chpt_0000_简介.md                    # 🆕 拆分的简介
├── chpt_0001.md                         # 🆕 单章分段结果（人类可读）
├── chpt_0002.md
├── ...
├── functional_analysis/                 # 功能分析结果
│   ├── chpt_0001_functional_analysis_v20260207_203000.json
│   ├── chpt_0001_functional_analysis_latest.json  # 🆕 指针
│   ├── chpt_0002_functional_analysis_v20260207_203100.json
│   ├── chpt_0002_functional_analysis_latest.json
│   └── ...
└── archive/                             # 归档目录
    ├── ARCHIVE_INDEX.md                 # 本文件
    ├── v2_old_functional_analysis_20260207/
    ├── v2_old_segmentation_20260207/
    └── v2_merged_chapters_20260207/
```

### 新流程
1. **拆分简介**: chpt_0000.md → chpt_0000_简介.md
2. **拆分章节**: raw/novel.txt → chpt_0001.md, chpt_0002.md, ...（单章）
3. **功能分析**: 使用 DeepSeek R1 + 简化Prompt → chpt_XXXX_functional_analysis.json
4. **版本管理**: 时间戳版本 + _latest.json 指针

### 使用的模型
- **主模型**: DeepSeek V3（快速，成本低）
- **Fallback模型**: DeepSeek R1（推理强，处理V3失败的情况）
- **Fallback触发条件**:
  - V3 API 错误
  - 段落1字数 < 120（只有广播没有反应）
  - 段落1字数 > 400（过度聚合）

---

**归档者**: Cursor AI  
**归档日期**: 2026-02-07
