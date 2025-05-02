#-*- coding: utf-8 -*-
# 构建ip代理池，并
# 使用ip代理池爬取数据
# 演示功能：爬取豆瓣电影top250

import requests
from bs4 import BeautifulSoup
import random
import time
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import logging
import json
import os
from datetime import datetime, timedelta

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class ProxyPool:
    """IP代理池类"""
    
    def __init__(self, proxy_file="proxy_pool.json"):
        self.proxy_pool = []
        self.proxy_apis = [
            "https://free-proxy-list.net/",
        ]
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15'
        ]
        self.proxy_file = proxy_file
        self.max_proxy_age = timedelta(hours=24)  # 代理最长有效期为24小时

    def get_random_user_agent(self):
        """获取随机User-Agent"""
        return random.choice(self.user_agents)
    
    def fetch_proxies_from_source(self, url):
        """从代理源网站获取代理IP列表"""
        proxies = []
        try:
            headers = {"User-Agent": self.get_random_user_agent()}
            response = requests.get(url, headers=headers, timeout=10)
            logger.info(f"请求代理网站: {url}，状态码: {response.status_code}")
            
            
            if response.status_code == 200:
                logger.info(f"text: {response.text}")
                soup = BeautifulSoup(response.text, 'html.parser')
                table = soup.find('table', {'class': 'table table-striped table-bordered'})
                if not table:
                    return []
                
                for tr in table.find('tbody').find_all('tr'):
                    tds = tr.find_all('td')
                    if len(tds) < 7:
                        continue
                    
                    ip = tds[0].text.strip()
                    port = tds[1].text.strip()
                    if tds[3].text.strip().lower() == 'yes':
                        protocol = 'https'
                    else:
                        protocol = 'http'
                    
                    if protocol in ['http', 'https']:
                        proxy = f"{protocol}://{ip}:{port}"
                        proxies.append(proxy)
                
                logger.info(f"从 {url} 获取了 {len(proxies)} 个代理")
            else:
                logger.warning(f"请求代理网站失败: {response.status_code}")
        
        except Exception as e:
            logger.error(f"获取代理出错: {e}")
        
        return proxies
    
    def verify_proxy(self, proxy):
        """验证代理是否可用"""
        try:
            protocol = proxy.split('://')[0]
            proxies = {protocol: proxy}
            
            test_url = "https://www.google.com"
            response = requests.get(
                test_url, 
                proxies=proxies, 
                timeout=5, 
                headers={"User-Agent": self.get_random_user_agent()}
            )
            
            if response.status_code == 200:
                logger.debug(f"代理可用: {proxy}")
                return proxy
            
        except Exception:
            logger.warning(f"代理不可用: {proxy}")
            pass
        
        return None
    
    def save_proxies(self):
        """将代理保存到文件"""
        data = {
            "timestamp": datetime.now().isoformat(),
            "proxies": self.proxy_pool
        }
        try:
            with open(self.proxy_file, 'w') as f:
                json.dump(data, f)
            logger.info(f"成功保存 {len(self.proxy_pool)} 个代理到文件")
            return True
        except Exception as e:
            logger.error(f"保存代理到文件失败: {e}")
            return False
    
    def load_proxies(self):
        """从文件加载代理"""
        if not os.path.exists(self.proxy_file):
            logger.info("代理文件不存在，将重新获取代理")
            return []
        
        try:
            with open(self.proxy_file, 'r') as f:
                data = json.load(f)
            
            saved_time = datetime.fromisoformat(data["timestamp"])
            now = datetime.now()
            
            # 检查代理是否过期
            if now - saved_time > self.max_proxy_age:
                logger.info("代理文件已过期，将重新获取代理")
                return []
            
            loaded_proxies = data["proxies"]
            logger.info(f"从文件加载了 {len(loaded_proxies)} 个代理")
            return loaded_proxies
        
        except Exception as e:
            logger.error(f"从文件加载代理失败: {e}")
            return []
    
    def build_pool(self, min_size=10, max_retries=5):
        """构建代理池"""
        # 首先尝试从文件加载代理
        self.proxy_pool = self.load_proxies()
        
        # 如果已有足够代理，则验证它们是否可用
        if len(self.proxy_pool) >= min_size:
            logger.info("验证已加载代理的可用性...")
            valid_proxies = []
            with ThreadPoolExecutor(max_workers=10) as executor:
                valid_proxies = list(filter(None, executor.map(self.verify_proxy, self.proxy_pool)))
            
            self.proxy_pool = valid_proxies
            logger.info(f"验证后剩余 {len(self.proxy_pool)} 个可用代理")
            
            # 如果验证后的代理数量仍然足够，直接返回
            if len(self.proxy_pool) >= min_size:
                return True
            else:
                logger.info("已保存代理不足或大部分已失效，将获取新代理")
        
        # 原有的获取代理逻辑
        retry_count = 0
        
        while len(self.proxy_pool) < min_size and retry_count < max_retries:
            all_proxies = []
            
            # 从各个源获取代理
            for api_url in self.proxy_apis:
                proxies = self.fetch_proxies_from_source(api_url)
                all_proxies.extend(proxies)
                # 避免请求过于频繁
                time.sleep(2)
            
            if not all_proxies:
                logger.warning("未找到代理IP，等待后重试...")
                retry_count += 1
                time.sleep(5)
                continue
            
            # 并发验证代理可用性
            with ThreadPoolExecutor(max_workers=10) as executor:
                valid_proxies = list(filter(None, executor.map(self.verify_proxy, all_proxies)))
            
            self.proxy_pool.extend(valid_proxies)
            logger.info(f"验证通过 {len(valid_proxies)} 个代理，当前代理池大小: {len(self.proxy_pool)}")
            
            if not valid_proxies:
                retry_count += 1
                time.sleep(5)
        
        # 保存获取到的代理
        if self.proxy_pool:
            self.save_proxies()
        
        if len(self.proxy_pool) >= min_size:
            logger.info(f"代理池构建成功，包含 {len(self.proxy_pool)} 个可用代理")
            return True
        else:
            logger.error(f"代理池构建失败，仅获取到 {len(self.proxy_pool)} 个代理，少于最低要求 {min_size} 个")
            return False
    
    def get_random_proxy(self):
        """随机获取一个代理"""
        if not self.proxy_pool:
            return None
        return random.choice(self.proxy_pool)
    
    def remove_proxy(self, proxy):
        """从代理池中移除失效代理"""
        if proxy in self.proxy_pool:
            self.proxy_pool.remove(proxy)
            logger.info(f"移除失效代理 {proxy}，剩余代理数: {len(self.proxy_pool)}")
            # 代理池有变动时保存
            self.save_proxies()




