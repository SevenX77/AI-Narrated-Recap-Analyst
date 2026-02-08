#!/usr/bin/env python3
"""
番茄小说榜单数据分析 - 热度分析与影视化改编潜力评估
"""

import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime
import re


def parse_readers(readers_str):
    """解析读者数字符串为数值（单位：万）"""
    if not readers_str:
        return 0.0
    
    # 移除可能的空格
    readers_str = readers_str.strip()
    
    # 处理"万"单位
    if '万' in readers_str:
        num = readers_str.replace('万', '')
        try:
            return float(num)
        except:
            return 0.0
    
    # 纯数字（小于1万的情况）
    try:
        return float(readers_str) / 10000
    except:
        return 0.0


def categorize_genre(ranking_name):
    """根据榜单名称分类小说类型"""
    # 定义影视化改编适合度的关键词
    high_adaptation_keywords = ['都市', '现代', '古风', '宫斗', '宅斗', '豪门', '总裁', '婚恋', '职场', '民国', '年代', '悬疑', '快穿']
    medium_adaptation_keywords = ['玄幻', '修真', '仙侠', '武侠', '历史', '军事', '抗战', '种田', '重生', '穿越']
    low_adaptation_keywords = ['游戏', '科幻', '末世', '体育', '无限流', '系统', '衍生']
    
    # 提取榜单类型
    if '男频' in ranking_name:
        gender = '男频'
    elif '女频' in ranking_name:
        gender = '女频'
    else:
        gender = '未知'
    
    # 判断是否新书榜
    is_new = '新书榜' in ranking_name
    
    # 提取具体类型（去除"男频-"、"女频-"、"新书榜-"等前缀）
    genre = ranking_name.split('-')[-1] if '-' in ranking_name else ranking_name
    
    # 评估影视化改编潜力
    adaptation_potential = 'low'
    for keyword in high_adaptation_keywords:
        if keyword in genre:
            adaptation_potential = 'high'
            break
    
    if adaptation_potential == 'low':
        for keyword in medium_adaptation_keywords:
            if keyword in genre:
                adaptation_potential = 'medium'
                break
    
    return {
        'gender': gender,
        'is_new': is_new,
        'genre': genre,
        'adaptation_potential': adaptation_potential
    }


