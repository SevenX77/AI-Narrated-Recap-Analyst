# AI模型训练与微调完全指南

**日期**: 2026-02-05  
**目标读者**: 对AI训练不熟悉的开发者  
**范围**: 从零到实战的完整流程

---

## 🎓 第一部分：核心概念科普

### 1. 什么是"模型"？

想象一个**超级聪明的学生**：

| 比喻 | AI模型中的对应概念 |
|------|------------------|
| 学生的大脑 | **模型参数**（数十亿个数字） |
| 教科书 | **训练数据**（大量文本示例） |
| 学习过程 | **训练**（调整参数） |
| 课后辅导 | **微调**（针对性训练） |
| 考试 | **推理/生成**（实际使用） |

---

### 2. 预训练 vs 微调：有什么区别？

#### 🏫 预训练（Pre-training）

**类比**：让学生读遍整个图书馆

```
输入：海量通用文本（维基百科、书籍、网页...）
目标：学会语言的基本规律
耗时：几个月，成本几百万美元
结果：GPT-4、DeepSeek等"基础模型"
```

**我们通常不做预训练**，因为：
- ❌ 需要海量数据（几TB文本）
- ❌ 需要大量GPU（几千张卡）
- ❌ 需要几个月时间
- ✅ 可以直接用现成的（GPT-4、DeepSeek）

---

#### 🎯 微调（Fine-tuning）

**类比**：让学生专门学习某个科目

```
输入：特定任务的标注数据（几百到几万条）
目标：学会完成特定任务
耗时：几小时到几天
结果：你的专用模型
```

**这是我们要做的**：
- ✅ 数据量小（几百到几万条）
- ✅ 成本低（几十到几百美元）
- ✅ 时间短（几小时到几天）
- ✅ 效果好（针对性强）

---

## 🔄 第二部分：微调的完整流程

### 阶段 0：准备工作

#### 0.1 选择基础模型

| 模型 | 优点 | 缺点 | 推荐场景 |
|------|------|------|---------|
| **GPT-4** | 效果最好 | 贵（$30/1M tokens） | 预算充足、要求最高质量 |
| **DeepSeek V3** | 性价比高 | 中文更强 | **推荐**（中文项目） |
| **Qwen** | 开源 | 需自己部署 | 有服务器资源 |
| **Llama 3** | 开源 | 英文为主 | 英文项目 |

**我们的选择**：DeepSeek V3
- 💰 成本低：$0.27/1M tokens（输入）
- 🇨🇳 中文强：中文训练数据多
- ⚡ 速度快：推理速度快
- 🔧 易用：API兼容OpenAI

---

#### 0.2 准备训练数据

**数据格式**：JSONL（每行一个JSON）

```jsonl
{"messages": [
  {"role": "system", "content": "你是专业的小说分析师..."},
  {"role": "user", "content": "请分析以下文本..."},
  {"role": "assistant", "content": "分析结果：..."}
]}
{"messages": [
  {"role": "system", "content": "..."},
  {"role": "user", "content": "..."},
  {"role": "assistant", "content": "..."}
]}
...
```

**数据量建议**：

| 任务类型 | 最少 | 推荐 | 理想 |
|---------|------|------|------|
| 简单分类 | 50 | 200 | 500+ |
| 信息提取 | 100 | 500 | 1000+ |
| 生成任务 | 200 | 1000 | 5000+ |
| 复杂推理 | 500 | 2000 | 10000+ |

---

### 阶段 1：生成训练数据

#### 方法A：手工标注（最准确，最慢）

```python
# 示例：标注小说情节
annotation = {
    "text": "陈野骑着二八大杠在车队中...",
    "label": {
        "type": "故事推进",
        "summary": "主角从江城出发",
        "props": ["二八大杠"],
        "location": {"from": "江城", "to": "路上"}
    }
}
```

**时间成本**：1-5分钟/条

---

