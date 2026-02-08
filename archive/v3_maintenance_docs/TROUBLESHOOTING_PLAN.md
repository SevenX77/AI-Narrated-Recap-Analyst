# 问题排查计划

生成时间：2026-02-03  
项目：PROJ_002  
问题：对齐质量不合格（58.5分）

---

## 📊 初步诊断

### 质量报告摘要：
```json
{
  "overall_score": 58.5,           ← 不合格（需要>70）
  "avg_confidence": 0.585,
  "avg_event_match_score": 0.834,  ← Event级匹配还可以
  "avg_validation_score": 0.419,   ← Block验证很低！⚠️
  "total_alignments": 13
}
```

### 🔴 核心问题识别：

1. **Block链验证分数过低（41.9%）**
   - Event级匹配：83.4% ✅
   - Block链验证：41.9% ❌ （问题所在！）

2. **多个Script Event匹配到同一个Novel Event**
   - 对齐#1: Script "车队组建" → Novel "收听广播"
   - 对齐#2: Script "探索系统" → Novel "收听广播" ⚠️
   - 对齐#3: Script "内部冲突" → Novel "收听广播" ⚠️

---

## 🔍 排查流程（沿着Workflow逐步检查）

### Phase 1: 数据准备阶段

#### ✅ Step 1.1: 检查SRT文件处理
- [ ] SRT blocks解析是否正确
- [ ] 句子还原是否准确（有JSON解析错误）
- [ ] Semantic Blocks划分是否合理
- [ ] Events聚合是否正确

**检查点**：
```bash
# 查看ep01的Script Events
cat data/projects/PROJ_002/alignment/ep01_script_events_v2_latest.json | jq '.[] | {title, blocks: (.semantic_blocks | length)}'
```

#### ✅ Step 1.2: 检查Novel章节处理
- [ ] 章节分割是否正确
- [ ] 句子分割是否合理
- [ ] Semantic Blocks划分是否准确
- [ ] Events聚合是否正确

**检查点**：
```bash
# 查看Novel Events
cat data/projects/PROJ_002/alignment/novel_events_v2_latest.json | jq '.[] | {title, chapter_range, blocks: (.semantic_blocks | length)}' | head -30
```

---

### Phase 2: Hook检测阶段

#### ✅ Step 2.1: 检查Hook检测结果
- [ ] Hook是否正确识别
- [ ] 线性叙事起点是否准确
- [ ] Hook summary是否合理

**检查点**：
```bash
# 查看Hook检测结果
cat data/projects/PROJ_002/alignment/ep01_hook_detection_latest.json | jq '.'
```

---

### Phase 3: 两级匹配阶段

#### 🔴 Step 3.1: Event级粗匹配（问题区域）
- [ ] Script Events数量与内容
- [ ] Novel Events数量与内容
- [ ] Event级匹配候选是否合理
- [ ] 是否有多个Script Event匹配同一个Novel Event

**关键问题**：
- 为什么多个Script Event都匹配到"收听广播"这个Novel Event？
- 是否Novel Event粒度太粗，导致匹配不准确？

**检查命令**：
```python
# 查看所有对齐结果中的Novel Event分布
import json
with open('data/projects/PROJ_002/alignment/alignment_v2_latest.json', 'r') as f:
    data = json.load(f)

novel_event_usage = {}
for item in data:
    novel_title = item['novel_event']['title']
    novel_event_usage[novel_title] = novel_event_usage.get(novel_title, 0) + 1

print("Novel Event使用次数：")
for title, count in sorted(novel_event_usage.items(), key=lambda x: -x[1]):
    print(f"  {count}次: {title}")
```

#### 🔴 Step 3.2: Block链验证（主要问题区域）
- [ ] Script Event的Semantic Blocks内容
- [ ] Novel Event的Semantic Blocks内容
- [ ] Block链匹配逻辑是否正确
- [ ] 为什么validation_score这么低？

**关键问题**：
- Block链验证的逻辑是什么？
- 是否Semantic Blocks粒度不匹配？
- 是否Prompt指令不清晰？

---

### Phase 4: 日志分析

#### ✅ Step 4.1: 查看关键日志
- [ ] Event级匹配的详细日志
- [ ] Block链验证的详细日志
- [ ] LLM返回的原始数据

**检查命令**：
```bash
# 查看Event级匹配日志
grep "📌 处理Script Event" logs/app.log -A 20 | head -50

# 查看Block链验证日志
grep "🔍 Level 2: 批量Block链验证" logs/app.log -A 15 | head -50
```

---

## 🎯 优先级排查顺序

### 🔴 高优先级（立即检查）

#### 1. 为什么多个Script Event匹配到同一个Novel Event？
**可能原因**：
- Novel Event粒度太粗，一个Event包含了太多内容
- Event级匹配的Prompt不够精确
- 没有考虑"已匹配"的Novel Event，导致重复匹配

**排查步骤**：
1. 查看Novel Events的内容和粒度
2. 查看Script Events的内容
3. 对比匹配逻辑

#### 2. 为什么Block链验证分数这么低？
**可能原因**：
- Semantic Blocks粒度不匹配（Script太细，Novel太粗）
- Block链验证的Prompt不合理
- LLM理解Block匹配的标准不一致

**排查步骤**：
1. 查看具体的Block内容
2. 查看Block链验证的Prompt
3. 查看LLM返回的验证结果

---

### ⚠️ 中优先级

#### 3. JSON解析错误是否影响了数据质量？
- ep01.srt 句子还原失败，使用了fallback方案
- 是否导致Semantic Blocks不准确？

#### 4. Hook检测是否影响了匹配？
- Hook部分是否正确排除？
- 线性叙事起点是否准确？

---

### ℹ️ 低优先级

#### 5. 性能优化
- 批量处理是否正确工作？
- 并发控制是否合理？

---

## 📝 排查检查清单

### 数据层面：
- [ ] Script Events数量和质量
- [ ] Novel Events数量和质量
- [ ] Semantic Blocks粒度是否合理
- [ ] Events聚合是否正确

### 匹配层面：
- [ ] Event级匹配逻辑
- [ ] Block链验证逻辑
- [ ] 重复匹配问题
- [ ] 阈值设置是否合理

### 日志层面：
- [ ] 关键步骤的日志
- [ ] LLM返回数据
- [ ] 错误和警告信息

---

## 🛠️ 排查工具清单

### 1. 快速查看工具
```bash
# 查看对齐概况
python3 scripts/analyze_alignment.py

# 查看Block详情
python3 scripts/inspect_blocks.py --event-id ep01_evt_001

# 查看匹配过程
grep "处理Script Event" logs/app.log -A 30
```

### 2. 数据对比工具
```python
# 对比Script和Novel的Blocks
python3 scripts/compare_blocks.py --script ep01_evt_001 --novel novel_evt_003
```

---

## 📊 预期输出

完成排查后，应该能够回答：
1. ✅ 为什么Block链验证分数低？
2. ✅ 为什么多个Script Event匹配同一个Novel Event？
3. ✅ 数据质量如何（Semantic Blocks和Events是否合理）？
4. ✅ 需要优化哪些环节？
5. ✅ 具体的优化方案是什么？

---

**下一步行动**：
开始执行排查，从高优先级问题开始，逐步定位根本原因。