def analyze_rankings():
    """分析所有榜单数据"""
    rankings_dir = Path("data/fanqie/rankings")
    
    # 数据收集
    all_novels = []
    genre_stats = defaultdict(lambda: {
        'count': 0,
        'total_readers': 0,
        'novels': [],
        'adaptation_potential': 'low',
        'gender': '',
        'is_new': False
    })
    
    # 读取所有榜单（排除测试文件和配置文件）
    ranking_files = [f for f in rankings_dir.glob("*.json") 
                     if "_test" not in f.name 
                     and f.name not in ['todo_rankings.json', 'ranking_urls.json']]
    
    print(f"📊 开始分析 {len(ranking_files)} 个榜单...")
    print("=" * 80)
    
    for ranking_file in ranking_files:
        with open(ranking_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        ranking_name = data.get('ranking_name', ranking_file.stem)
        category_info = categorize_genre(ranking_name)
        
        for novel in data.get('novels', []):
            readers_num = parse_readers(novel.get('readers', '0'))
            
            novel_info = {
                'title': novel.get('title', ''),
                'author': novel.get('author', ''),
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
            
            all_novels.append(novel_info)
            
            # 按类型统计
            genre = category_info['genre']
            genre_stats[genre]['count'] += 1
            genre_stats[genre]['total_readers'] += readers_num
            genre_stats[genre]['novels'].append(novel_info)
            genre_stats[genre]['adaptation_potential'] = category_info['adaptation_potential']
            genre_stats[genre]['gender'] = category_info['gender']
            genre_stats[genre]['is_new'] = category_info['is_new']
    
    return all_novels, genre_stats


def generate_report(all_novels, genre_stats):
    """生成分析报告"""
    output_dir = Path("data/fanqie")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = output_dir / f"adaptation_analysis_{timestamp}.md"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# 番茄小说榜单数据分析报告\n\n")
        f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**数据来源**: 72个番茄小说榜单\n\n")
        f.write("---\n\n")
        
        # 1. 热度排行 - 按类型
        f.write("## 📊 一、小说类型热度排行（按总读者数）\n\n")
        sorted_genres = sorted(genre_stats.items(), key=lambda x: x[1]['total_readers'], reverse=True)
        
        f.write("| 排名 | 类型 | 性别分类 | 小说数 | 总读者数 | 平均读者数 | 影视化潜力 |\n")
        f.write("|------|------|----------|--------|----------|------------|------------|\n")
        
        for idx, (genre, stats) in enumerate(sorted_genres, 1):
            avg_readers = stats['total_readers'] / stats['count'] if stats['count'] > 0 else 0
            potential_icon = {'high': '🔥🔥🔥', 'medium': '🔥🔥', 'low': '🔥'}[stats['adaptation_potential']]
            f.write(f"| {idx} | {genre} | {stats['gender']} | {stats['count']} | {stats['total_readers']:.1f}万 | {avg_readers:.1f}万 | {potential_icon} |\n")
        
        f.write("\n---\n\n")
        
        # 2. 影视化改编潜力分析
        f.write("## 🎬 二、影视化改编潜力分析\n\n")
        
        # 高潜力类型
        f.write("### 🔥🔥🔥 高潜力类型（适合影视化改编）\n\n")
        high_potential = [(g, s) for g, s in sorted_genres if s['adaptation_potential'] == 'high']
        
        f.write("**特点**: 现实题材、情感主线明确、场景易于拍摄、观众基础广泛\n\n")
        f.write("| 类型 | 性别分类 | 总读者数 | 平均读者数 | 推荐理由 |\n")
        f.write("|------|----------|----------|------------|----------|\n")
        
        for genre, stats in high_potential[:10]:  # 前10个高潜力类型
            avg_readers = stats['total_readers'] / stats['count'] if stats['count'] > 0 else 0
            reason = get_adaptation_reason(genre)
            f.write(f"| {genre} | {stats['gender']} | {stats['total_readers']:.1f}万 | {avg_readers:.1f}万 | {reason} |\n")
        
        f.write("\n")
        
        # 中等潜力类型
        f.write("### 🔥🔥 中等潜力类型（需要特效支持）\n\n")
        medium_potential = [(g, s) for g, s in sorted_genres if s['adaptation_potential'] == 'medium']
        
        f.write("**特点**: 需要特效、服化道投入较大、但有成功案例\n\n")
        f.write("| 类型 | 性别分类 | 总读者数 | 平均读者数 |\n")
        f.write("|------|----------|----------|------------|\n")
        
        for genre, stats in medium_potential[:10]:
            avg_readers = stats['total_readers'] / stats['count'] if stats['count'] > 0 else 0
            f.write(f"| {genre} | {stats['gender']} | {stats['total_readers']:.1f}万 | {avg_readers:.1f}万 |\n")
        
        f.write("\n---\n\n")
        
        # 3. 最热门小说TOP50
        f.write("## 🏆 三、最热门小说 TOP 50\n\n")
        top_novels = sorted(all_novels, key=lambda x: x['readers_num'], reverse=True)[:50]
        
        f.write("| 排名 | 书名 | 作者 | 类型 | 性别分类 | 读者数 | 状态 | 影视化潜力 |\n")
        f.write("|------|------|------|------|----------|--------|------|------------|\n")
        
        for idx, novel in enumerate(top_novels, 1):
            potential_icon = {'high': '🔥🔥🔥', 'medium': '🔥🔥', 'low': '🔥'}[novel['adaptation_potential']]
            f.write(f"| {idx} | {novel['title']} | {novel['author']} | {novel['genre']} | {novel['gender']} | {novel['readers']} | {novel['status']} | {potential_icon} |\n")
        
        f.write("\n---\n\n")
        
        # 4. 影视化改编推荐榜（高潜力 + 高热度）
        f.write("## 🎯 四、影视化改编推荐榜 TOP 30\n\n")
        f.write("**筛选标准**: 影视化潜力高 + 读者数高 + 已完结或更新稳定\n\n")
        
        adaptation_novels = [n for n in all_novels if n['adaptation_potential'] == 'high']
        adaptation_novels = sorted(adaptation_novels, key=lambda x: x['readers_num'], reverse=True)[:30]
        
        f.write("| 排名 | 书名 | 作者 | 类型 | 读者数 | 状态 | 最近更新 | 推荐理由 |\n")
        f.write("|------|------|------|------|--------|------|----------|----------|\n")
        
        for idx, novel in enumerate(adaptation_novels, 1):
            reason = get_novel_adaptation_reason(novel)
            f.write(f"| {idx} | {novel['title']} | {novel['author']} | {novel['genre']} | {novel['readers']} | {novel['status']} | {novel['last_updated']} | {reason} |\n")
        
        f.write("\n---\n\n")
        
        # 5. 数据洞察
        f.write("## 💡 五、数据洞察与建议\n\n")
        
        f.write("### 热门类型趋势\n\n")
        f.write("1. **最火类型**: ")
        top3_genres = sorted_genres[:3]
        f.write(", ".join([f"{g} ({s['total_readers']:.1f}万读者)" for g, s in top3_genres]))
        f.write("\n\n")
        
        f.write("2. **男女频对比**:\n")
        male_total = sum(s['total_readers'] for g, s in sorted_genres if s['gender'] == '男频')
        female_total = sum(s['total_readers'] for g, s in sorted_genres if s['gender'] == '女频')
        f.write(f"   - 男频总读者: {male_total:.1f}万\n")
        f.write(f"   - 女频总读者: {female_total:.1f}万\n\n")
        
        f.write("3. **影视化改编潜力分布**:\n")
        high_count = len([s for g, s in sorted_genres if s['adaptation_potential'] == 'high'])
        medium_count = len([s for g, s in sorted_genres if s['adaptation_potential'] == 'medium'])
        low_count = len([s for g, s in sorted_genres if s['adaptation_potential'] == 'low'])
        f.write(f"   - 高潜力类型: {high_count}个\n")
        f.write(f"   - 中等潜力类型: {medium_count}个\n")
        f.write(f"   - 低潜力类型: {low_count}个\n\n")
        
        f.write("### 影视化改编建议\n\n")
        f.write("1. **首选题材**: 都市、现代、豪门、婚恋、职场类小说\n")
        f.write("   - 制作成本相对较低\n")
        f.write("   - 观众共鸣度高\n")
        f.write("   - 场景易于实现\n\n")
        
        f.write("2. **古装题材**: 古风、宫斗、宅斗、民国类\n")
        f.write("   - 需要较大服化道投入\n")
        f.write("   - 但市场成熟，有成功案例\n")
        f.write("   - 适合制作精良的大剧\n\n")
        
        f.write("3. **悬疑推理**: 悬疑、刑侦类\n")
        f.write("   - 剧情张力强\n")
        f.write("   - 适合短剧形式\n")
        f.write("   - 制作周期相对较短\n\n")
        
        f.write("4. **避免题材**: 游戏、无限流、系统流\n")
        f.write("   - 影视化难度大\n")
        f.write("   - 特效成本高\n")
        f.write("   - 观众理解门槛高\n\n")
    
    print(f"\n✅ 分析报告已生成: {report_file}")
    return report_file


def get_adaptation_reason(genre):
    """获取影视化改编推荐理由"""
    reasons = {
        '都市': '现实题材，制作成本低',
        '豪门': '观众基础广，市场成熟',
        '总裁': '言情市场热门，易短剧化',
        '婚恋': '情感共鸣强，适合都市剧',
        '职场': '现实题材，励志向',
        '古风': '服化道成熟，市场认可度高',
        '宫斗': '宫廷剧经典题材',
        '宅斗': '家族剧市场稳定',
        '民国': '民国剧有成功案例',
        '年代': '怀旧情怀，观众年龄层广',
        '悬疑': '剧情张力强，适合网剧',
        '快穿': '多元世界观，可系列化',
        '现言脑洞': '脑洞创意，适合短剧',
        '青春甜宠': '青春剧市场稳定',
        '星光璀璨': '娱乐圈题材热门'
    }
    return reasons.get(genre, '有市场潜力')


def get_novel_adaptation_reason(novel):
    """获取单本小说的影视化改编推荐理由"""
    readers_num = novel['readers_num']
    status = novel['status']
    genre = novel['genre']
    
    reasons = []
    
    if readers_num > 30:
        reasons.append("超高人气")
    elif readers_num > 10:
        reasons.append("高人气")
    
    if status == '已完结':
        reasons.append("完结，剧本完整")
    
    if '都市' in genre or '现代' in genre or '豪门' in genre:
        reasons.append("现实题材")
    elif '古风' in genre or '宫斗' in genre:
        reasons.append("古装题材")
    
    if not reasons:
        reasons.append("有改编潜力")
    
    return "、".join(reasons)


def main():
    print("\n" + "="*80)
    print("📊 番茄小说榜单数据分析 - 热度分析与影视化改编潜力评估")
    print("="*80 + "\n")
    
    # 分析数据
    all_novels, genre_stats = analyze_rankings()
    
    print(f"\n✅ 数据加载完成:")
    print(f"   - 总小说数: {len(all_novels)}")
    print(f"   - 类型数: {len(genre_stats)}")
    
    # 生成报告
    report_file = generate_report(all_novels, genre_stats)
    
    # 打印简要统计
    print("\n" + "="*80)
    print("📈 简要统计")
    print("="*80)
    
    sorted_genres = sorted(genre_stats.items(), key=lambda x: x[1]['total_readers'], reverse=True)
    
    print("\n🔥 热度TOP 10类型:")
    for idx, (genre, stats) in enumerate(sorted_genres[:10], 1):
        avg_readers = stats['total_readers'] / stats['count'] if stats['count'] > 0 else 0
        potential_icon = {'high': '🔥🔥🔥', 'medium': '🔥🔥', 'low': '🔥'}[stats['adaptation_potential']]
        print(f"{idx:2d}. {genre:12s} | {stats['gender']:4s} | 读者:{stats['total_readers']:6.1f}万 | 影视化:{potential_icon}")
    
    print("\n🎬 高影视化潜力类型:")
    high_potential = [(g, s) for g, s in sorted_genres if s['adaptation_potential'] == 'high']
    for idx, (genre, stats) in enumerate(high_potential[:10], 1):
        print(f"{idx:2d}. {genre:12s} | {stats['gender']:4s} | 读者:{stats['total_readers']:6.1f}万")
    
    print("\n" + "="*80)
    print(f"✅ 完整报告请查看: {report_file}")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
