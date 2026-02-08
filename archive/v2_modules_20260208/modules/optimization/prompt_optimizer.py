"""
Prompt优化器 (Prompt Optimizer)

使用LLM分析标注错误，自动优化Prompt：
1. 聚合高Heat错误案例
2. LLM分析错误模式
3. 生成优化后的Prompt
4. 版本管理
"""

import json
import logging
import yaml
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime

from src.core.schemas import AlignmentAnnotation, PromptVersion
from src.utils.prompt_loader import load_prompts

logger = logging.getLogger(__name__)


class PromptOptimizer:
    """
    Prompt优化器
    
    工作流程：
        1. 筛选高Heat错误（Heat>60）
        2. 分析错误模式
        3. 让LLM优化Prompt
        4. 保存新版本
    """
    
    def __init__(
        self,
        llm_client,
        model_name: str = "deepseek-chat",
        prompt_dir: str = "src/prompts",
        version_dir: str = "data/alignment_optimization/prompts"
    ):
        """
        初始化Prompt优化器
        
        Args:
            llm_client: LLM客户端
            model_name: 模型名称
            prompt_dir: 当前Prompt目录
            version_dir: Prompt版本历史目录
        """
        self.llm_client = llm_client
        self.model_name = model_name
        self.prompt_dir = Path(prompt_dir)
        self.version_dir = Path(version_dir)
        self.version_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("✅ PromptOptimizer 初始化完成")
    
    async def optimize_prompt(
        self,
        layer: str,
        annotations: List[AlignmentAnnotation],
        current_prompt_key: str,
        heat_threshold: float = 60.0
    ) -> PromptVersion:
        """
        优化Prompt
        
        Args:
            layer: 层级名称
            annotations: 标注数据
            current_prompt_key: 当前Prompt的key（如"extract_world_building"）
            heat_threshold: Heat阈值
        
        Returns:
            新Prompt版本
        """
        logger.info(f"🔧 优化Prompt: {layer} (prompt_key={current_prompt_key})")
        
        # 1. 筛选高Heat错误
        high_heat_errors = [a for a in annotations if a.heat_score >= heat_threshold]
        
        if not high_heat_errors:
            logger.warning(f"   无高Heat错误（>={heat_threshold}），无需优化")
            return None
        
        logger.info(f"   高Heat错误: {len(high_heat_errors)}个")
        
        # 2. 分析错误模式
        error_patterns = self._analyze_error_patterns(high_heat_errors)
        
        # 3. 加载当前Prompt
        current_prompt = self._load_current_prompt(current_prompt_key)
        
        # 4. LLM优化
        optimized_prompt = await self._llm_optimize(
            layer=layer,
            current_prompt=current_prompt,
            error_patterns=error_patterns,
            high_heat_errors=high_heat_errors
        )
        
        # 5. 生成版本信息
        # 获取当前版本号
        existing_versions = self._get_existing_versions(layer)
        if existing_versions:
            last_version = existing_versions[-1]
            version_num = float(last_version.split('v')[1]) + 0.1
        else:
            version_num = 1.1
        
        new_version = f"v{version_num:.1f}"
        
        # 6. 创建PromptVersion
        prompt_version = PromptVersion(
            version=new_version,
            layer=layer,
            parent_version=existing_versions[-1] if existing_versions else "v1.0",
            prompt_content=optimized_prompt,
            change_summary=error_patterns["summary"],
            optimized_for=list(error_patterns["error_types"].keys()),
            heat_addressed=[a.heat_score for a in high_heat_errors]
        )
        
        # 7. 保存版本
        self._save_prompt_version(prompt_version)
        
        logger.info(f"✅ Prompt优化完成: {new_version}")
        logger.info(f"   针对错误: {', '.join(prompt_version.optimized_for)}")
        logger.info(f"   解决Heat: {sum(prompt_version.heat_addressed):.1f}")
        
        return prompt_version
    
    def _analyze_error_patterns(
        self,
        annotations: List[AlignmentAnnotation]
    ) -> Dict:
        """分析错误模式"""
        error_types = {}
        for ann in annotations:
            if ann.error_type:
                if ann.error_type not in error_types:
                    error_types[ann.error_type] = []
                error_types[ann.error_type].append({
                    "script": ann.script_content,
                    "novel": ann.novel_content,
                    "feedback": ann.human_feedback,
                    "heat": ann.heat_score
                })
        
        # 生成摘要
        summary_parts = []
        for error_type, cases in error_types.items():
            summary_parts.append(f"{error_type}({len(cases)}个)")
        summary = "修复" + "、".join(summary_parts)
        
        return {
            "error_types": error_types,
            "summary": summary,
            "total_errors": len(annotations),
            "total_heat": sum(a.heat_score for a in annotations)
        }
    
    def _load_current_prompt(self, prompt_key: str) -> str:
        """加载当前Prompt"""
        prompts = load_prompts("layered_extraction")
        prompt_data = prompts.get(prompt_key, {})
        
        if not prompt_data:
            raise ValueError(f"未找到Prompt: {prompt_key}")
        
        # 组合system和user部分
        system = prompt_data.get("system", "")
        user = prompt_data.get("user", "")
        
        return f"【System Prompt】\n{system}\n\n【User Prompt】\n{user}"
    
    async def _llm_optimize(
        self,
        layer: str,
        current_prompt: str,
        error_patterns: Dict,
        high_heat_errors: List[AlignmentAnnotation]
    ) -> str:
        """使用LLM优化Prompt"""
        # 构建错误案例描述
        cases_desc = []
        for error_type, cases in error_patterns["error_types"].items():
            cases_desc.append(f"\n【{error_type}】({len(cases)}个案例)")
            for i, case in enumerate(cases[:3], 1):  # 只展示前3个案例
                cases_desc.append(f"\n案例{i}:")
                cases_desc.append(f"  Script: {case['script']}")
                cases_desc.append(f"  Novel:  {case['novel']}")
                if case['feedback']:
                    cases_desc.append(f"  问题: {case['feedback']}")
                cases_desc.append(f"  Heat: {case['heat']:.1f}")
        
        optimization_prompt = f"""你是一个Prompt工程专家。当前Prompt在提取{layer}层信息时存在以下问题：

【高Heat错误案例】（Heat>60，总计{len(high_heat_errors)}个）
{''.join(cases_desc)}

【当前Prompt】
{current_prompt}

【优化要求】
1. 分析错误原因（为什么会出现这些问题？）
2. 针对性优化Prompt：
   - 增强【提取原则】部分
   - 增加正反例说明
   - 强调容易遗漏的关键点
   - 添加标志词识别
3. 保持原有正确的部分
4. 返回完整的优化后Prompt（包含System和User部分）

【输出格式】
直接返回优化后的完整Prompt内容，保持YAML格式，包含：
- system部分（包含优化后的【提取原则】、【示例】等）
- user部分

不要有任何额外的解释或markdown代码块标记。"""
        
        messages = [
            {"role": "system", "content": "你是一个Prompt优化专家，擅长分析错误并改进Prompt质量。"},
            {"role": "user", "content": optimization_prompt}
        ]
        
        try:
            response = self.llm_client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.3
            )
            
            optimized_prompt = response.choices[0].message.content
            
            logger.info("   LLM优化完成")
            logger.debug(f"   新Prompt长度: {len(optimized_prompt)}字符")
            
            return optimized_prompt
            
        except Exception as e:
            logger.error(f"❌ LLM优化失败: {e}")
            raise
    
    def _get_existing_versions(self, layer: str) -> List[str]:
        """获取已有版本列表"""
        layer_dir = self.version_dir / layer
        if not layer_dir.exists():
            return []
        
        versions = []
        for file in layer_dir.glob("v*.yaml"):
            versions.append(file.stem)
        
        return sorted(versions)
    
    def _save_prompt_version(self, prompt_version: PromptVersion):
        """保存Prompt版本"""
        layer_dir = self.version_dir / prompt_version.layer
        layer_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存Prompt内容
        prompt_file = layer_dir / f"{prompt_version.version}.yaml"
        with open(prompt_file, 'w', encoding='utf-8') as f:
            f.write(prompt_version.prompt_content)
        
        # 保存元数据
        meta_file = layer_dir / f"{prompt_version.version}_meta.json"
        with open(meta_file, 'w', encoding='utf-8') as f:
            json.dump(prompt_version.dict(exclude={"prompt_content"}), f, ensure_ascii=False, indent=2, default=str)
        
        # 更新metrics.json
        self._update_metrics(prompt_version)
        
        logger.info(f"   已保存: {prompt_file}")
    
    def _update_metrics(self, prompt_version: PromptVersion):
        """更新metrics文件"""
        layer_dir = self.version_dir / prompt_version.layer
        metrics_file = layer_dir / "metrics.json"
        
        # 加载现有metrics
        if metrics_file.exists():
            with open(metrics_file, 'r', encoding='utf-8') as f:
                metrics = json.load(f)
        else:
            metrics = {"versions": []}
        
        # 添加新版本metrics
        metrics["versions"].append({
            "version": prompt_version.version,
            "created_at": str(prompt_version.created_at),
            "change_summary": prompt_version.change_summary,
            "optimized_for": prompt_version.optimized_for,
            "heat_addressed": round(sum(prompt_version.heat_addressed), 2),
            "metrics": prompt_version.metrics or {}
        })
        
        # 保存
        with open(metrics_file, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, ensure_ascii=False, indent=2)
