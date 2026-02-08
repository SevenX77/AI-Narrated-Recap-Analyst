"""
批量爬取番茄小说所有榜单
使用 Playwright MCP 访问每个榜单并提取数据
"""
import json
import logging
from datetime import datetime
from pathlib import Path
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.config import config

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# JavaScript 提取函数（已验证可用）
EXTRACT_JS = """
() => {
  const novels = [];
  const processedUrls = new Set();
  
  // 找所有小说链接
  const novelLinks = document.querySelectorAll('a[href*="/page/7"]');
  
  novelLinks.forEach((link) => {
    try {
      const url = link.href;
      if (processedUrls.has(url)) return;
      processedUrls.add(url);
      
      const title = link.textContent.trim();
      if (!title || title.length < 2) return;
      
      // 向上查找足够大的容器（包含完整信息）
      let container = link;
      for (let i = 0; i < 10; i++) {
        container = container.parentElement;
        if (!container) break;
        
        // 检查容器是否包含作者链接
        const hasAuthor = container.querySelector('a[href*="/author-page/"]');
        const hasImage = container.querySelector('img');
        if (hasAuthor || hasImage) break;
      }
      
      if (!container) return;
      
      // 提取作者
      const authorLink = container.querySelector('a[href*="/author-page/"]');
      const author = authorLink ? authorLink.textContent.trim() : '';
      
      // 提取排名
      const rankElem = container.querySelector('h1');
      let rank = novels.length + 1;
      if (rankElem) {
        const rankText = rankElem.textContent.trim();
        const rankMatch = rankText.match(/\\d+/);
        if (rankMatch) rank = parseInt(rankMatch[0]);
      }
      
      // 提取封面
      const img = container.querySelector('img');
      const cover = img ? img.alt || '' : '';
      
      // 提取所有文本信息
      const allText = container.textContent;
      
      // 提取状态
      let status = '';
      if (allText.includes('已完结')) status = '已完结';
      else if (allText.includes('连载中')) status = '连载中';
      
      // 提取阅读数
      const readersMatch = allText.match(/在读[：:]\\s*([\\d.]+万?)/);
      const readers = readersMatch ? readersMatch[1] : '';
      
      // 提取最新章节
      const chapterMatch = allText.match(/最近更新[：:]\\s*([^\\n]+)/);
      const latestChapter = chapterMatch ? chapterMatch[1].substring(0, 50) : '';
      
      novels.push({
        rank: rank,
        title: title,
        author: author,
        url: url,
        cover: cover,
        status: status,
        readers: readers,
        latestChapter: latestChapter
      });
      
    } catch (e) {
      console.error('处理失败:', e);
    }
  });
  
  // 按排名排序
  novels.sort((a, b) => a.rank - b.rank);
  
  return {
    success: true,
    total: novels.length,
    novels: novels.slice(0, 10),
    pageTitle: document.title,
    pageUrl: window.location.href
  };
}
"""


def main():
    """主函数"""
    logger.info("=" * 80)
    logger.info("🚀 开始批量爬取番茄小说榜单")
    logger.info("=" * 80)
    
    # 获取所有榜单配置
    rankings = config.fanqie.rankings
    logger.info(f"\n📊 共有 {len(rankings)} 个榜单待爬取")
    
    # 统计
    male_rankings = [name for name, info in rankings.items() if info.get('category') == 'male']
    female_rankings = [name for name, info in rankings.items() if info.get('category') == 'female']
    
    logger.info(f"   - 男频榜单: {len(male_rankings)} 个")
    logger.info(f"   - 女频榜单: {len(female_rankings)} 个")
    
    # 创建输出目录
    output_dir = Path(config.data_dir) / "fanqie" / "rankings"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"\n💾 输出目录: {output_dir}")
    logger.info("\n" + "=" * 80)
    logger.info("⚠️  注意：")
    logger.info("   此脚本需要在 Playwright MCP 浏览器打开的情况下运行")
    logger.info("   请确保已经通过 Cursor 的 MCP 功能打开了浏览器")
    logger.info("   实际爬取需要集成 Playwright MCP 工具调用")
    logger.info("=" * 80)
    
    # 显示榜单列表
    logger.info("\n📋 榜单列表：")
    logger.info("\n【男频榜单】")
    for idx, name in enumerate(male_rankings[:5], 1):
        url = rankings[name]['url']
        logger.info(f"   {idx}. {name}")
        logger.info(f"      {url}")
    if len(male_rankings) > 5:
        logger.info(f"   ... 还有 {len(male_rankings) - 5} 个男频榜单")
    
    logger.info("\n【女频榜单】")
    for idx, name in enumerate(female_rankings[:5], 1):
        url = rankings[name]['url']
        logger.info(f"   {idx}. {name}")
        logger.info(f"      {url}")
    if len(female_rankings) > 5:
        logger.info(f"   ... 还有 {len(female_rankings) - 5} 个女频榜单")
    
    logger.info("\n" + "=" * 80)
    logger.info("✅ 配置检查完成")
    logger.info("=" * 80)
    logger.info("\n📝 提取脚本已准备就绪（JavaScript）：")
    logger.info(f"   - 脚本长度: {len(EXTRACT_JS)} 字符")
    logger.info("   - 功能: 提取榜单中的小说标题、作者、URL、状态、阅读数等")
    
    logger.info("\n" + "=" * 80)
    logger.info("🎯 下一步操作：")
    logger.info("=" * 80)
    logger.info("1. 在 Cursor 中打开 Playwright MCP 浏览器")
    logger.info("2. 使用 mcp_playwright_browser_navigate 访问每个榜单 URL")
    logger.info("3. 使用 mcp_playwright_browser_evaluate 执行上述 JS 提取数据")
    logger.info("4. 保存每个榜单的数据到 JSON 文件")
    logger.info("5. 汇总所有榜单数据并去重")
    logger.info("6. 生成下载队列")
    
    logger.info("\n✨ 脚本准备完毕！")


if __name__ == "__main__":
    main()
