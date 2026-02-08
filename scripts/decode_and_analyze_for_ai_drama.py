#!/usr/bin/env python3
"""
解码番茄小说榜单数据 + AI爽剧改编分析
- 解码混淆的书名和作者名
- 针对AI爽剧改编重新评估
"""

import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime
import sys

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tools.fanqie_decoder import FanqieTextDecoder


def parse_readers(readers_str):
    """解析读者数字符串为数值（单位：万）"""
    if not readers_str:
        return 0.0
    
    readers_str = readers_str.strip()
    
    if '万' in readers_str:
        num = readers_str.replace('万', '')
        try:
            return float(num)
        except:
            return 0.0
    
    try:
        return float(readers_str) / 10000
    except:
        return 0.0


def calculate_ai_drama_score(novel_info):
    """
    计算AI爽剧改编适配度评分（0-100分）
    
    评分维度：
    1. 类型适配度（40分）：系统流、重生流、逆袭题材得高分
    2. 热度（30分）：读者数越高分数越高
    3. 完结状态（15分）：已完结更适合改编
    4. 节奏（15分）：根据类型判断节奏快慢
    """
    score = 0
    
    # 1. 类型适配度（40分）
    genre = novel_info.get('genre', '')
    title = novel_info.get('title', '')
    
    # 超高适配类型（40分）
    high_fit_keywords = ['系统', '重生', '逆袭', '赘婿', '战神', '装逼', '打脸', '签到', '开局']
    # 高适配类型（30-35分）
    good_fit_keywords = ['都市', '豪门', '总裁', '快穿', '修真', '高武', '脑洞']
    # 中等适配类型（20-25分）
    medium_fit_keywords = ['悬疑', '玄幻', '历史', '宫斗', '种田']
    # 低适配类型（10-15分）
    low_fit_keywords = ['衍生', '同人', '慢热']
    
    # 检查标题和类型中的关键词
    combined_text = f"{title}{genre}"
    
    if any(kw in combined_text for kw in high_fit_keywords):
        score += 40
    elif any(kw in combined_text for kw in good_fit_keywords):
        score += 32
    elif any(kw in combined_text for kw in medium_fit_keywords):
        score += 22
    elif any(kw in combined_text for kw in low_fit_keywords):
        score += 12
    else:
        score += 25  # 默认分数
    
    # 2. 热度（30分）
    readers_num = novel_info.get('readers_num', 0)
    if readers_num >= 100:
        score += 30
    elif readers_num >= 50:
        score += 25
    elif readers_num >= 20:
        score += 20
    elif readers_num >= 10:
        score += 15
    elif readers_num >= 5:
        score += 10
    else:
        score += 5
    
    # 3. 完结状态（15分）
    if novel_info.get('status') == '已完结':
        score += 15
    else:
        score += 10  # 连载中也可以，但完结更好
    
    # 4. 节奏评分（15分）- 基于类型判断
    fast_pace_types = ['都市脑洞', '都市高武', '快穿', '系统', '游戏']
    medium_pace_types = ['豪门', '总裁', '悬疑', '修真']
    slow_pace_types = ['种田', '古风', '历史']
    
    if any(t in genre for t in fast_pace_types):
        score += 15
    elif any(t in genre for t in medium_pace_types):
        score += 10
    elif any(t in genre for t in slow_pace_types):
        score += 5
    else:
        score += 10
    
    # 额外加分项
    # - 标题中有爽文元素
    bonus_title_keywords = ['崩', '破防', '爆', '疯', '哭', '泪', '震惊', '惊']
    if any(kw in title for kw in bonus_title_keywords):
        score = min(100, score + 5)
    
    return min(100, score)