#### 方法B：LLM辅助标注（快速，需要人工审核）

```python
# 使用现有模型生成初步标注
def generate_annotation(text: str) -> dict:
    prompt = f"请分析以下文本的情节要素：{text}"
    response = llm.generate(prompt)
    return response

# 人工审核和修正
annotation = generate_annotation(text)
# 人工检查 → 修正错误 → 保存
```

**时间成本**：30秒-1分钟/条（含审核）

---

#### 方法C：Few-shot + 批量生成（最快，质量需控制）

```python
# 使用少量高质量示例，让LLM生成更多
few_shot_examples = load_examples("gold_standard.jsonl")  # 5-10个精品示例

for chapter in chapters:
    annotation = llm.generate(
        prompt=build_few_shot_prompt(few_shot_examples, chapter)
    )
    # 自动质量检查
    if quality_check(annotation) > 0.8:
        save_to_training_set(annotation)
    else:
        add_to_manual_review_queue(annotation)
```

**时间成本**：几秒/条（自动）+ 人工抽查10-20%

---

### 阶段 2：数据准备与验证

#### 2.1 数据清洗

```python
def clean_training_data(data: List[dict]) -> List[dict]:
    """清洗训练数据"""
    cleaned = []
    
    for item in data:
        # 1. 去重
        if is_duplicate(item, cleaned):
            continue
        
        # 2. 格式验证
        if not validate_format(item):
            logger.warning(f"Invalid format: {item}")
            continue
        
        # 3. 质量检查
        if get_quality_score(item) < 0.7:
            logger.warning(f"Low quality: {item}")
            continue
        
        cleaned.append(item)
    
    return cleaned
```

---

#### 2.2 数据分割

```python
# 分割数据集
train_data, val_data, test_data = split_dataset(
    cleaned_data,
    train_ratio=0.8,    # 80% 训练
    val_ratio=0.1,      # 10% 验证
    test_ratio=0.1      # 10% 测试
)

# 保存
save_jsonl(train_data, "train.jsonl")
save_jsonl(val_data, "val.jsonl")
save_jsonl(test_data, "test.jsonl")
```

**为什么要分割？**

| 数据集 | 用途 | 说明 |
|--------|------|------|
| **训练集** | 训练模型 | 模型学习的数据 |
| **验证集** | 调整参数 | 防止过拟合 |
| **测试集** | 最终评估 | 模拟真实场景 |

---

### 阶段 3：模型微调

#### 3.1 选择微调方式

| 方式 | 说明 | 成本 | 效果 | 推荐场景 |
|------|------|------|------|---------|
| **API微调** | 调用服务商API | 低 | 好 | **推荐**（快速开始） |
| **LoRA微调** | 只训练部分参数 | 中 | 好 | 有GPU（单卡） |
| **全量微调** | 训练所有参数 | 高 | 最好 | 有大量GPU |

**我们推荐：API微调**
- ✅ 无需GPU
- ✅ 配置简单
- ✅ 成本可控

---

#### 3.2 DeepSeek API 微调示例

```python
from openai import OpenAI

client = OpenAI(
    api_key="your_deepseek_api_key",
    base_url="https://api.deepseek.com"
)

# 1. 上传训练数据
with open("train.jsonl", "rb") as f:
    train_file = client.files.create(
        file=f,
        purpose="fine-tune"
    )

# 2. 创建微调任务
fine_tune_job = client.fine_tuning.jobs.create(
    training_file=train_file.id,
    model="deepseek-chat",
    hyperparameters={
        "n_epochs": 3,              # 训练轮数
        "batch_size": 8,            # 批次大小
        "learning_rate": 5e-5       # 学习率
    }
)

print(f"微调任务ID: {fine_tune_job.id}")

# 3. 监控训练进度
while True:
    job_status = client.fine_tuning.jobs.retrieve(fine_tune_job.id)
    print(f"状态: {job_status.status}")
    
    if job_status.status == "succeeded":
        fine_tuned_model = job_status.fine_tuned_model
        print(f"微调完成！模型ID: {fine_tuned_model}")
        break
    elif job_status.status == "failed":
        print(f"微调失败: {job_status.error}")
        break
    
    time.sleep(60)  # 每分钟检查一次
```

