"""
Novel Importer Tool
小说导入工具：读取并规范化小说文件

职责：
1. 读取 novel.txt 文件
2. 自动检测并统一编码（UTF-8）
3. 规范化换行符（统一为 \n）
4. 去除 BOM 标记
5. 基础格式验证
"""

import logging
from pathlib import Path
from typing import Union, List, Tuple, Optional

# chardet 是可选依赖，如果不可用则使用降级策略
try:
    import chardet
    CHARDET_AVAILABLE = True
except ImportError:
    CHARDET_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("chardet not available, will use fallback encoding detection")

from src.core.interfaces import BaseTool
from src.core.schemas_novel import NovelImportResult

logger = logging.getLogger(__name__)


class NovelImporter(BaseTool):
    """
    小说导入工具
    
    职责：
    - 读取原始小说文件（任意位置）
    - 自动检测文件编码（支持 UTF-8, GBK, GB2312, Big5 等）
    - 统一转换为 UTF-8
    - 规范化换行符和BOM标记
    - 保存到项目标准位置：data/projects/{project_name}/raw/novel.txt
    - 返回导入结果和元数据
    
    Example:
        >>> importer = NovelImporter()
        >>> result = importer.execute(
        ...     source_file="分析资料/.../novel.txt",
        ...     project_name="末哥超凡公路"
        ... )
        >>> print(result.saved_path)  # "data/projects/末哥超凡公路/raw/novel.txt"
        >>> print(result.encoding)     # "GBK"
        >>> print(result.char_count)   # 245830
    """
    
    name = "novel_importer"
    description = "Import and normalize novel text files to project directory"
    
    # 配置常量
    MAX_FILE_SIZE_MB = 50  # 最大文件大小（MB）
    MIN_CONTENT_LENGTH = 100  # 最小内容长度（字符）
    ENCODING_CONFIDENCE_THRESHOLD = 0.7  # 编码检测置信度阈值
    ENCODING_DETECT_BYTES = 10240  # 编码检测采样大小（10KB）
    
    # 降级编码列表（按优先级）
    FALLBACK_ENCODINGS = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'big5', 'latin1']
    
    def execute(
        self, 
        source_file: Union[str, Path],
        project_name: str,
        save_to_disk: bool = True,
        include_content: bool = False
    ) -> NovelImportResult:
        """
        导入并规范化小说文件
        
        Args:
            source_file: 原始小说文件路径（任意位置）
            project_name: 项目名称（用于确定保存位置）
            save_to_disk: 是否保存到磁盘（默认True，False用于仅内存处理）
            include_content: 是否在返回结果中包含文本内容（用于Workflow内存传递）
        
        Returns:
            NovelImportResult: 导入结果（包含保存路径和元数据）
        
        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 文件验证失败（文件过大、内容过短等）
            UnicodeDecodeError: 所有编码尝试均失败
        """
        source_file = Path(source_file)
        
        logger.info(f"Importing novel file: {source_file}")
        logger.info(f"Target project: {project_name}")
        
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
        
        # Step 5: 基础验证
        self._validate_content(normalized_content)
        
        # Step 6: 统计信息
        file_size = source_file.stat().st_size
        line_count = normalized_content.count('\n') + 1
        char_count = len(normalized_content.strip())
        
        logger.info(f"Normalization complete: {char_count} chars, {line_count} lines")
        
        # Step 7: 保存到项目目录（如果启用）
        saved_path = None
        if save_to_disk:
            saved_path = self._save_to_project(
                content=normalized_content,
                project_name=project_name
            )
            # 保存 Markdown 版本
            self._save_imported_markdown(normalized_content, project_name)
            logger.info(f"Saved to: {saved_path}")
        else:
            logger.info("Skip saving to disk (save_to_disk=False)")
            saved_path = f"data/projects/{project_name}/raw/novel.txt"  # 虚拟路径
        
        # Step 8: 构建返回结果
        return NovelImportResult(
            saved_path=str(saved_path),
            original_path=str(source_file),
            project_name=project_name,
            encoding=actual_encoding,
            file_size=file_size,
            line_count=line_count,
            char_count=char_count,
            has_bom='\ufeff' in content,  # 检测原始内容中是否有BOM
            normalization_applied=operations,
            content=normalized_content if include_content else None
        )
    
    def _validate_file(self, file_path: Path) -> None:
        """
        验证文件存在性和大小
        
        Args:
            file_path: 文件路径
        
        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 文件过大
        """
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
        """
        检测文件编码
        
        Args:
            file_path: 文件路径
        
        Returns:
            (encoding, confidence): 检测到的编码和置信度
        """
        # 读取前 N 字节进行检测
        with open(file_path, 'rb') as f:
            raw_data = f.read(self.ENCODING_DETECT_BYTES)
        
        # 如果 chardet 可用，使用它
        if CHARDET_AVAILABLE:
            detection = chardet.detect(raw_data)
            encoding = detection.get('encoding', 'utf-8')
            confidence = detection.get('confidence', 0.0)
            
            logger.debug(f"Chardet detection: {encoding} (confidence: {confidence:.2f})")
            
            # 如果置信度低，记录警告
            if confidence < self.ENCODING_CONFIDENCE_THRESHOLD:
                logger.warning(
                    f"Low encoding confidence ({confidence:.2f}), "
                    f"will try fallback encodings if needed"
                )
            
            return encoding, confidence
        else:
            # 降级策略：假设 UTF-8，低置信度
            logger.warning("chardet not available, assuming UTF-8")
            return 'utf-8', 0.5
    
    def _read_file(self, file_path: Path, detected_encoding: str) -> Tuple[str, str]:
        """
        读取文件内容
        
        Args:
            file_path: 文件路径
            detected_encoding: 检测到的编码
        
        Returns:
            (content, actual_encoding): 文件内容和实际使用的编码
        
        Raises:
            UnicodeDecodeError: 所有编码尝试均失败
        """
        # 尝试使用检测到的编码
        try:
            with open(file_path, 'r', encoding=detected_encoding) as f:
                content = f.read()
            return content, detected_encoding
        except (UnicodeDecodeError, LookupError) as e:
            logger.warning(f"Failed to read with {detected_encoding}: {e}")
        
        # 降级：尝试编码列表
        for encoding in self.FALLBACK_ENCODINGS:
            if encoding == detected_encoding:
                continue  # 已经尝试过
            
            try:
                logger.debug(f"Trying fallback encoding: {encoding}")
                with open(file_path, 'r', encoding=encoding) as f:
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
        """
        规范化内容
        
        Args:
            content: 原始文本内容
        
        Returns:
            (normalized_content, operations): 规范化后的内容和应用的操作列表
        """
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
        
        # 3. 合并多余空行（连续多个空行合并为一个）
        original_line_count = content.count('\n')
        # 使用正则表达式：连续2个及以上换行符替换为单个换行符
        import re
        content = re.sub(r'\n\s*\n', '\n', content)
        new_line_count = content.count('\n')
        if new_line_count < original_line_count:
            operations.append('merged_empty_lines')
            logger.debug(f"Merged empty lines: {original_line_count} → {new_line_count} newlines")
        
        # 4. 章节标题前添加空行（便于区分章节）
        # 匹配章节标题：=== 第X章 ... ===
        # 在章节标题前添加一个空行，但第一个章节标题前不添加
        lines = content.split('\n')
        processed_lines = []
        for i, line in enumerate(lines):
            # 检测章节标题
            if re.match(r'^===\s*第\s*\d+\s*章', line.strip()):
                # 如果不是第一行，且前一行不是空行，则添加空行
                if i > 0 and processed_lines and processed_lines[-1].strip():
                    processed_lines.append('')
                    if 'added_chapter_spacing' not in operations:
                        operations.append('added_chapter_spacing')
            processed_lines.append(line)
        content = '\n'.join(processed_lines)
        
        # 5. 去除首尾空白
        original_length = len(content)
        content = content.strip()
        if len(content) < original_length:
            operations.append('stripped_whitespace')
            logger.debug(f"Stripped {original_length - len(content)} whitespace chars")
        
        if not operations:
            operations.append('no_normalization_needed')
        
        return content, operations
    
    def _validate_content(self, content: str) -> None:
        """
        验证内容有效性
        
        Args:
            content: 规范化后的内容
        
        Raises:
            ValueError: 内容验证失败
        """
        # 检查内容非空
        if not content.strip():
            raise ValueError("File is empty after normalization")
        
        # 检查最小长度
        if len(content) < self.MIN_CONTENT_LENGTH:
            raise ValueError(
                f"Content too short ({len(content)} chars, "
                f"min: {self.MIN_CONTENT_LENGTH} chars)"
            )
        
        # 检查有效行数
        valid_lines = [line for line in content.split('\n') if line.strip()]
        if len(valid_lines) < 10:
            raise ValueError(
                f"Too few valid lines ({len(valid_lines)}, min: 10)"
            )
        
        logger.debug(f"Content validation passed: {len(content)} chars, {len(valid_lines)} valid lines")
    
    def _save_imported_markdown(self, content: str, project_name: str) -> Path:
        """
        保存为 Markdown 格式 (novel-imported.md)
        处理每一章的标题为 Markdown 标题，标准格式“# 第x章 xxxx”
        """
        import re
        
        lines = content.split('\n')
        chapter_lines = []
        found_first_chapter = False
        
        for line in lines:
            stripped = line.strip()
            # 匹配章节标题：=== 第X章 ... === 或 第X章 ...
            chapter_match = re.match(r'^(?:===)?\s*(第\s*\d+\s*章.*)(?:===)?$', stripped)
            
            if chapter_match:
                found_first_chapter = True
                title_content = chapter_match.group(1).strip()
                # 移除可能存在的尾部 ===
                title_content = re.sub(r'\s*===+$', '', title_content)
                chapter_lines.append(f"# {title_content}")
            elif found_first_chapter:
                # 第一章之后的内容都放入正文
                chapter_lines.append(line)
        
        project_dir = Path("data/projects") / project_name / "processed" / "novel"
        project_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存 novel-imported.md（只包含正文，intro.md 由 preprocess_service 从 metadata 生成）
        chapter_content = '\n'.join(chapter_lines).strip()
        output_file = project_dir / "novel-imported.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(chapter_content)
        logger.debug(f"Saved novel content: {output_file}")
        
        return output_file

    def _save_to_project(self, content: str, project_name: str) -> Path:
        """
        保存规范化后的文本到项目目录
        
        Args:
            content: 规范化后的文本内容
            project_name: 项目名称
        
        Returns:
            Path: 保存的文件路径
        """
        # 创建项目目录结构
        project_dir = Path("data/projects") / project_name / "raw"
        project_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存文件
        output_file = project_dir / "novel.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.debug(f"File saved: {output_file} ({len(content)} chars)")
        
        return output_file
