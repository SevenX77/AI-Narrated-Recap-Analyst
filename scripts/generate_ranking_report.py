#!/usr/bin/env python3
"""
生成番茄小说榜单统计报告

功能:
    - 分析所有已爬取的榜单
    - 统计阅读人数
    - 对比不同类别的热度
    - 生成Markdown格式报告
"""

import json
from pathlib import Path
from datetime import datetime

def parse_readers(readers_str):
    """解析阅读人数字符串，转换为数字（万为单位）"""
    if not readers_str:
        return 0.0
    readers_str = readers_str.replace('万', '')
    try:
        return float(readers_str)
    except:
        return 0.0

def main():
    """主函数"""
    ranking_dir = Path("data/fanqie/rankings")
    rankings = []
    
    # 读取所有已爬取的榜单
    for json_file in ranking_dir.glob("*.json"):
        if "_test" in json_file.name or "_202" in json_file.name or "todo" in json_file.name:
            continue
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if 'ranking_name' in data and 'novels' in data:
                    rankings.append(data)
        except Exception as e:
            print(f"⚠️  读取文件失败: {json_file.name} - {e}")
    
    if not rankings:
        print("❌ 没有找到已爬取的榜单数据")
        return
    
    print("=" * 80)
    print("📊 番茄小说榜单统计报告")
    print("=" * 80)
    print(f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"已爬取榜单数: {len(rankings)}")
    
    # 分类统计
    male_rankings = [r for r in rankings if r['category'] == 'male']
    female_rankings = [r for r in rankings if r['category'] == 'female']
    
    print(f"  - 男频: {len(male_rankings)} 个")
    print(f"  - 女频: {len(female_rankings)} 个")
    
    # 统计每个榜单的数据
    ranking_stats = []
    all_novels = []
    
    for ranking in rankings:
        novels = ranking.get('novels', [])
        total_readers = sum(parse_readers(n.get('readers', '0')) for n in novels)
        avg_readers = total_readers / len(novels) if novels else 0
        
        # 统计状态
        finished_count = sum(1 for n in novels if n.get('status') == '已完结')
        ongoing_count = sum(1 for n in novels if n.get('status') == '连载中')
        
        ranking_stats.append({
            'name': ranking['ranking_name'],
            'category': ranking['category'],
            'url': ranking['url'],
            'total_novels': len(novels),
            'total_readers': total_readers,
            'avg_readers': avg_readers,
            'finished': finished_count,
            'ongoing': ongoing_count
        })
        
        # 收集所有小说
        for novel in novels:
            all_novels.append({
                'title': novel.get('title', ''),
                'author': novel.get('author', ''),
                'readers': parse_readers(novel.get('readers', '0')),
                'status': novel.get('status', ''),
                'ranking': ranking['ranking_name'],
                'category': ranking['category']
            })
    
    # 按总阅读数排序
    ranking_stats.sort(key=lambda x: x['total_readers'], reverse=True)
    
    # 打印报告
    print("\n" + "=" * 80)
    print("🏆 榜单热度排名 (按总阅读数)")
    print("=" * 80)
    
    for i, stat in enumerate(ranking_stats, 1):
        cat_emoji = "👨" if stat['category'] == 'male' else "👩"
        print(f"\n{i:2d}. {cat_emoji} {stat['name']}")
        print(f"    📊 总阅读量: {stat['total_readers']:.1f}万")
        print(f"    📈 平均阅读: {stat['avg_readers']:.1f}万/本")
        print(f"    📚 小说数量: {stat['total_novels']}本")
        print(f"    📖 连载: {stat['ongoing']}本 | 完结: {stat['finished']}本")
    
    # 全局TOP小说
    all_novels.sort(key=lambda x: x['readers'], reverse=True)
    
    print("\n" + "=" * 80)
    print("🌟 全站TOP 10最热小说")
    print("=" * 80)
    
    for i, novel in enumerate(all_novels[:10], 1):
        cat = '男频' if novel['category'] == 'male' else '女频'
        status_emoji = "✅" if novel['status'] == '已完结' else "📖"
        print(f"\n{i:2d}. {status_emoji} {novel['title']}")
        print(f"    👤 作者: {novel['author'] or '未知'}")
        print(f"    📊 阅读: {novel['readers']:.1f}万")
        print(f"    📚 榜单: {novel['ranking']} ({cat})")
    
    # 男女频对比
    male_total = sum(s['total_readers'] for s in ranking_stats if s['category'] == 'male')
    female_total = sum(s['total_readers'] for s in ranking_stats if s['category'] == 'female')
    
    print("\n" + "=" * 80)
    print("⚖️  男频 vs 女频对比")
    print("=" * 80)
    print(f"\n👨 男频:")
    print(f"   榜单数: {len(male_rankings)}")
    print(f"   总阅读: {male_total:.1f}万")
    print(f"   平均每榜: {male_total/len(male_rankings) if male_rankings else 0:.1f}万")
    
    print(f"\n👩 女频:")
    print(f"   榜单数: {len(female_rankings)}")
    print(f"   总阅读: {female_total:.1f}万")
    print(f"   平均每榜: {female_total/len(female_rankings) if female_rankings else 0:.1f}万")
    
    # 保存报告
    report_dir = Path("data/fanqie")
    report_file = report_dir / f"ranking_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(f"# 番茄小说榜单统计报告\n\n")
        f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"## 📊 数据概览\n\n")
        f.write(f"- **已爬取榜单**: {len(rankings)} 个\n")
        f.write(f"- **男频榜单**: {len(male_rankings)} 个\n")
        f.write(f"- **女频榜单**: {len(female_rankings)} 个\n\n")
        
        f.write(f"## 🏆 榜单热度排名\n\n")
        f.write("| 排名 | 榜单名称 | 类别 | 总阅读量(万) | 平均阅读(万) | 小说数 |\n")
        f.write("|------|----------|------|-------------|-------------|-------|\n")
        for i, stat in enumerate(ranking_stats, 1):
            cat = '男频' if stat['category'] == 'male' else '女频'
            f.write(f"| {i} | {stat['name']} | {cat} | {stat['total_readers']:.1f} | {stat['avg_readers']:.1f} | {stat['total_novels']} |\n")
        
        f.write(f"\n## 🌟 全站TOP 10最热小说\n\n")
        f.write("| 排名 | 书名 | 作者 | 阅读量(万) | 状态 | 榜单 |\n")
        f.write("|------|------|------|-----------|------|------|\n")
        for i, novel in enumerate(all_novels[:10], 1):
            status = '已完结' if novel['status'] == '已完结' else '连载中'
            f.write(f"| {i} | {novel['title']} | {novel['author']} | {novel['readers']:.1f} | {status} | {novel['ranking']} |\n")
    
    print(f"\n✅ 报告已保存: {report_file}")
    
    # 输出建议
    print("\n" + "=" * 80)
    print("💡 下载建议")
    print("=" * 80)
    
    # 找出前5个最热门的榜单
    top_5_rankings = ranking_stats[:5]
    print("\n基于阅读量数据，建议优先下载以下榜单的小说：\n")
    for i, stat in enumerate(top_5_rankings, 1):
        print(f"{i}. {stat['name']} (总阅读: {stat['total_readers']:.1f}万)")
    
    print("\n这些榜单的小说具有更高的热度和关注度，适合优先分析。")

if __name__ == "__main__":
    main()