---

#### 3.3 关键超参数解释

| 参数 | 说明 | 推荐值 | 调整建议 |
|------|------|--------|---------|
| **n_epochs** | 训练轮数 | 3-5 | 数据多→少轮，数据少→多轮 |
| **batch_size** | 批次大小 | 4-16 | GPU内存大→大批次 |
| **learning_rate** | 学习率 | 1e-5 ~ 5e-5 | 过拟合→降低，欠拟合→提高 |

**常见问题**：

```python
# 问题1：过拟合（训练集好，验证集差）
# 解决：减少 n_epochs 或增加 dropout

# 问题2：欠拟合（训练集和验证集都差）
# 解决：增加 n_epochs 或提高 learning_rate

# 问题3：训练不稳定（loss波动大）
# 解决：降低 learning_rate 或减小 batch_size
```

---

### 阶段 4：模型评估

#### 4.1 自动评估指标

```python
def evaluate_model(model_id: str, test_data: List[dict]) -> dict:
    """评估微调后的模型"""
    
    metrics = {
        "accuracy": 0.0,      # 准确率
        "precision": 0.0,     # 精确率
        "recall": 0.0,        # 召回率
        "f1_score": 0.0       # F1分数
    }
    
    correct = 0
    total = len(test_data)
    
    for item in test_data:
        # 使用微调模型生成
        prediction = client.chat.completions.create(
            model=model_id,
            messages=item["messages"][:-1]  # 去掉正确答案
        ).choices[0].message.content
        
        # 与正确答案对比
        ground_truth = item["messages"][-1]["content"]
        
        if compare(prediction, ground_truth):
            correct += 1
    
    metrics["accuracy"] = correct / total
    return metrics
```

---

#### 4.2 人工评估（更重要！）

```python
# 抽样测试
test_samples = random.sample(test_data, 20)

for i, sample in enumerate(test_samples):
    print(f"\n=== 测试 {i+1} ===")
    print(f"输入: {sample['input']}")
    print(f"期望输出: {sample['expected']}")
    
    # 微调模型输出
    prediction = model.generate(sample['input'])
    print(f"实际输出: {prediction}")
    
    # 人工打分
    score = input("质量评分 (1-5): ")
    feedback = input("问题描述: ")
    
    log_evaluation(sample, prediction, score, feedback)
```

**人工评估维度**：

| 维度 | 说明 | 评分标准 |
|------|------|---------|
| **准确性** | 信息是否正确 | 1-5分 |
| **完整性** | 是否遗漏重要信息 | 1-5分 |
| **流畅性** | 表达是否自然 | 1-5分 |
| **相关性** | 是否偏离主题 | 1-5分 |

---

### 阶段 5：部署与使用

#### 5.1 使用微调模型

```python
# 使用方式与原模型完全相同
response = client.chat.completions.create(
    model="ft-your-fine-tuned-model-id",  # 使用微调后的模型ID
    messages=[
        {"role": "system", "content": "你是专业的小说分析师"},
        {"role": "user", "content": "请分析以下文本..."}
    ]
)

print(response.choices[0].message.content)
```

---

#### 5.2 A/B测试

```python
def ab_test(input_text: str):
    """对比原模型和微调模型"""
    
    # 原模型
    base_response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[...]
    )
    
    # 微调模型
    finetuned_response = client.chat.completions.create(
        model="ft-your-model",
        messages=[...]
    )
    
    print("=== 原模型 ===")
    print(base_response.choices[0].message.content)
    
    print("\n=== 微调模型 ===")
    print(finetuned_response.choices[0].message.content)
    
    # 人工或自动评估哪个更好
    winner = input("哪个更好？(1=原模型, 2=微调模型): ")
    log_ab_result(input_text, winner)
```

