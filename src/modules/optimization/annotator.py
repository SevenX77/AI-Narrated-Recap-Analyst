"""
对齐结果标注工具 (Alignment Annotator)

CLI交互式标注界面，用于：
1. 查看对齐结果
2. 标记错误（缺失/不完整/错配/相似度错误）
3. 提供人类反馈
4. 保存标注数据
"""

import json
import logging
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime

from src.core.schemas import AlignmentAnnotation

logger = logging.getLogger(__name__)


class AlignmentAnnotator:
    """
    对齐结果标注器
    
    工作流程：
        1. 加载对齐结果
        2. 逐条展示对齐对
        3. 用户标注（正确/错误）
        4. 保存标注数据
    """
    
    def __init__(self, output_dir: str = "data/alignment_optimization/annotations"):
        """
        初始化标注器
        
        Args:
            output_dir: 标注数据输出目录
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.annotations: List[AlignmentAnnotation] = []
        
        logger.info(f"✅ AlignmentAnnotator 初始化完成")
        logger.info(f"   输出目录: {self.output_dir}")
    
    def annotate_alignment_result(
        self,
        alignment_result_path: str,
        project_id: str,
        episode: str,
        annotator_name: Optional[str] = None
    ) -> List[AlignmentAnnotation]:
        """
        标注对齐结果
        
        Args:
            alignment_result_path: 对齐结果文件路径
            project_id: 项目ID
            episode: 集数
            annotator_name: 标注人姓名
        
        Returns:
            标注列表
        """
        # 1. 加载对齐结果
        with open(alignment_result_path, 'r', encoding='utf-8') as f:
            alignment_data = json.load(f)
        
        self.annotations = []
        
        print("\n" + "="*60)
        print(f"  对齐结果标注")
        print(f"  项目: {project_id} | 集数: {episode}")
        print("="*60)
        print("\n按Ctrl+C可随时退出并保存已标注数据\n")
        
        try:
            # 2. 遍历各层
            for layer_name in ["world_building", "game_mechanics", "items_equipment", "plot_events"]:
                layer_data = alignment_data.get("layered_alignment", {}).get(layer_name, {})
                alignments = layer_data.get("alignments", [])
                
                if not alignments:
                    print(f"\n⏭  {layer_name}层无对齐数据，跳过\n")
                    continue
                
                print(f"\n{'='*60}")
                print(f"  {layer_name}层 ({len(alignments)}条对齐)")
                print(f"{'='*60}\n")
                
                # 3. 逐条标注
                for idx, alignment in enumerate(alignments, 1):
                    annotation = self._annotate_single_alignment(
                        alignment=alignment,
                        project_id=project_id,
                        episode=episode,
                        layer=layer_name,
                        index=idx,
                        total=len(alignments),
                        annotator=annotator_name
                    )
                    
                    if annotation:
                        self.annotations.append(annotation)
        
        except KeyboardInterrupt:
            print("\n\n⚠️  用户中断，保存已标注数据...")
        
        # 4. 保存标注
        if self.annotations:
            self._save_annotations(project_id, episode)
            print(f"\n✅ 已保存 {len(self.annotations)} 条标注")
        else:
            print("\n⚠️  无标注数据")
        
        return self.annotations
    
    def _annotate_single_alignment(
        self,
        alignment: Dict,
        project_id: str,
        episode: str,
        layer: str,
        index: int,
        total: int,
        annotator: Optional[str]
    ) -> Optional[AlignmentAnnotation]:
        """标注单条对齐"""
        script_node = alignment.get("script_node", {})
        novel_node = alignment.get("novel_node", {})
        similarity = alignment.get("similarity", 0.0)
        confidence = alignment.get("confidence", "unknown")
        reasoning = alignment.get("reasoning")
        
        # 显示对齐信息
        print(f"┌{'─'*58}┐")
        print(f"│ 对齐 {index}/{total} (Layer: {layer}){' '*(58-len(f' 对齐 {index}/{total} (Layer: {layer})'))}│")
        print(f"├{'─'*58}┤")
        print(f"│ Script: {script_node.get('content', '')[:45]:<45} │")
        print(f"│ Novel:  {novel_node.get('content', '')[:45]:<45} │")
        print(f"├{'─'*58}┤")
        print(f"│ 系统判断:                                               │")
        print(f"│   相似度: {similarity:.2f}                                         │")
        print(f"│   置信度: {confidence}                                        │")
        if reasoning:
            print(f"│   理由: {reasoning[:48]:<48} │")
        print(f"└{'─'*58}┘")
        
        # 获取用户输入
        while True:
            response = input("\n这个匹配正确吗？[y]正确 [n]错误 [s]跳过 [q]退出: ").strip().lower()
            
            if response == 'q':
                raise KeyboardInterrupt
            
            if response == 's':
                return None
            
            if response in ['y', 'n']:
                break
            
            print("❌ 无效输入，请输入 y/n/s/q")
        
        is_correct = (response == 'y')
        
        # 如果错误，获取详细信息
        error_type = None
        human_feedback = None
        human_similarity = None
        
        if not is_correct:
            print("\n错误类型：")
            print("  [1] missing - 缺失关键信息")
            print("  [2] incomplete - 提取不完整")
            print("  [3] wrong_match - 错误匹配")
            print("  [4] similarity_wrong - 相似度评分错误")
            
            while True:
                error_choice = input("请选择错误类型 [1-4]: ").strip()
                if error_choice in ['1', '2', '3', '4']:
                    error_types = {
                        '1': 'missing',
                        '2': 'incomplete',
                        '3': 'wrong_match',
                        '4': 'similarity_wrong'
                    }
                    error_type = error_types[error_choice]
                    break
                print("❌ 无效输入，请输入 1-4")
            
            # 获取反馈
            feedback = input("\n请描述问题（可选，按Enter跳过）: ").strip()
            if feedback:
                human_feedback = feedback
            
            # 如果是相似度错误，获取人类评分
            if error_type == 'similarity_wrong':
                while True:
                    try:
                        score_input = input(f"你认为正确的相似度是多少？[0.0-1.0]（当前系统评分：{similarity:.2f}）: ").strip()
                        if not score_input:
                            break
                        human_similarity = float(score_input)
                        if 0.0 <= human_similarity <= 1.0:
                            break
                        print("❌ 请输入0.0-1.0之间的数字")
                    except ValueError:
                        print("❌ 无效输入")
        
        # 创建标注
        annotation = AlignmentAnnotation(
            annotation_id=f"{project_id}_{episode}_{layer}_{index}_{int(datetime.now().timestamp())}",
            project_id=project_id,
            episode=episode,
            layer=layer,
            script_node_id=script_node.get("node_id", ""),
            novel_node_id=novel_node.get("node_id", ""),
            script_content=script_node.get("content", ""),
            novel_content=novel_node.get("content", ""),
            system_similarity=similarity,
            system_confidence=confidence,
            is_correct_match=is_correct,
            error_type=error_type,
            human_similarity=human_similarity,
            human_feedback=human_feedback,
            heat_score=0.0,  # 将由HeatCalculator计算
            annotator=annotator
        )
        
        print(f"\n✅ 标注已记录\n")
        
        return annotation
    
    def _save_annotations(self, project_id: str, episode: str):
        """保存标注数据"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{project_id}_{episode}_annotations_{timestamp}.jsonl"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            for annotation in self.annotations:
                f.write(json.dumps(annotation.dict(), ensure_ascii=False, default=str) + '\n')
        
        logger.info(f"✅ 标注已保存到: {filepath}")
    
    def load_annotations(self, annotation_file: str) -> List[AlignmentAnnotation]:
        """加载标注数据"""
        annotations = []
        
        with open(annotation_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    annotations.append(AlignmentAnnotation(**data))
        
        logger.info(f"✅ 加载了 {len(annotations)} 条标注")
        return annotations
