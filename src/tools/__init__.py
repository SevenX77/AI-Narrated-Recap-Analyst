"""
Tools Package
工具包：独立、无状态、可复用的原子操作

分类：
- Novel Processing: 小说处理工具（Phase I）
- Script Processing: Script处理工具（Phase I）
- Analysis: 分析工具（Phase II）

注意：旧工具已归档到 archive/v2_tools_20260208/
"""

# Phase I: Novel Processing Tools
from src.tools.novel_importer import NovelImporter
from src.tools.novel_metadata_extractor import NovelMetadataExtractor
from src.tools.novel_chapter_detector import NovelChapterDetector
from src.tools.novel_segmenter import NovelSegmenter

# TODO: 待实现的工具
# from src.tools.novel_segmenter import NovelSegmenter
# from src.tools.novel_chapter_splitter import NovelChapterSplitter

# TODO: Phase I - Script Processing Tools
# from src.tools.srt_importer import SrtImporter
# from src.tools.srt_text_extractor import SrtTextExtractor
# from src.tools.script_segmenter import ScriptSegmenter

__all__ = [
    # Phase I - Novel Processing
    "NovelImporter",
    "NovelMetadataExtractor",
    "NovelChapterDetector",
    "NovelSegmenter",
    
    # TODO: 添加更多工具
]
