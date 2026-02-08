"""
Tools Package
工具包：独立、无状态、可复用的原子操作

分类：
- Novel Processing: 小说处理工具
- Script Processing: Script处理工具
- Analysis: 分析工具
"""

# Novel Processing Tools
from src.tools.novel_processor import NovelSegmentationTool
from src.tools.novel_chapter_processor import NovelChapterProcessor
from src.tools.introduction_validator import IntroductionValidator

# Script Processing Tools
from src.tools.srt_processor import SrtScriptProcessor

# Analysis Tools
from src.tools.novel_segmentation_analyzer import NovelSegmentationAnalyzer
from src.tools.novel_chapter_analyzer import NovelChapterAnalyzer
from src.tools.script_segment_aligner import ScriptSegmentAligner
from src.tools.key_info_extractor import KeyInfoExtractor

__all__ = [
    # Novel Processing
    "NovelSegmentationTool",
    "NovelChapterProcessor",
    "IntroductionValidator",
    
    # Script Processing
    "SrtScriptProcessor",
    
    # Analysis
    "NovelSegmentationAnalyzer",
    "NovelChapterAnalyzer",
    "ScriptSegmentAligner",
    "KeyInfoExtractor",
]
