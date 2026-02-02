import re

def split_text_into_chunks(text: str, max_tokens: int = 1000) -> list[str]:
    """
    将长文本切分为适合 LLM 处理的片段。
    这里使用简单的按行/段落切分作为 MVP 实现。
    后续可以升级为基于语义的切分。
    """
    lines = text.split('\n')
    chunks = []
    current_chunk = []
    current_length = 0
    
    # 粗略估算：1个汉字 ≈ 1.5 tokens (这只是一个保守估计)
    # 实际上为了安全，我们可以按字符数切分，比如每 1500 字符
    MAX_CHARS = 1500 
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if current_length + len(line) > MAX_CHARS:
            chunks.append("\n".join(current_chunk))
            current_chunk = [line]
            current_length = len(line)
        else:
            current_chunk.append(line)
            current_length += len(line)
            
    if current_chunk:
        chunks.append("\n".join(current_chunk))
        
    return chunks