---

## 🎯 第三部分：本项目的应用场景

### 场景1：小说情节标注

**目标**：让模型学会识别故事推进、设定、道具、时空变化

#### 训练数据生成

```python
# 1. 使用第一章分段.md作为示例
gold_standard = parse_markdown("分析资料/有原小说/01_末哥超凡公路/novel/第一章分段.md")

# 2. 用Few-shot让LLM生成更多标注
for chapter in novel_chapters[1:]:  # 第2-50章
    annotation = llm.generate_with_few_shot(
        examples=gold_standard[:3],  # 使用前3个示例
        input_text=chapter
    )
    
    # 3. 人工抽查20%
    if random.random() < 0.2:
        annotation = human_review(annotation)
    
    training_data.append(annotation)
```

---

#### 微调流程

```python
# 1. 准备数据
training_examples = []

for chapter, annotation in training_data:
    training_examples.append({
        "messages": [
            {"role": "system", "content": "你是专业的小说分析师，擅长识别故事结构..."},
            {"role": "user", "content": f"请分析以下章节：\n\n{chapter}"},
            {"role": "assistant", "content": json.dumps(annotation, ensure_ascii=False)}
        ]
    })

# 2. 保存为JSONL
save_jsonl(training_examples, "novel_annotation_train.jsonl")

# 3. 微调
fine_tune_job = client.fine_tuning.jobs.create(
    training_file=upload_file("novel_annotation_train.jsonl"),
    model="deepseek-chat",
    hyperparameters={"n_epochs": 3}
)

# 4. 等待完成并测试
fine_tuned_model_id = wait_for_completion(fine_tune_job.id)
test_on_new_chapter(fine_tuned_model_id, chapter_51)
```

---

### 场景2：解说词质量评估

**目标**：让模型学会评估生成的解说词是否抓住关键情节

#### 训练数据示例

```jsonl
{"messages": [
  {"role": "system", "content": "你是专业的解说词质量评估师..."},
  {"role": "user", "content": "原文：{novel_text}\n解说词：{script_text}\n请评估质量。"},
  {"role": "assistant", "content": "{\"score\": 85, \"reasoning\": \"抓住了核心设定和主要情节，但遗漏了二八大杠升级这个关键钩子...\"}"}
]}
```

---

## 💰 第四部分：成本估算

### DeepSeek 微调成本（2026年价格）

| 项目 | 成本 | 说明 |
|------|------|------|
| **数据生成** | $1-5 | 用基础模型生成1000条训练数据 |
| **微调训练** | $10-50 | 取决于数据量和训练轮数 |
| **模型存储** | $2/月 | 保存微调后的模型 |
| **推理使用** | $0.27/1M tokens | 使用微调模型的成本 |

**总成本（首次）**：约 $20-100  
**月度成本**：$2 存储费 + 推理费用

---

## ⚠️ 第五部分：常见陷阱与注意事项

### 陷阱1：数据质量差

```python
# ❌ 错误做法：不加审核地批量生成
for text in texts:
    annotation = llm.generate(text)
    training_data.append(annotation)  # 可能有很多错误

# ✅ 正确做法：质量控制
for text in texts:
    annotation = llm.generate(text)
    
    # 自动质量检查
    if quality_score(annotation) < 0.8:
        annotation = human_review(annotation)
    
    training_data.append(annotation)
```

---

### 陷阱2：过拟合

**现象**：训练集准确率95%，测试集准确率60%

**原因**：
- 训练数据太少
- 训练轮数太多
- 数据多样性不足

**解决**：
```python
# 1. 增加数据多样性
training_data = diversify_data(training_data)

# 2. 减少训练轮数
hyperparameters={"n_epochs": 2}  # 从5轮降到2轮

# 3. 使用正则化
hyperparameters={"dropout": 0.1}
```

