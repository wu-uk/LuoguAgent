import json
import os
import re
import requests
import asyncio, aiofiles  # 用于异步文件 IO
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CrawlerRunConfig,
    CacheMode,
)

from constant import *
from schema import ProblemDetails, SolutionDetails
from strategy import PROBLEM_STRATEGY, SOLUTION_STRATEGY

class LuoguCrawlerAgent:
    """
    封装了针对洛谷题目和题解的完整爬取流程。
    [!] 新增了本地 JSON 缓存功能。
    """

    def __init__(self, crawler: AsyncWebCrawler, cache_dir: str = CACHE_DIR):  # <--- 修改
        """
        初始化 Agent，传入一个已经实例化的 AsyncWebCrawler。
        """
        self.crawler = crawler
        self.cache_dir = cache_dir  # <--- 新增
        # 同步创建目录，这在初始化时是可接受的
        os.makedirs(self.cache_dir, exist_ok=True)  # <--- 新增
        print(f"[Agent] 初始化完成，使用缓存目录: {self.cache_dir}")

    # ... extract_problem_details 方法保持不变 ...
    async def extract_problem_details(self, problem_id: str) -> Dict[str, Any]:
        """
        [子任务] 爬取并提取单个题目的详细信息。
        """
        url = f"https://www.luogu.com.cn/problem/{problem_id}"
        print(f"[Agent.Problem] 正在爬取题目: {url}")
        
        config = CrawlerRunConfig(
            cache_mode=CacheMode.ENABLED, # 题目页可以缓存
            extraction_strategy=PROBLEM_STRATEGY,
            delay_before_return_html=1
        )
        
        result = await self.crawler.arun(url, config=config)
        
        if result.success and result.extracted_content:
            try:
                data_list = json.loads(result.extracted_content)
                if not data_list:
                    return {"error": "LLM 从题目页返回了空列表"}
                
                problem_data = ProblemDetails.model_validate(data_list[0])
                print(f"[Agent.Problem] 题目 {problem_id} 提取成功。")
                return problem_data.model_dump()
            
            except json.JSONDecodeError:
                return {"error": "LLM 返回了无效的 JSON", "raw": result.extracted_content}
            except Exception as e:
                return {"error": f"Pydantic 验证失败: {e}", "raw": data_list[0]}
        else:
            return {"error": "crawl4ai 爬取题目失败", "details": result.error_message}


    def _sync_search_solutions(self, problem_id: str) -> List[Dict[str, str]]:
        """
        [同步] 使用 requests 搜索题解 URL。
        """
        search_url = f"https://www.luogu.com.cn/article?keyword={problem_id}&page=1"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        print(f"[Agent.Search] 正在用 requests 搜索: {search_url} ...")
        
        try:
            response = requests.get(search_url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            article_links = soup.find_all('a', href=re.compile(r'^/article/[a-zA-Z0-9]{8}$'))
            
            if not article_links:
                print("[Agent.Search] 失败：没有找到任何 /article/... 链接。")
                return []

            results = []
            for link in article_links:
                href = link.get('href')
                title = link.get_text(strip=True)
                
                if href and (problem_id in title or problem_id.lower() in title):
                    if href not in [r['url'] for r in results]:
                        results.append({"title": title, "url": href})

            print(f"[Agent.Search] 成功：找到 {len(results)} 篇相关题解链接。")
            return results
            
        except requests.RequestException as e:
            print(f"[Agent.Search] 异常: {e}")
            return []

    async def search_for_solution_urls(self, problem_id: str) -> List[Dict[str, str]]:
        """
        [子任务] 异步执行同步的 URL 搜索。
        """
        loop = asyncio.get_running_loop()
        results = await loop.run_in_executor(
            None, self._sync_search_solutions, problem_id
        )
        return results

    async def extract_solution_content(self, article: Dict[str, str]) -> Dict[str, Any]:
        """
        [子任务] 爬取并提取单篇题解的详细内容。
        """
        full_url = f"https://www.luogu.com.cn{article['url']}"
        print(f"[Agent.Solution] 正在用 crawl4ai 提取: {full_url} ...")
        
        config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            extraction_strategy=SOLUTION_STRATEGY,
            delay_before_return_html=1
        )
        
        result = await self.crawler.arun(full_url, config=config)
        
        if result.success and result.extracted_content:
            try:
                data_list = json.loads(result.extracted_content)
                if not data_list:
                    return {"error": "LLM 从题解页返回了空列表"}
                
                raw_data = data_list[0]
                clean_data = SolutionDetails.model_validate(raw_data)
                
                if not clean_data.solution_text:
                    return {"error": "LLM 返回了空内容"}
                
                final_data = clean_data.model_dump()
                final_data['title'] = article['title']
                final_data['url'] = article['url']
                return final_data

            except json.JSONDecodeError:
                return {"error": "LLM 返回了无效的 JSON", "raw": result.extracted_content}
            except Exception as e:
                return {"error": f"Pydantic 验证失败: {e}", "raw": raw_data}
        else:
            return {"error": "crawl4ai 爬取题解失败"}

    async def run(self, problem_id: str, max_solutions: int = 3) -> Dict[str, Any]:
        """
        [主入口] 执行完整的爬取和提取流程。
        [!] 增加了缓存检查和保存逻辑。
        """
        print(f"\n--- [Agent] 启动 {problem_id} 完整任务 (max_solutions={max_solutions}) ---")

        # --- 1. 缓存检查 (Cache Check) ---
        cache_file = os.path.join(self.cache_dir, f"{problem_id}.json")

        try:
            async with aiofiles.open(cache_file, 'r', encoding='utf-8') as f:
                content = await f.read()
                cached_data = json.loads(content)

            # 检查缓存是否有效
            if 'problem' in cached_data and "error" not in cached_data['problem']:
                # 检查缓存的题解数量是否满足本次请求
                cached_solutions_count = len(cached_data.get("solutions", []))
                if cached_solutions_count >= max_solutions:
                    print(f"[Agent] CACHE HIT: {problem_id} (含 {cached_solutions_count} 篇题解) 满足需求。从本地加载。")
                    print(f"--- [Agent] {problem_id} 任务完成 (来自缓存)。---")
                    return cached_data
                else:
                    print(f"[Agent] CACHE PARTIAL: 缓存有 {cached_solutions_count} 篇题解, 需求 {max_solutions}。重新爬取。")
            else:
                print(f"[Agent] CACHE INVALID: 缓存数据 {problem_id} 损坏。重新爬取。")

        except FileNotFoundError:
            print(f"[Agent] CACHE MISS: {problem_id} 未在本地找到。开始爬取...")
        except Exception as e:
            print(f"[Agent] CACHE ERROR: 加载 {cache_file} 失败 ({e})。重新爬取。")

        # --- 2. 缓存未命中或失效，执行完整爬取 ---

        # 2.1. 并行执行“爬题目”和“搜题解列表”
        problem_task = self.extract_problem_details(problem_id)
        search_task = self.search_for_solution_urls(problem_id)
        
        problem_result, solution_urls = await asyncio.gather(problem_task, search_task)
        
        final_output = {
            "problem": problem_result,
            "solutions": []
        }
        
        if "error" in problem_result:
            print(f"[Agent] 严重错误：题目 {problem_id} 爬取失败。任务中止。")
            return final_output

        if not solution_urls:
            print(f"[Agent] 警告：没有找到 {problem_id} 的题解链接。")
        
        else:
            # 2.2. 并行提取 N 篇题解
            urls_to_fetch = solution_urls[:max_solutions]
            print(f"[Agent] 准备从 {len(urls_to_fetch)} 个链接中提取题解内容...")
            
            solution_tasks = [self.extract_solution_content(article) for article in urls_to_fetch]
            solution_results = await asyncio.gather(*solution_tasks)
            
            # 2.3. 清洗题解结果
            successful_solutions = []
            for i, res in enumerate(solution_results):
                if "error" not in res:
                    successful_solutions.append(res)
                else:
                    print(f"[Agent] 提取 {urls_to_fetch[i]['url']} 失败: {res['error']}")
            
            final_output["solutions"] = successful_solutions

        # --- 3. 缓存保存 (Cache Save) ---
        if "error" not in final_output["problem"]:
            try:
                async with aiofiles.open(cache_file, 'w', encoding='utf-8') as f:
                    content_to_save = json.dumps(final_output, indent=2, ensure_ascii=False)
                    await f.write(content_to_save)
                print(f"[Agent] CACHE SAVE: 成功保存 {problem_id} 到 {cache_file}")
            except Exception as e:
                print(f"[Agent] CACHE SAVE FAILED: 写入 {cache_file} 失败: {e}")
        
        print(f"--- [Agent] {problem_id} 任务完成。成功提取 {len(final_output['solutions'])} 篇题解。---")
        return final_output

