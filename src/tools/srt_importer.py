"""
SRT Importer Tool
SRT导入工具：读取、解析并规范化SRT字幕文件

职责：
1. 读取 SRT 文件
2. 自动检测并统一编码（UTF-8）
3. 解析 SRT 格式（序号、时间轴、文本）
4. 验证时间轴格式
5. 修复常见格式错误
6. 保存到项目标准位置
"""

import logging
import re
from pathlib import Path
from typing import Union, List, Tuple, Optional

# chardet 是可选依赖
try:
    import chardet
    CHARDET_AVAILABLE = True
except ImportError:
    CHARDET_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("chardet not available, will use fallback encoding detection")

from src.core.interfaces import BaseTool
from src.core.schemas_script import SrtImportResult, SrtEntry

logger = logging.getLogger(__name__)


class SrtImporter(BaseTool):
    """
    SRT导入工具
    
    职责：
    - 读取原始SRT文件（任意位置）
    - 自动检测文件编码（支持 UTF-8, GBK, GB2312 等）
    - 统一转换为 UTF-8
    - 解析SRT格式（序号、时间轴、文本）
    - 验证时间轴格式
    - 修复常见格式错误（缺失空行、错误分隔符）
    - 保存到项目标准位置：data/projects/{project_name}/raw/{episode}.srt
    - 返回导入结果和SRT条目列表
    
    Example:
        >>> importer = SrtImporter()
        >>> result = importer.execute(
        ...     source_file="分析资料/.../ep01.srt",
        ...     project_name="末哥超凡公路"
        ... )
        >>> print(result.episode_name)  # "ep01"
        >>> print(result.entry_count)   # 524
        >>> print(len(result.entries))  # 524
    """
    
    name = "srt_importer"
    description = "Import and parse SRT subtitle files to project directory"
    
    # 配置常量
    MAX_FILE_SIZE_MB = 20  # 最大文件大小（MB）
    MIN_ENTRY_COUNT = 10   # 最小条目数
    ENCODING_CONFIDENCE_THRESHOLD = 0.7
    ENCODING_DETECT_BYTES = 10240  # 10KB
    
    # 降级编码列表
    FALLBACK_ENCODINGS = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'latin1']
    
    # SRT时间戳格式正则
    TIME_PATTERN = re.compile(
        r'(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})'
    )
    
    def execute(
        self,
        source_file: Union[str, Path],
        project_name: str,
        episode_name: Optional[str] = None,
        save_to_disk: bool = True,
        include_entries: bool = True
    ) -> SrtImportResult:
        """
        导入并解析SRT文件
        
        Args:
            source_file: 原始SRT文件路径（任意位置）
            project_name: 项目名称（用于确定保存位置）
            episode_name: 集数名称（如 "ep01"，不提供则从文件名推断）
            save_to_disk: 是否保存到磁盘（默认True）
            include_entries: 是否在返回结果中包含SRT条目列表（用于Workflow内存传递）
        
        Returns:
            SrtImportResult: 导入结果（包含保存路径、元数据和可选的条目列表）
        
        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 文件验证失败或SRT格式错误
        """
        source_file = Path(source_file)
        
        # 推断集数名称
        if episode_name is None:
            episode_name = source_file.stem
        
        logger.info(f"Importing SRT file: {source_file}")
        logger.info(f"Target project: {project_name}, episode: {episode_name}")
        
        # Step 1: 文件验证
        self._validate_file(source_file)
        
        # Step 2: 编码检测
        detected_encoding, confidence = self._detect_encoding(source_file)
        logger.info(f"Detected encoding: {detected_encoding} (confidence: {confidence:.2f})")
        
        # Step 3: 读取文件
        content, actual_encoding = self._read_file(source_file, detected_encoding)
        logger.info(f"Successfully read file with encoding: {actual_encoding}")
        
        # Step 4: 规范化处理
        normalized_content, operations = self._normalize_content(content)
        logger.info(f"Applied normalization operations: {operations}")
        
        # Step 5: 解析SRT
        entries = self._parse_srt(normalized_content, source_file)
        logger.info(f"Parsed {len(entries)} SRT entries")
        
        # Step 6: 验证SRT质量
        self._validate_srt_entries(entries)
        
        # Step 7: 统计信息
        file_size = source_file.stat().st_size
        total_duration = entries[-1].end_time if entries else "00:00:00,000"
        
        # Step 8: 保存到项目目录（如果启用）
        saved_path = None
        if save_to_disk:
            saved_path = self._save_to_project(
                content=normalized_content,
                project_name=project_name,
                episode_name=episode_name
            )
            logger.info(f"Saved to: {saved_path}")
        else:
            logger.info("Skip saving to disk (save_to_disk=False)")
            saved_path = f"data/projects/{project_name}/raw/{episode_name}.srt"
        
        # Step 9: 构建返回结果
        return SrtImportResult(
            saved_path=str(saved_path),
            original_path=str(source_file),
            project_name=project_name,
            episode_name=episode_name,
            encoding=actual_encoding,
            entry_count=len(entries),
            total_duration=total_duration,
            file_size=file_size,
            normalization_applied=operations,
            entries=entries if include_entries else None
        )
    
    def _validate_file(self, file_path: Path) -> None:
        """验证文件存在性和大小"""
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not file_path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")
        
        # 检查文件大小
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        if file_size_mb > self.MAX_FILE_SIZE_MB:
            raise ValueError(
                f"File too large: {file_size_mb:.2f}MB "
                f"(max: {self.MAX_FILE_SIZE_MB}MB)"
            )
        
        logger.debug(f"File validation passed: {file_size_mb:.2f}MB")
    
    def _detect_encoding(self, file_path: Path) -> Tuple[str, float]:
        """检测文件编码"""
        with open(file_path, 'rb') as f:
            raw_data = f.read(self.ENCODING_DETECT_BYTES)
        
        if CHARDET_AVAILABLE:
            detection = chardet.detect(raw_data)
            encoding = detection.get('encoding', 'utf-8')
            confidence = detection.get('confidence', 0.0)
            
            logger.debug(f"Chardet detection: {encoding} (confidence: {confidence:.2f})")
            
            if confidence < self.ENCODING_CONFIDENCE_THRESHOLD:
                logger.warning(
                    f"Low encoding confidence ({confidence:.2f}), "
                    f"will try fallback encodings if needed"
                )
            
            return encoding, confidence
        else:
            logger.warning("chardet not available, assuming UTF-8")
            return 'utf-8', 0.5
    
    def _read_file(self, file_path: Path, detected_encoding: str) -> Tuple[str, str]:
        """读取文件内容"""
        # 尝试使用检测到的编码
        try:
            with open(file_path, 'r', encoding=detected_encoding, errors='strict') as f:
                content = f.read()
            return content, detected_encoding
        except (UnicodeDecodeError, LookupError) as e:
            logger.warning(f"Failed to read with {detected_encoding}: {e}")
        
        # 降级：尝试编码列表
        for encoding in self.FALLBACK_ENCODINGS:
            if encoding == detected_encoding:
                continue
            
            try:
                logger.debug(f"Trying fallback encoding: {encoding}")
                with open(file_path, 'r', encoding=encoding, errors='strict') as f:
                    content = f.read()
                logger.warning(f"Successfully read with fallback encoding: {encoding}")
                return content, encoding
            except (UnicodeDecodeError, LookupError):
                continue
        
        # 最终降级：UTF-8 with ignore errors
        logger.warning("All encodings failed, using UTF-8 with error ignore")
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        return content, 'utf-8 (with errors ignored)'
    
    def _normalize_content(self, content: str) -> Tuple[str, List[str]]:
        """规范化内容"""
        operations = []
        
        # 1. 去除 BOM 标记
        if content.startswith('\ufeff'):
            content = content.lstrip('\ufeff')
            operations.append('removed_bom')
            logger.debug("Removed BOM marker")
        
        # 2. 统一换行符
        if '\r\n' in content or '\r' in content:
            content = content.replace('\r\n', '\n').replace('\r', '\n')
            operations.append('unified_newlines')
            logger.debug("Unified newlines to \\n")
        
        # 3. 修复时间轴格式（某些SRT使用单箭头或无空格）
        original_content = content
        content = re.sub(
            r'(\d{2}:\d{2}:\d{2},\d{3})\s*[-=]>\s*(\d{2}:\d{2}:\d{2},\d{3})',
            r'\1 --> \2',
            content
        )
        if content != original_content:
            operations.append('fixed_time_format')
            logger.debug("Fixed time arrow format")
        
        if not operations:
            operations.append('no_normalization_needed')
        
        return content, operations
    
    def _parse_srt(self, content: str, file_path: Path) -> List[SrtEntry]:
        """
        解析SRT内容
        
        Args:
            content: 规范化后的SRT文本
            file_path: 文件路径（用于错误日志）
        
        Returns:
            SRT条目列表
        """
        entries = []
        blocks = content.strip().split('\n\n')
        
        for block_idx, block in enumerate(blocks):
            lines = block.strip().split('\n')
            if len(lines) < 3:
                logger.debug(f"Skipping incomplete block {block_idx + 1}: {block[:50]}...")
                continue
            
            try:
                # 解析序号
                index_str = lines[0].strip()
                if not index_str.isdigit():
                    logger.warning(f"Invalid index in block {block_idx + 1}: '{index_str}'")
                    continue
                index = int(index_str)
                
                # 解析时间轴
                time_line = lines[1].strip()
                time_match = self.TIME_PATTERN.match(time_line)
                if not time_match:
                    logger.warning(f"Invalid time format in block {block_idx + 1}: '{time_line}'")
                    continue
                
                start_time = time_match.group(1)
                end_time = time_match.group(2)
                
                # 解析文本（可能多行）
                text = '\n'.join(lines[2:]).strip()
                
                entries.append(SrtEntry(
                    index=index,
                    start_time=start_time,
                    end_time=end_time,
                    text=text
                ))
            
            except (ValueError, IndexError) as e:
                logger.warning(f"Failed to parse block {block_idx + 1}: {e}")
                continue
        
        if not entries:
            raise ValueError(f"No valid SRT entries found in {file_path.name}")
        
        logger.info(f"Successfully parsed {len(entries)} SRT entries")
        return entries
    
    def _validate_srt_entries(self, entries: List[SrtEntry]) -> None:
        """验证SRT条目质量"""
        if len(entries) < self.MIN_ENTRY_COUNT:
            raise ValueError(
                f"Too few SRT entries ({len(entries)}, min: {self.MIN_ENTRY_COUNT})"
            )
        
        # 检查时间轴连续性（警告级别）
        discontinuities = 0
        for i in range(1, len(entries)):
            prev_end = entries[i - 1].end_time
            curr_start = entries[i].start_time
            if prev_end > curr_start:
                discontinuities += 1
        
        if discontinuities > 0:
            logger.warning(
                f"Found {discontinuities} time discontinuities "
                f"({discontinuities / len(entries) * 100:.1f}% of entries)"
            )
        
        logger.debug(f"SRT validation passed: {len(entries)} entries")
    
    def _save_to_project(
        self,
        content: str,
        project_name: str,
        episode_name: str
    ) -> Path:
        """保存规范化后的SRT到项目目录"""
        # 创建项目目录结构
        project_dir = Path("data/projects") / project_name / "raw"
        project_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存文件
        output_file = project_dir / f"{episode_name}.srt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.debug(f"File saved: {output_file}")
        
        return output_file