---

### 陷阱3：评估不充分

```python
# ❌ 只看自动指标
print(f"准确率: {accuracy}")  # 85%，看起来不错

# ✅ 结合人工评估
auto_metrics = calculate_metrics(predictions)
human_scores = human_evaluate(samples)

print(f"自动准确率: {auto_metrics['accuracy']}")
print(f"人工平均分: {human_scores['avg_score']}")
print(f"常见问题: {human_scores['issues']}")
```

---

## 🚀 第六部分：快速开始清单

### 第1步：准备环境

```bash
# 安装依赖
pip install openai datasets pandas

# 设置API密钥
export DEEPSEEK_API_KEY="your_key"
```

---

### 第2步：收集训练数据

```python
# 方案A：手工标注（5-10个高质量示例）
examples = manually_annotate(samples[:10])

# 方案B：LLM辅助（用示例生成100-1000条）
training_data = generate_with_few_shot(examples, all_samples)
```

---

### 第3步：准备数据文件

```python
# 转换为微调格式
formatted_data = [
    {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": input_text},
            {"role": "assistant", "content": expected_output}
        ]
    }
    for input_text, expected_output in training_data
]

# 保存
save_jsonl(formatted_data, "train.jsonl")
```

---

### 第4步：启动微调

```python
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

# 上传数据
with open("train.jsonl", "rb") as f:
    file = client.files.create(file=f, purpose="fine-tune")

# 启动微调
job = client.fine_tuning.jobs.create(
    training_file=file.id,
    model="deepseek-chat"
)

print(f"微调任务ID: {job.id}")
```

---

### 第5步：等待并测试

```python
# 等待完成
model_id = wait_for_fine_tune(job.id)

# 测试
test_response = client.chat.completions.create(
    model=model_id,
    messages=[
        {"role": "user", "content": "测试输入..."}
    ]
)

print(test_response.choices[0].message.content)
```

---

## 📚 第七部分：推荐学习资源

### 官方文档

| 资源 | 链接 | 说明 |
|------|------|------|
| OpenAI Fine-tuning Guide | https://platform.openai.com/docs/guides/fine-tuning | API微调官方教程 |
| DeepSeek API Docs | https://platform.deepseek.com/api-docs | DeepSeek API文档 |
| Hugging Face Tutorials | https://huggingface.co/docs/transformers | 开源模型微调 |

### 实战教程

| 资源 | 难度 | 说明 |
|------|------|------|
| "Fine-tuning GPT for Classification" | ⭐⭐ | 分类任务入门 |
| "Custom Chatbot with Fine-tuning" | ⭐⭐⭐ | 对话任务实战 |
| "LoRA Fine-tuning Guide" | ⭐⭐⭐⭐ | 本地微调进阶 |

---

## 🎓 总结

### 关键要点

1. **微调 ≠ 从零训练**
   - 基于已有模型（如DeepSeek）
   - 只需少量数据（几百到几千条）
   - 成本低、时间短

2. **数据质量 > 数据数量**
   - 100条高质量数据 > 1000条低质量数据
   - 一定要人工审核关键样本

3. **迭代改进**
   - 先用少量数据快速测试
   - 根据效果调整数据和参数
   - 逐步扩大规模

4. **评估要全面**
   - 不能只看自动指标
   - 人工评估更重要
   - A/B测试对比基础模型

---

## 🔗 相关文档

- `docs/architecture/LAYERED_ALIGNMENT_DESIGN.md` - v4.0 对齐架构
- `docs/maintenance/PROJECT_OPTIMIZATION_V2.1.md` - 数据结构优化
- `src/prompts/novel_segmentation.yaml` - 小说分段Prompt示例

---

**准备好开始了吗？** 从收集10个高质量标注示例开始！🚀

---
*最后更新: 2026-02-05*
