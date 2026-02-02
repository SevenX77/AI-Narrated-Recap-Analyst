import os
import json
from typing import List
from src.agents.deepseek_analyst import DeepSeekAnalyst, get_llm_client
from src.agents.feedback_agent import FeedbackAgent
from src.modules.alignment.deepseek_alignment_engine import DeepSeekAlignmentEngine
from src.utils.text_processing import split_text_into_chunks
from src.core.schemas import NarrativeEvent

class TrainingWorkflow:
    def __init__(self, novel_path: str, srt_folder: str, workspace_dir: str):
        self.novel_path = novel_path
        self.srt_folder = srt_folder
        self.workspace_dir = workspace_dir
        self.client = get_llm_client()
        self.analyst = DeepSeekAnalyst(self.client)
        self.aligner = DeepSeekAlignmentEngine(self.client)
        self.feedback_agent = FeedbackAgent(self.client)

    def run(self):
        print(f"🚀 开始训练流程...")
        
        # 1. Load Novel
        print("1. 读取小说...")
        with open(self.novel_path, 'r', encoding='utf-8') as f:
            novel_text = f.read(60000) # Limit for demo
            
        # 2. Extract Novel Events (or load cache)
        print("2. 提取小说事件...")
        novel_events_cache = os.path.join(self.workspace_dir, "novel_events_cache.json")
        novel_events_db = []
        
        if os.path.exists(novel_events_cache):
            print("   - 加载缓存...")
            with open(novel_events_cache, 'r', encoding='utf-8') as f:
                novel_events_db = json.load(f)
        else:
            # Simple chapter splitting for demo
            import re
            chapters = re.split(r"(第[0-9]+章\s+[^\n]+)", novel_text)
            # ... (Logic to process chapters similar to batch_align_verifier) ...
            # For simplicity in this workflow implementation, let's assume we implement the splitting logic here or import it
            # To keep it clean, I'll assume we process the whole text as a few chunks if splitting logic isn't handy
            # But wait, I can copy the splitting logic.
            
            parts = chapters
            if parts and not re.match(r"(第[0-9]+章\s+[^\n]+)", parts[0]):
                parts = parts[1:] # Skip preamble for now
                
            for i in range(0, len(parts), 2):
                if i+1 < len(parts):
                    title = parts[i].strip()
                    content = parts[i+1].strip()
                    print(f"   - 处理 {title}...")
                    events = self.analyst.extract_events(content, title)
                    novel_events_db.append({"id": title, "events": [e.model_dump() for e in events]})
            
            with open(novel_events_cache, 'w', encoding='utf-8') as f:
                json.dump(novel_events_db, f, ensure_ascii=False, indent=2)

        # 3. Process SRTs
        import glob
        srt_files = sorted(glob.glob(os.path.join(self.srt_folder, "*.srt")))
        
        all_alignment_results = []
        
        for srt_path in srt_files:
            filename = os.path.basename(srt_path)
            print(f"\n3. 处理解说: {filename}")
            
            with open(srt_path, 'r', encoding='utf-8') as f:
                srt_content = f.read()
                
            # Parse SRT (Simple grouping)
            blocks = srt_content.strip().split('\n\n')
            srt_chunks = []
            current_text = []
            start_time = ""
            
            for i, block in enumerate(blocks):
                lines = block.split('\n')
                if len(lines) >= 3:
                    if not start_time: start_time = lines[1].split(' --> ')[0]
                    current_text.append(" ".join(lines[2:]))
                    if (i+1) % 10 == 0:
                        srt_chunks.append({"time": start_time, "content": " ".join(current_text)})
                        current_text = []
                        start_time = ""
            if current_text:
                srt_chunks.append({"time": start_time, "content": " ".join(current_text)})
                
            # Extract SRT Events
            print("   - 提取解说事件...")
            srt_events_data = []
            for chunk in srt_chunks:
                events = self.analyst.extract_events(chunk['content'], f"{filename} {chunk['time']}")
                srt_events_data.append({"time": chunk['time'], "events": [e.model_dump() for e in events]})
                
            # Align
            print("   - 执行对齐...")
            alignment = self.aligner.align_script_with_novel(novel_events_db, srt_events_data)
            all_alignment_results.extend(alignment)
            
        # 4. Generate Feedback
        print("\n4. 生成反馈报告...")
        feedback = self.feedback_agent.analyze_alignment(all_alignment_results)
        
        # 5. Save Methodology
        methodology_path = os.path.join(self.workspace_dir, "methodology_v1.txt")
        with open(methodology_path, 'w', encoding='utf-8') as f:
            f.write(feedback.methodology_update)
            
        report_path = os.path.join(self.workspace_dir, "feedback_report.json")
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(feedback.model_dump(), f, ensure_ascii=False, indent=2)
            
        print(f"\n✅ 训练完成！")
        print(f"   - 方法论更新: {methodology_path}")
        print(f"   - 详细报告: {report_path}")
        print(f"   - 评分: {feedback.score}")
