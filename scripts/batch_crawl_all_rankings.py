#!/usr/bin/env python3
"""
批量爬取所有番茄小说榜单

使用方法:
    python3 scripts/batch_crawl_all_rankings.py
    
功能:
    - 自动遍历所有37个榜单
    - 使用Playwright MCP提取数据
    - 保存为JSON文件
    - 生成统计报告
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.config import config

# JavaScript提取脚本（通用模板）
EXTRACT_JS_TEMPLATE = """() => {
  const novels = [];
  const processedUrls = new Set();
  
  const novelLinks = document.querySelectorAll('a[href*="/page/7"]');
  
  novelLinks.forEach((link) => {
    try {
      const url = link.href;
      if (processedUrls.has(url)) return;
      processedUrls.add(url);
      
      const title = link.textContent.trim();
      if (!title || title.length < 2) return;
      
      let container = link;
      for (let i = 0; i < 10; i++) {
        container = container.parentElement;
        if (!container) break;
        
        const hasAuthor = container.querySelector('a[href*="/author-page/"]');
        const hasImage = container.querySelector('img');
        if (hasAuthor || hasImage) break;
      }
      
      if (!container) return;
      
      const authorLink = container.querySelector('a[href*="/author-page/"]');
      const author = authorLink ? authorLink.textContent.trim() : '';
      
      const rankElem = container.querySelector('h1');
      let rank = novels.length + 1;
      if (rankElem) {
        const rankText = rankElem.textContent.trim();
        const rankMatch = rankText.match(/\\d+/);
        if (rankMatch) rank = parseInt(rankMatch[0]);
      }
      
      const allText = container.textContent;
      
      let status = '';
      if (allText.includes('已完结')) status = '已完结';
      else if (allText.includes('连载中')) status = '连载中';
      
      const readersMatch = allText.match(/在读[：:]\\s*([\\d.]+万?)/);
      const readers = readersMatch ? readersMatch[1] : '';
      
      const chapterMatch = allText.match(/最近更新[：:]\\s*([^\\n]+)/);
      const latestChapter = chapterMatch ? chapterMatch[1].substring(0, 50) : '';
      
      const dateMatch = allText.match(/(\\d{4}-\\d{2}-\\d{2}\\s+\\d{2}:\\d{2})/);
      const lastUpdated = dateMatch ? dateMatch[1] : '';
      
      novels.push({
        rank: rank,
        title: title,
        author: author,
        url: url,
        status: status,
        readers: readers,
        latest_chapter: latestChapter,
        last_updated: lastUpdated
      });
      
    } catch (e) {
      console.error('处理失败:', e);
    }
  });
  
  novels.sort((a, b) => a.rank - b.rank);
  
  return {
    success: true,
    ranking_name: 'RANKING_NAME',
    category: 'CATEGORY',
    url: window.location.href,
    total: novels.length,
    novels: novels
  };
}"""

def main():
    """主函数"""
    print("=" * 80)
    print("🚀 开始批量爬取所有番茄小说榜单")
    print("=" * 80)
    
    rankings = config.fanqie.rankings
    output_dir = Path("data/fanqie/rankings")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n📊 总榜单数: {len(rankings)}")
    print(f"💾 输出目录: {output_dir}")
    
    # 读取已爬取的榜单
    crawled_rankings = set()
    for json_file in output_dir.glob("*.json"):
        if "_test" in json_file.name or "_202" in json_file.name:
            continue
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if 'ranking_name' in data:
                    crawled_rankings.add(data['ranking_name'])
        except:
            pass
    
    print(f"✅ 已爬取: {len(crawled_rankings)} 个榜单")
    print(f"⏳ 剩余: {len(rankings) - len(crawled_rankings)} 个榜单")
    
    # 准备待爬取列表
    todo_rankings = []
    for name, info in rankings.items():
        if name not in crawled_rankings:
            todo_rankings.append((name, info))
    
    if not todo_rankings:
        print("\n✨ 所有榜单已爬取完成！")
        return
    
    print(f"\n📝 待爬取榜单:")
    for i, (name, _) in enumerate(todo_rankings[:10], 1):
        print(f"  {i:2d}. {name}")
    if len(todo_rankings) > 10:
        print(f"  ... 还有 {len(todo_rankings) - 10} 个榜单")
    
    print("\n" + "=" * 80)
    print("⚠️  注意: 此脚本需要手动配合Playwright MCP工具使用")
    print("=" * 80)
    print("\n请按以下步骤操作:")
    print("  1. 确保Playwright浏览器已启动")
    print("  2. 使用mcp_playwright_browser_navigate导航到每个榜单URL")
    print("  3. 使用mcp_playwright_browser_evaluate执行提取脚本")
    print("  4. 将返回的JSON数据保存到对应文件")
    
    print("\n待爬取榜单URL列表:")
    print("-" * 80)
    
    ranking_urls = []
    for name, info in todo_rankings:
        ranking_urls.append({
            "name": name,
            "url": info['url'],
            "category": info['category'],
            "output_file": f"data/fanqie/rankings/{name}.json"
        })
    
    # 保存待爬取清单
    urls_file = output_dir / "todo_rankings.json"
    with open(urls_file, 'w', encoding='utf-8') as f:
        json.dump(ranking_urls, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 待爬取清单已保存: {urls_file}")
    print(f"\n总计 {len(ranking_urls)} 个榜单待爬取")
    
    # 输出前5个示例
    print("\n示例（前5个）:")
    for i, item in enumerate(ranking_urls[:5], 1):
        print(f"\n{i}. {item['name']}")
        print(f"   URL: {item['url']}")
        print(f"   类别: {'男频' if item['category'] == 'male' else '女频'}")
        print(f"   保存: {item['output_file']}")

if __name__ == "__main__":
    main()