async def main():
    TEST_PROBLEM_ID = "P4137"
    
    brouser_config = BrowserConfig(headless=True, proxy=None)
    
    async with AsyncWebCrawler(config=brouser_config) as crawler:
        
        agent = LuoguCrawlerAgent(crawler, cache_dir=CACHE_DIR)
        
        final_data = await agent.run(TEST_PROBLEM_ID, max_solutions=1)
        
        print("\n\n--- [Main] Agent 执行完毕，最终数据: ---")
        print(json.dumps(final_data, indent=2, ensure_ascii=False))
        
        if "error" in final_data["problem"]:
            print(f"\n问题：题目爬取失败: {final_data['problem']['error']}")
        else:
            print(f"\n成功：爬取到题目 {final_data['problem']['description'][:20]}...")
            
        print(f"成功：爬取到 {len(final_data['solutions'])} 篇题解。")

        # # --- (可选) 测试缓存 ---
        # print("\n\n--- [Main] 3秒后，再次运行以测试缓存... ---")
        # await asyncio.sleep(3)
        # # 这次调用应该会立即从缓存返回
        # final_data_cached = await agent.run(TEST_PROBLEM_ID, max_solutions=1)
        # print(f"第二次运行是否使用了缓存? {'是的' if final_data == final_data_cached else '否'}")

if __name__ == "__main__":
    asyncio.run(main())