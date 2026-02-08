"""
混合相似度引擎 (Hybrid Similarity Engine)

实现三层相似度计算策略：
1. 字符集过滤（快速排除无关对）
2. Embedding粗筛（中等精度）
3. LLM精确判断（高精度，带解释）
"""

import logging
import json
from typing import Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SimilarityResult:
    """相似度计算结果"""
    score: float  # 0.0-1.0
    method: str  # "char_filter" | "embedding" | "llm"
    reasoning: Optional[str] = None  # LLM判断的理由


class HybridSimilarityEngine:
    """
    混合相似度引擎
    
    策略：
        1. 字符集Jaccard < 0.2 → 快速排除
        2. 0.2 ≤ Embedding < 0.5 → 中等相关
        3. Embedding ≥ 0.5 → LLM精确判断
    
    优势：
        - 速度：90%的对用字符过滤，秒级完成
        - 准确：关键的10%用LLM精判
        - 可解释：LLM给出判断理由
    """
    
    def __init__(
        self,
        llm_client,
        model_name: str = "deepseek-chat",
        use_embedding: bool = True
    ):
        """
        初始化混合相似度引擎
        
        Args:
            llm_client: LLM客户端
            model_name: 模型名称
            use_embedding: 是否使用Embedding层（如果False，跳过直接到LLM）
        """
        self.llm_client = llm_client
        self.model_name = model_name
        self.use_embedding = use_embedding
        
        # 尝试加载Embedding模型
        self.embedding_model = None
        if use_embedding:
            try:
                from sentence_transformers import SentenceTransformer
                self.embedding_model = SentenceTransformer(
                    'paraphrase-multilingual-MiniLM-L12-v2'
                )
                logger.info("✅ Embedding模型加载成功")
            except ImportError:
                logger.warning("⚠️ sentence-transformers未安装，跳过Embedding层")
                self.use_embedding = False
            except Exception as e:
                logger.warning(f"⚠️ Embedding模型加载失败: {e}，跳过Embedding层")
                self.use_embedding = False
        
        logger.info(f"✅ HybridSimilarityEngine 初始化完成 (use_embedding={self.use_embedding})")
    
    async def calculate_similarity(
        self,
        text1: str,
        text2: str,
        layer: Optional[str] = None
    ) -> SimilarityResult:
        """
        计算两段文本的相似度
        
        Args:
            text1: 文本1（通常是Script）
            text2: 文本2（通常是Novel）
            layer: 层级（用于调整阈值）
        
        Returns:
            SimilarityResult
        """
        # Step 1: 字符集快速过滤
        char_sim = self._calculate_char_similarity(text1, text2)
        
        if char_sim < 0.2:
            logger.debug(f"   字符过滤排除: {char_sim:.2f} < 0.2")
            return SimilarityResult(
                score=char_sim,
                method="char_filter",
                reasoning="字符重叠度低，快速排除"
            )
        
        # Step 2: Embedding粗筛（如果可用）
        if self.use_embedding and self.embedding_model:
            emb_sim = self._calculate_embedding_similarity(text1, text2)
            
            if emb_sim < 0.5:
                logger.debug(f"   Embedding判断: {emb_sim:.2f} < 0.5")
                return SimilarityResult(
                    score=emb_sim,
                    method="embedding",
                    reasoning="Embedding相似度中等"
                )
            
            logger.debug(f"   Embedding候选: {emb_sim:.2f} ≥ 0.5, 进入LLM精判")
        else:
            # 如果没有Embedding，字符相似度>0.2就进入LLM
            logger.debug(f"   字符候选: {char_sim:.2f} ≥ 0.2, 进入LLM精判")
        
        # Step 3: LLM精确判断
        llm_result = await self._calculate_llm_similarity(text1, text2)
        return llm_result
    
    def _calculate_char_similarity(self, text1: str, text2: str) -> float:
        """字符集Jaccard相似度（快速过滤）"""
        set1 = set(text1)
        set2 = set(text2)
        
        intersection = set1 & set2
        union = set1 | set2
        
        if not union:
            return 0.0
        
        return len(intersection) / len(union)
    
    def _calculate_embedding_similarity(self, text1: str, text2: str) -> float:
        """Embedding余弦相似度"""
        try:
            from scipy.spatial.distance import cosine
            
            emb1 = self.embedding_model.encode(text1)
            emb2 = self.embedding_model.encode(text2)
            
            return 1 - cosine(emb1, emb2)
        except Exception as e:
            logger.warning(f"Embedding计算失败: {e}")
            return 0.5  # 返回中等值，进入LLM判断
    
    async def _calculate_llm_similarity(
        self,
        text1: str,
        text2: str
    ) -> SimilarityResult:
        """LLM语义相似度（精确判断）"""
        prompt = f"""比较以下两段文本的语义相似度，返回0-1之间的分数。

【文本1】（Script）
{text1}

【文本2】（Novel）
{text2}

【评分标准】
- 1.0：意思完全一致
- 0.8-0.9：核心意思相同，细节略有差异
- 0.6-0.7：部分相关
- 0.3-0.5：有关联但主题不同
- 0.0-0.2：无关

【重要】
- 同义词视为相同（如"降临"和"爆发"）
- 忽略修饰词的差异（如"全球"的有无）
- 关注核心语义，而非字面相似

【返回JSON格式】
{{
    "score": 0.92,
    "reasoning": "核心意思完全一致，Script用'降临'，Novel用'爆发'，本质上表达同一事件。Script省略'全球'修饰，但不影响核心语义。"
}}"""
        
        messages = [
            {"role": "system", "content": "你是一个语义相似度评估专家。"},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = self.llm_client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            result_json = json.loads(response.choices[0].message.content)
            score = float(result_json.get("score", 0.5))
            reasoning = result_json.get("reasoning", "")
            
            logger.debug(f"   LLM判断: {score:.2f} - {reasoning[:50]}...")
            
            return SimilarityResult(
                score=score,
                method="llm",
                reasoning=reasoning
            )
            
        except Exception as e:
            logger.error(f"LLM相似度计算失败: {e}")
            # 降级到字符相似度
            char_sim = self._calculate_char_similarity(text1, text2)
            return SimilarityResult(
                score=char_sim,
                method="char_filter",
                reasoning=f"LLM调用失败，降级到字符相似度: {str(e)}"
            )