class DoubanCrawler:
    """豆瓣电影爬虫类"""
    
    def __init__(self, proxy_pool):
        self.proxy_pool = proxy_pool
        self.base_url = "https://movie.douban.com/top250"
        self.movies = []
    
    def fetch_page(self, page):
        """爬取单页数据"""
        start = (page - 1) * 25
        url = f"{self.base_url}?start={start}"
        
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            # 获取代理
            proxy = self.proxy_pool.get_random_proxy()
            if not proxy:
                logger.warning("无可用代理，直接连接")
                proxies = None
            else:
                protocol = proxy.split('://')[0]
                proxies = {protocol: proxy}
            
            try:
                headers = {"User-Agent": self.proxy_pool.get_random_user_agent()}
                logger.info(f"爬取页面 {page}，URL: {url}，使用代理: {proxy}")
                
                response = requests.get(url, headers=headers, proxies=proxies, timeout=10)
                
                if response.status_code == 200:
                    return self.parse_page(response.text)
                else:
                    logger.warning(f"请求失败，状态码: {response.status_code}")
                    # 移除失效代理
                    if proxy:
                        self.proxy_pool.remove_proxy(proxy)
                    
                    retry_count += 1
                    time.sleep(2)
            
            except Exception as e:
                logger.error(f"请求出错: {e}")
                # 移除失效代理
                if proxy:
                    self.proxy_pool.remove_proxy(proxy)
                
                retry_count += 1
                time.sleep(2)
        
        logger.error(f"页面 {page} 爬取失败，达到最大重试次数")
        return []
    
    def parse_page(self, html):
        """解析页面HTML提取电影信息"""
        page_movies = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # 查找所有电影条目
        items = soup.select('.grid_view li')
        logger.info(f"找到 {len(items)} 部电影条目")
        
        for item in items:
            try:
                # 排名
                rank = item.select_one('.pic em').text.strip()
                
                # 标题（主标题）
                title_elem = item.select_one('.hd a .title')
                title = title_elem.text.strip() if title_elem else ""
                
                # 原标题（如果有多个.title，第二个通常是原标题）
                title_elements = item.select('.hd a .title')
                original_title = ""
                if len(title_elements) > 1:
                    original_title = title_elements[1].text.strip().replace('&nbsp;/&nbsp;', '')
                
                # 其他名称（港台译名等）
                other_title = ""
                other_elem = item.select_one('.hd a .other')
                if other_elem:
                    other_title = other_elem.text.strip().replace('&nbsp;/&nbsp;', '')
                
                # 导演和主演信息
                info_elem = item.select_one('.bd p')
                director_actors = ""
                details = ""
                
                if info_elem:
                    info_text = info_elem.get_text(strip=True)
                    info_lines = [line.strip() for line in info_elem.text.split('\n') if line.strip()]
                    director_actors = info_lines[0] if info_lines else ""
                    details = info_lines[1] if len(info_lines) > 1 else ""
                
                # 评分
                rating_elem = item.select_one('.rating_num')
                rating = rating_elem.text.strip() if rating_elem else "0.0"
                
                # 评价人数
                rating_people = "0"
                people_elem = item.select_one('.star span:nth-last-child(1)')
                if people_elem:
                    people_text = people_elem.text.strip()
                    rating_people = people_text.replace('人评价', '').strip('()')
                
                # 简介
                quote = ""
                quote_elem = item.select_one('.quote .inq')
                if quote_elem:
                    quote = quote_elem.text.strip()
                
                movie = {
                    'rank': rank,
                    'title': title,
                    'original_title': original_title.strip('/').strip(),
                    'other_title': other_title.strip('/').strip(),
                    'director_actors': director_actors,
                    'details': details,
                    'rating': rating,
                    'rating_people': rating_people,
                    'quote': quote
                }
                
                page_movies.append(movie)
                logger.debug(f"解析电影: {title}, 排名: {rank}")
            
            except Exception as e:
                logger.error(f"解析电影数据出错: {e}", exc_info=True)
        
        logger.info(f"成功解析 {len(page_movies)} 部电影数据")
        return page_movies
    
    def crawl_top250(self):
        """爬取豆瓣Top250电影"""
        total_pages = 10  # 豆瓣Top250共10页
        
        for page in range(1, total_pages + 1):
            logger.info(f"开始爬取第 {page} 页")
            
            page_movies = self.fetch_page(page)
            self.movies.extend(page_movies)
            
            # 添加随机延迟，避免被封
            sleep_time = random.uniform(3, 6)
            logger.info(f"第 {page} 页爬取完成，休息 {sleep_time:.2f} 秒")
            time.sleep(sleep_time)
        
        logger.info(f"爬取完成，共获取 {len(self.movies)} 部电影数据")
        return self.movies
    
    def save_to_csv(self, filename="douban_top250.csv"):
        """将爬取的数据保存为CSV文件"""
        if not self.movies:
            logger.warning("没有数据可保存")
            return False
        
        df = pd.DataFrame(self.movies)
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        logger.info(f"数据已保存至 {filename}")
        return True



def main():
    """主函数"""
    logger.info("开始构建代理池...")
    proxy_pool = ProxyPool()
    pool_built = proxy_pool.build_pool(min_size=5)  # 至少需要5个可用代理
    
    if not pool_built and not proxy_pool.proxy_pool:
        logger.error("代理池构建失败且没有可用代理，程序退出")
        return
    
    # 即使代理数量不够最低要求，也尝试使用现有代理爬取
    logger.info("开始爬取豆瓣电影Top250...")
    crawler = DoubanCrawler(proxy_pool)
    crawler.crawl_top250()
    
    # 保存结果
    crawler.save_to_csv()


if __name__ == "__main__":
    main()