def categorize_for_ai_drama(ranking_name):
    """根据榜单名称分类并评估AI爽剧适配度"""
    if '男频' in ranking_name:
        gender = '男频'
    elif '女频' in ranking_name:
        gender = '女频'
    else:
        gender = '未知'
    
    is_new = '新书榜' in ranking_name
    genre = ranking_name.split('-')[-1] if '-' in ranking_name else ranking_name
    
    # AI爽剧适配度评级（针对AI生成的特点）
    # 核心考虑：爽点密集、节奏快、剧情简单、视觉冲击强
    
    # S级：爽点密集，节奏极快，最适合AI短剧
    s_tier_keywords = ['战神赘婿', '都市脑洞', '都市高武', '逆袭', '系统']
    
    # A级：爽文属性强，节奏快
    a_tier_keywords = ['豪门', '总裁', '快穿', '修真', '悬疑脑洞', '玄幻脑洞']
    
    # B级：有爽点但节奏适中
    b_tier_keywords = ['宫斗', '宅斗', '游戏', '都市日常', '年代', '种田']
    
    # C级：节奏慢或改编难度大
    c_tier_keywords = ['衍生', '古风', '历史', '科幻末世']
    
    if any(kw in genre for kw in s_tier_keywords):
        ai_fit_level = 'S'
    elif any(kw in genre for kw in a_tier_keywords):
        ai_fit_level = 'A'
    elif any(kw in genre for kw in b_tier_keywords):
        ai_fit_level = 'B'
    else:
        ai_fit_level = 'C'
    
    return {
        'gender': gender,
        'is_new': is_new,
        'genre': genre,
        'ai_fit_level': ai_fit_level
    }


