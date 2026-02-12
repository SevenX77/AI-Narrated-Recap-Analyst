"""测试质量报告生成（不依赖API）"""

import sys
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.workflows.novel_processing_workflow import NovelProcessingWorkflow
from src.core.schemas_novel import ParagraphSegmentationResult, ParagraphSegment

def test_quality_report():
    """测试质量报告生成"""
    print("🧪 测试质量报告生成")
    
    # 创建模拟分段数据
    seg_results = {
        1: ParagraphSegmentationResult(
            chapter_number=1,
            total_paragraphs=9,
            paragraphs=[
                ParagraphSegment(index=1, type="A", content="这是世界观设定", start_char=0, end_char=10),
                ParagraphSegment(index=2, type="A", content="这是另一个设定", start_char=10, end_char=20),
                ParagraphSegment(index=3, type="B", content="这是事件1", start_char=20, end_char=30),
                ParagraphSegment(index=4, type="B", content="这是事件2", start_char=30, end_char=40),
                ParagraphSegment(index=5, type="B", content="这是事件3", start_char=40, end_char=50),
                ParagraphSegment(index=6, type="B", content="这是事件4", start_char=50, end_char=60),
                ParagraphSegment(index=7, type="C", content="【系统提示】", start_char=60, end_char=70),
                ParagraphSegment(index=8, type="B", content="这是事件5", start_char=70, end_char=80),
                ParagraphSegment(index=9, type="B", content="这是事件6", start_char=80, end_char=90),
            ],
            metadata={"text_restoration_rate": 99.8}
        )
    }
    
    # 创建临时测试目录
    test_dir = Path("data/projects/quality_report_test/processing")
    test_dir.mkdir(parents=True, exist_ok=True)
    (test_dir / "reports").mkdir(exist_ok=True)
    
    # 生成报告
    workflow = NovelProcessingWorkflow()
    workflow._output_step4_report(seg_results, str(test_dir))
    
    # 检查报告是否生成
    report_path = test_dir / "reports" / "step4_segmentation_quality.md"
    if report_path.exists():
        print(f"✅ 质量报告生成成功: {report_path}")
        with open(report_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 显示前30行
        lines = content.split('\n')[:30]
        print("\n📄 报告内容预览：")
        print("-" * 60)
        for line in lines:
            print(line)
        print("-" * 60)
        
        # 检查关键要素
        if "质量评分" in content:
            print("✅ 包含质量评分")
        if "ABC分布合理性" in content:
            print("✅ 包含ABC分布分析")
        if "改进建议" in content:
            print("✅ 包含改进建议")
        
        return True
    else:
        print(f"❌ 报告未生成: {report_path}")
        return False

if __name__ == "__main__":
    success = test_quality_report()
    exit(0 if success else 1)
