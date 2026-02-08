#!/usr/bin/env python3
"""
批量爬取女频新书榜的脚本
使用Playwright MCP工具进行自动化爬取
"""

import json
from pathlib import Path
from datetime import datetime

# 女频新书榜的18个子分类
FEMALE_NEW_BOOK_RANKINGS = [
    ("女频新书榜-古风世情", "https://fanqienovel.com/rank/0_1_1139?enter_from=menu"),
    ("女频新书榜-科幻末世", "https://fanqienovel.com/rank/0_1_8?enter_from=menu"),
    ("女频新书榜-游戏体育", "https://fanqienovel.com/rank/0_1_746?enter_from=menu"),
    ("女频新书榜-女频衍生", "https://fanqienovel.com/rank/0_1_1015?enter_from=menu"),
    ("女频新书榜-玄幻言情", "https://fanqienovel.com/rank/0_1_248?enter_from=menu"),
    ("女频新书榜-种田", "https://fanqienovel.com/rank/0_1_23?enter_from=menu"),
    ("女频新书榜-年代", "https://fanqienovel.com/rank/0_1_79?enter_from=menu"),
    ("女频新书榜-现言脑洞", "https://fanqienovel.com/rank/0_1_267?enter_from=menu"),
    ("女频新书榜-宫斗宅斗", "https://fanqienovel.com/rank/0_1_246?enter_from=menu"),
    ("女频新书榜-悬疑脑洞", "https://fanqienovel.com/rank/0_1_539?enter_from=menu"),
    ("女频新书榜-古言脑洞", "https://fanqienovel.com/rank/0_1_253?enter_from=menu"),
    ("女频新书榜-快穿", "https://fanqienovel.com/rank/0_1_24?enter_from=menu"),
    ("女频新书榜-青春甜宠", "https://fanqienovel.com/rank/0_1_749?enter_from=menu"),
    ("女频新书榜-星光璀璨", "https://fanqienovel.com/rank/0_1_745?enter_from=menu"),
    ("女频新书榜-女频悬疑", "https://fanqienovel.com/rank/0_1_747?enter_from=menu"),
    ("女频新书榜-职场婚恋", "https://fanqienovel.com/rank/0_1_750?enter_from=menu"),
    ("女频新书榜-豪门总裁", "https://fanqienovel.com/rank/0_1_748?enter_from=menu"),
    ("女频新书榜-民国言情", "https://fanqienovel.com/rank/0_1_1017?enter_from=menu"),
]

# JavaScript提取脚本
EXTRACT_JS = """
() => {
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
    category: 'female_new',
    url: window.location.href,
    crawled_at: new Date().toISOString(),
    total: novels.length,
    novels: novels
  };
}
"""

def main():
    """主函数：打印爬取指令"""
    print("=" * 70)
    print("女频新书榜批量爬取脚本")
    print("=" * 70)
    print(f"\n总计需要爬取：{len(FEMALE_NEW_BOOK_RANKINGS)} 个榜单\n")
    
    for i, (name, url) in enumerate(FEMALE_NEW_BOOK_RANKINGS, 1):
        print(f"\n{'='*70}")
        print(f"【{i}/18】 {name}")
        print(f"{'='*70}")
        print(f"URL: {url}")
        print("\n📋 手动执行步骤：")
        print(f"1. browser_navigate: {url}")
        print(f"2. browser_evaluate: 执行提取脚本（替换 RANKING_NAME 为 '{name}'）")
        print(f"3. 保存数据到: data/fanqie/rankings/{name}.json")
        print()

if __name__ == "__main__":
    main()