def decode_and_analyze():
    """解码所有榜单并生成AI爽剧改编分析"""
    rankings_dir = Path("data/fanqie/rankings")
    decoder = FanqieTextDecoder()
    
    print("🔓 开始解码榜单数据...")
    print("=" * 80)
    
    # 读取所有榜单
    ranking_files = [f for f in rankings_dir.glob("*.json") 
                     if "_test" not in f.name 
                     and f.name not in ['todo_rankings.json', 'ranking_urls.json']]
    
    all_novels = []
    genre_stats = defaultdict(lambda: {
        'count': 0,
        'total_readers': 0,
        'total_ai_score': 0,
        'novels': [],
        'ai_fit_level': 'C',
        'gender': '',
        'is_new': False
    })
    
    decoded_count = 0
    
    for ranking_file in ranking_files:
        with open(ranking_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        ranking_name = data.get('ranking_name', ranking_file.stem)
        category_info = categorize_for_ai_drama(ranking_name)
        
        for novel in data.get('novels', []):
            # 解码书名和作者名
            original_title = novel.get('title', '')
            original_author = novel.get('author', '')
            
            decoded_title = decoder.execute(original_title)
            decoded_author = decoder.execute(original_author)
            
            if decoded_title != original_title or decoded_author != original_author:
                decoded_count += 1
            
            readers_num = parse_readers(novel.get('readers', '0'))
            
            novel_info = {
                'title': decoded_title,
                'author': decoded_author,
                'url': novel.get('url', ''),
                'status': novel.get('status', ''),
                'readers': novel.get('readers', ''),
                'readers_num': readers_num,
                'latest_chapter': novel.get('latest_chapter', ''),
                'last_updated': novel.get('last_updated', ''),
                'ranking': ranking_name,
                'rank': novel.get('rank', 0),
                **category_info
            }
            
            # 计算AI爽剧适配度评分
            ai_score = calculate_ai_drama_score(novel_info)
            novel_info['ai_score'] = ai_score
            
            all_novels.append(novel_info)
            
            # 按类型统计
            genre = category_info['genre']
            genre_stats[genre]['count'] += 1
            genre_stats[genre]['total_readers'] += readers_num
            genre_stats[genre]['total_ai_score'] += ai_score
            genre_stats[genre]['novels'].append(novel_info)
            genre_stats[genre]['ai_fit_level'] = category_info['ai_fit_level']
            genre_stats[genre]['gender'] = category_info['gender']
            genre_stats[genre]['is_new'] = category_info['is_new']
    
    print(f"✅ 解码完成！共解码 {decoded_count} 条数据")
    print(f"📚 总小说数: {len(all_novels)}")
    print(f"📊 类型数: {len(genre_stats)}\n")
    
    # 保存解码后的数据
    save_decoded_data(all_novels)
    
    return all_novels, genre_stats


def save_decoded_data(all_novels):
    """保存解码后的完整数据"""
    output_file = Path("data/fanqie/decoded_novels.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_novels, f, ensure_ascii=False, indent=2)
    print(f"💾 已保存解码数据: {output_file}\n")


def generate_ai_drama_report(all_novels, genre_stats):
    """生成AI爽剧改编分析报告"""
    output_dir = Path("data/fanqie")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = output_dir / f"ai_drama_analysis_{timestamp}.md"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# 番茄小说 AI爽剧改编分析报告\n\n")
        f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**分析对象**: 72个榜单，{len(all_novels)}部小说（已解码）\n\n")
        f.write("**评估维度**: AI爽剧适配度（爽点密集度、节奏、热度、完成度）\n\n")
        f.write("---\n\n")
        
        # 1. AI爽剧适配度排行
        f.write("## 🎬 一、类型AI爽剧适配度排行\n\n")
        
        # 计算每个类型的平均AI评分
        for genre, stats in genre_stats.items():
            if stats['count'] > 0:
                stats['avg_ai_score'] = stats['total_ai_score'] / stats['count']
                stats['avg_readers'] = stats['total_readers'] / stats['count']
            else:
                stats['avg_ai_score'] = 0
                stats['avg_readers'] = 0
        
        sorted_genres = sorted(genre_stats.items(), 
                              key=lambda x: x[1]['avg_ai_score'], 
                              reverse=True)
        
        f.write("| 排名 | 类型 | 性别 | AI适配等级 | 平均AI评分 | 小说数 | 平均读者数 | 推荐理由 |\n")
        f.write("|------|------|------|------------|------------|--------|------------|----------|\n")
        
        for idx, (genre, stats) in enumerate(sorted_genres, 1):
            fit_icon = {'S': '🔥🔥🔥🔥', 'A': '🔥🔥🔥', 'B': '🔥🔥', 'C': '🔥'}[stats['ai_fit_level']]
            reason = get_ai_fit_reason(genre, stats['ai_fit_level'])
            f.write(f"| {idx} | {genre} | {stats['gender']} | {stats['ai_fit_level']} {fit_icon} | {stats['avg_ai_score']:.1f}分 | {stats['count']} | {stats['avg_readers']:.1f}万 | {reason} |\n")
        
        f.write("\n---\n\n")
        
        # 2. AI爽剧改编推荐榜 TOP 100
        f.write("## 🏆 二、AI爽剧改编推荐榜 TOP 100\n\n")
        f.write("**排序规则**: AI适配度评分（综合爽点密度、节奏、热度、完成度）\n\n")
        
        top_novels = sorted(all_novels, key=lambda x: x['ai_score'], reverse=True)[:100]
        
        f.write("| 排名 | 书名 | 作者 | 类型 | AI评分 | 读者数 | 状态 | 推荐标签 |\n")
        f.write("|------|------|------|------|--------|--------|------|----------|\n")
        
        for idx, novel in enumerate(top_novels, 1):
            tags = get_novel_tags(novel)
            f.write(f"| {idx} | {novel['title']} | {novel['author']} | {novel['genre']} | {novel['ai_score']:.0f}分 | {novel['readers']} | {novel['status']} | {tags} |\n")
        
        f.write("\n---\n\n")
        
        # 3. 分级推荐
        f.write("## 🎯 三、分级推荐（按AI适配等级）\n\n")
        
        # S级推荐
        f.write("### 🔥🔥🔥🔥 S级：顶级爽剧素材（强烈推荐）\n\n")
        f.write("**特点**: 爽点极度密集、节奏超快、金手指明显、打脸情节爆炸\n\n")
        s_novels = [n for n in all_novels if n['ai_fit_level'] == 'S']
        s_novels = sorted(s_novels, key=lambda x: x['ai_score'], reverse=True)[:30]
        
        f.write("| 排名 | 书名 | 作者 | 类型 | AI评分 | 读者数 | 爽点分析 |\n")
        f.write("|------|------|------|------|--------|--------|----------|\n")
        
        for idx, novel in enumerate(s_novels, 1):
            analysis = analyze_shuang_points(novel)
            f.write(f"| {idx} | {novel['title']} | {novel['author']} | {novel['genre']} | {novel['ai_score']:.0f}分 | {novel['readers']} | {analysis} |\n")
        
        f.write("\n")
        
        # A级推荐
        f.write("### 🔥🔥🔥 A级：优质爽剧素材（推荐）\n\n")
        f.write("**特点**: 爽点密集、节奏快、有明确升级线\n\n")
        a_novels = [n for n in all_novels if n['ai_fit_level'] == 'A']
        a_novels = sorted(a_novels, key=lambda x: x['ai_score'], reverse=True)[:20]
        
        f.write("| 排名 | 书名 | 类型 | AI评分 | 读者数 |\n")
        f.write("|------|------|------|--------|--------|\n")
        
        for idx, novel in enumerate(a_novels, 1):
            f.write(f"| {idx} | {novel['title']} | {novel['genre']} | {novel['ai_score']:.0f}分 | {novel['readers']} |\n")
        
        f.write("\n---\n\n")
        
        # 4. AI爽剧制作指南
        f.write("## 💡 四、AI爽剧制作指南\n\n")
        
        f.write("### 🎬 为什么这些小说适合AI爽剧？\n\n")
        f.write("1. **爽点密集**：打脸、装逼、逆袭情节多，每3-5分钟一个高潮\n")
        f.write("2. **节奏快速**：AI生成适合短剧，15-30秒一个转折点\n")
        f.write("3. **剧情简单**：主线明确，不需要复杂的人物关系\n")
        f.write("4. **视觉冲击**：AI可以快速生成特效场景，不受成本限制\n")
        f.write("5. **金手指明显**：系统流、重生流最适合AI呈现\n\n")
        
        f.write("### 🎯 AI爽剧制作建议\n\n")
        f.write("#### S级题材制作策略\n")
        f.write("- **战神赘婿类**: 每集重点突出一次大型打脸，配合震撼音效\n")
        f.write("- **系统流**: 用AI生成炫酷的系统界面和数据面板\n")
        f.write("- **都市装逼**: 快速剪辑，配合夸张的反派表情包\n")
        f.write("- **重生逆袭**: 利用时空穿越特效，对比前世今生\n\n")
        
        f.write("#### 集数建议\n")
        f.write("- **短剧模式**: 80-100集，每集1-3分钟\n")
        f.write("- **中篇模式**: 40-60集，每集3-5分钟\n")
        f.write("- **长篇模式**: 20-30集，每集8-10分钟\n\n")
        
        f.write("#### 节奏控制\n")
        f.write("- **前3集**: 建立主角困境，引发观众共鸣\n")
        f.write("- **4-80%**: 快速打脸升级，爽点密集轰炸\n")
        f.write("- **最后20%**: 终极反转，大型团灭，登顶巅峰\n\n")
        
        f.write("### ⚡ 爽点设计公式\n\n")
        f.write("```\n")
        f.write("爽度 = 打脸频率 × 反差强度 × 装逼系数 × 观众代入感\n")
        f.write("```\n\n")
        f.write("- **打脸频率**: 每5分钟至少1次打脸\n")
        f.write("- **反差强度**: 从被看不起到众人跪舔，反差越大越爽\n")
        f.write("- **装逼系数**: 主角要够狂，台词要够燃\n")
        f.write("- **代入感**: 让观众觉得\"如果是我，我也能这样\"\n\n")
        
        f.write("### 🚫 避免的题材\n\n")
        f.write("- **慢热文**: AI短剧需要快节奏，前10集见不到爽点的不适合\n")
        f.write("- **复杂政治**: 人物关系太复杂，AI难以表现\n")
        f.write("- **纯日常**: 缺乏冲突和高潮，不适合爽剧\n")
        f.write("- **纯虐文**: 观众不买账，AI爽剧要爽不要虐\n\n")
        
        f.write("---\n\n")
        
        # 5. 数据洞察
        f.write("## 📊 五、数据洞察\n\n")
        
        f.write(f"### 最适合AI爽剧的类型 TOP 5\n\n")
        top5_genres = sorted_genres[:5]
        for idx, (genre, stats) in enumerate(top5_genres, 1):
            f.write(f"{idx}. **{genre}** (AI评分: {stats['avg_ai_score']:.1f}分)\n")
            f.write(f"   - 小说数量: {stats['count']}\n")
            f.write(f"   - 平均读者: {stats['avg_readers']:.1f}万\n")
            f.write(f"   - 适配等级: {stats['ai_fit_level']}\n\n")
        
        # 统计各等级数量
        s_count = len([n for n in all_novels if n['ai_fit_level'] == 'S'])
        a_count = len([n for n in all_novels if n['ai_fit_level'] == 'A'])
        b_count = len([n for n in all_novels if n['ai_fit_level'] == 'B'])
        c_count = len([n for n in all_novels if n['ai_fit_level'] == 'C'])
        
        f.write(f"### AI适配度分布\n\n")
        f.write(f"- S级（顶级）: {s_count}部 ({s_count/len(all_novels)*100:.1f}%)\n")
        f.write(f"- A级（优质）: {a_count}部 ({a_count/len(all_novels)*100:.1f}%)\n")
        f.write(f"- B级（一般）: {b_count}部 ({b_count/len(all_novels)*100:.1f}%)\n")
        f.write(f"- C级（较低）: {c_count}部 ({c_count/len(all_novels)*100:.1f}%)\n\n")
        
        f.write(f"**结论**: {s_count + a_count}部小说（{(s_count + a_count)/len(all_novels)*100:.1f}%）非常适合AI爽剧改编！\n\n")
    
    print(f"✅ AI爽剧分析报告已生成: {report_file}")
    return report_file


def get_ai_fit_reason(genre, level):
    """获取AI适配度理由"""
    reasons = {
        'S': {
            '战神赘婿': '装逼打脸极致，爽点爆炸',
            '都市脑洞': '创意无限，节奏超快',
            '都市高武': '战斗场面AI易实现',
            '系统': '金手指明显，升级爽',
        },
        'A': {
            '豪门': '打脸剧情丰富',
            '总裁': '霸总文经典套路',
            '快穿': '多世界节奏快',
            '修真': '升级体系完整',
            '悬疑': '反转密集刺激',
        }
    }
    
    for key, value in reasons.get(level, {}).items():
        if key in genre:
            return value
    
    if level == 'S':
        return '爽点极密集'
    elif level == 'A':
        return '节奏快爽点多'
    elif level == 'B':
        return '有改编价值'
    else:
        return '需要改编调整'


def get_novel_tags(novel):
    """获取小说标签"""
    tags = []
    title = novel['title']
    genre = novel['genre']
    
    # 爽文元素标签
    if any(kw in title for kw in ['系统', '签到', '开局']):
        tags.append('系统流')
    if any(kw in title for kw in ['重生', '回到', '重返']):
        tags.append('重生')
    if any(kw in title for kw in ['赘婿', '战神', '龙王']):
        tags.append('装逼打脸')
    if any(kw in title for kw in ['逆袭', '崛起', '登顶']):
        tags.append('逆袭')
    if '快穿' in genre:
        tags.append('多世界')
    
    # 热度标签
    if novel['readers_num'] >= 100:
        tags.append('超高人气')
    elif novel['readers_num'] >= 50:
        tags.append('高人气')
    
    # 状态标签
    if novel['status'] == '已完结':
        tags.append('完结')
    
    if not tags:
        tags.append('值得改编')
    
    return '、'.join(tags[:3])  # 最多3个标签


def analyze_shuang_points(novel):
    """分析爽点"""
    title = novel['title']
    analysis = []
    
    if any(kw in title for kw in ['系统', '签到']):
        analysis.append('金手指明显')
    if any(kw in title for kw in ['打脸', '装逼', '震惊', '跪']):
        analysis.append('打脸情节多')
    if any(kw in title for kw in ['赘婿', '战神', '龙王', '隐藏']):
        analysis.append('身份反差大')
    if any(kw in title for kw in ['逆袭', '崛起', '无敌']):
        analysis.append('升级爽快')
    
    if not analysis:
        analysis.append('经典爽文')
    
    return '、'.join(analysis[:2])


def main():
    print("\n" + "="*80)
    print("🎬 番茄小说 AI爽剧改编分析系统")
    print("="*80 + "\n")
    
    # 解码并分析
    all_novels, genre_stats = decode_and_analyze()
    
    # 生成报告
    report_file = generate_ai_drama_report(all_novels, genre_stats)
    
    # 打印简要统计
    print("\n" + "="*80)
    print("📈 AI爽剧适配度 TOP 10 类型")
    print("="*80 + "\n")
    
    sorted_genres = sorted(genre_stats.items(), 
                          key=lambda x: x[1]['avg_ai_score'] if x[1]['count'] > 0 else 0, 
                          reverse=True)
    
    for idx, (genre, stats) in enumerate(sorted_genres[:10], 1):
        avg_score = stats['avg_ai_score'] if stats['count'] > 0 else 0
        fit_icon = {'S': '🔥🔥🔥🔥', 'A': '🔥🔥🔥', 'B': '🔥🔥', 'C': '🔥'}[stats['ai_fit_level']]
        print(f"{idx:2d}. {genre:15s} | {stats['gender']:4s} | 等级:{stats['ai_fit_level']} {fit_icon} | AI评分:{avg_score:5.1f}分 | 读者:{stats['avg_readers']:6.1f}万")
    
    print("\n" + "="*80)
    print("🏆 AI爽剧改编推荐 TOP 20")
    print("="*80 + "\n")
    
    top_novels = sorted(all_novels, key=lambda x: x['ai_score'], reverse=True)[:20]
    
    for idx, novel in enumerate(top_novels, 1):
        print(f"{idx:2d}. {novel['title']:30s} | {novel['genre']:10s} | AI评分:{novel['ai_score']:3.0f}分 | {novel['readers']:8s}")
    
    print("\n" + "="*80)
    print(f"✅ 完整报告请查看: {report_file}")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
