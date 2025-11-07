import json, os, re, requests
import asyncio, aiofiles
from typing import List, Dict, Any, Optional

from bs4 import BeautifulSoup
from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CrawlerRunConfig,
    CacheMode,
)

from luogu_agent.core.constant import *
from luogu_agent.core.schema import ProblemDetails, SolutionDetails
from luogu_agent.core.strategy import create_problem_strategy, create_solution_strategy

class LuoguCrawlerAgent:
    """
    负责洛谷题目和题解的爬取、提取和缓存。
    """

    def __init__(self, api_key: str, base_url: str, crawler: AsyncWebCrawler, cache_dir: str = CACHE_DIR):
        self.crawler = crawler
        self.cache_dir = cache_dir
        self.problem_strategy = create_problem_strategy(api_key, base_url)
        self.solution_strategy = create_solution_strategy(api_key, base_url)
        os.makedirs(self.cache_dir, exist_ok=True)
        print(f"[CrawlerAgent] 初始化完成，缓存目录: {self.cache_dir}")

    # --- 1. 公共主入口 (指挥官) ---

    async def run(self, problem_id: str, max_solutions: int = 3) -> Dict[str, Any]:
        """
        [主入口] 执行完整的爬取和提取流程。
        """
        print(f"\n--- [CrawlerAgent] 启动 {problem_id} 任务 (max={max_solutions}) ---")

        # 1. 尝试从缓存加载
        cached_data = await self._load_from_cache(problem_id, max_solutions)
        if cached_data:
            print(f"--- [CrawlerAgent] {problem_id} 任务完成 (来自缓存) ---")
            return cached_data

        # 2. 缓存未命中，执行爬取流水线
        print(f"[CrawlerAgent] CACHE MISS: {problem_id}。开始实时爬取...")
        final_output = await self._execute_crawl_pipeline(problem_id, max_solutions)

        # 3. 仅在爬取成功时保存到缓存
        if "error" not in final_output.get("problem", {}):
            await self._save_to_cache(problem_id, final_output)
        else:
            print(f"[CrawlerAgent] 题目爬取失败，不保存缓存。")

        print(f"--- [CrawlerAgent] {problem_id} 任务完成 (实时爬取)。---")
        return final_output

    # --- 2. 缓存处理 (I/O) ---

    async def _load_from_cache(self, problem_id: str, max_solutions: int) -> Optional[Dict[str, Any]]:
        """(职责1) 尝试从本地 JSON 加载并验证缓存"""
        cache_file = os.path.join(self.cache_dir, f"{problem_id}.json")
        try:
            async with aiofiles.open(cache_file, 'r', encoding='utf-8') as f:
                content = await f.read()
                cached_data = json.loads(content)

            # 验证缓存数据
            if 'problem' not in cached_data or "error" in cached_data['problem']:
                print(f"[CrawlerAgent] CACHE INVALID: {problem_id} 缓存损坏。")
                return None
            
            # 验证缓存数量
            cached_solutions_count = len(cached_data.get("solutions", []))
            if cached_solutions_count >= max_solutions:
                print(f"[CrawlerAgent] CACHE HIT: {problem_id} (含 {cached_solutions_count} 篇题解) 满足需求。")
                return cached_data
            else:
                print(f"[CrawlerAgent] CACHE PARTIAL: 缓存 {cached_solutions_count} 篇, 需求 {max_solutions}。")
                return None

        except FileNotFoundError:
            return None  # 缓存未命中，正常
        except Exception as e:
            print(f"[CrawlerAgent] CACHE ERROR: 加载 {cache_file} 失败 ({e})。")
            return None # 缓存读取失败，当作未命中处理

    async def _save_to_cache(self, problem_id: str, data: Dict[str, Any]):
        """(职责2) 异步保存结果到 JSON 缓存"""
        cache_file = os.path.join(self.cache_dir, f"{problem_id}.json")
        try:
            async with aiofiles.open(cache_file, 'w', encoding='utf-8') as f:
                content_to_save = json.dumps(data, indent=2, ensure_ascii=False)
                await f.write(content_to_save)
            print(f"[CrawlerAgent] CACHE SAVE: 成功保存 {problem_id} 到 {cache_file}")
        except Exception as e:
            print(f"[CrawlerAgent] CACHE SAVE FAILED: 写入 {cache_file} 失败: {e}")

    # --- 3. 核心爬取流水线 (干活的) ---

    async def _execute_crawl_pipeline(self, problem_id: str, max_solutions: int) -> Dict[str, Any]:
        """(职责3) 执行所有爬取、搜索和提取任务"""
        
        # 3.1. 并行执行“爬题目”和“搜题解列表”
        problem_task = self._fetch_problem_details(problem_id)
        search_task = self._search_solution_urls(problem_id)
        
        problem_result, solution_urls = await asyncio.gather(problem_task, search_task)
        
        final_output = {
            "problem": problem_result,
            "solutions": []
        }
        
        # 如果题目爬取失败，则中止
        if "error" in problem_result:
            print(f"[CrawlerAgent] 严重错误：题目 {problem_id} 爬取失败。任务中止。")
            return final_output

        # 如果没有题解，也提前返回
        if not solution_urls:
            print(f"[CrawlerAgent] 警告：没有找到 {problem_id} 的题解链接。")
            return final_output

        # 3.2. 并行提取 N 篇题解
        urls_to_fetch = solution_urls[:max_solutions]
        print(f"[CrawlerAgent] 准备从 {len(urls_to_fetch)} 个链接中提取题解内容...")
        
        solution_tasks = [self._fetch_solution_content(article) for article in urls_to_fetch]
        solution_results = await asyncio.gather(*solution_tasks)
        
        # 3.3. 清洗题解结果
        successful_solutions = []
        for i, res in enumerate(solution_results):
            if "error" not in res:
                successful_solutions.append(res)
            else:
                print(f"[CrawlerAgent] 提取 {urls_to_fetch[i]['url']} 失败: {res['error']}")
        
        final_output["solutions"] = successful_solutions
        print(f"[CrawlerAgent] 提取完成，成功 {len(successful_solutions)} / {len(urls_to_fetch)} 篇。")
        return final_output

    # --- 4. 子任务  ---

    async def _fetch_problem_details(self, problem_id: str) -> Dict[str, Any]:
        """[子任务] 爬取并提取单个题目的详细信息。"""
        url = f"https://www.luogu.com.cn/problem/{problem_id}"
        print(f"[CrawlerAgent.Problem] 正在爬取题目: {url}")
        
        config = CrawlerRunConfig(
            cache_mode=CacheMode.ENABLED, # 题目页可以缓存
            extraction_strategy=self.problem_strategy,
            delay_before_return_html=1
        )
        result = await self.crawler.arun(url, config=config)
        
        if not (result.success and result.extracted_content):
            return {"error": "crawl4ai 爬取题目失败", "details": result.error_message}
            
        try:
            data_list = json.loads(result.extracted_content)
            if not data_list:
                return {"error": "LLM 从题目页返回了空列表"}
            
            problem_data = ProblemDetails.model_validate(data_list[0])
            print(f"[CrawlerAgent.Problem] 题目 {problem_id} 提取成功。")
            return problem_data.model_dump()
        
        except json.JSONDecodeError:
            return {"error": "LLM 返回了无效的 JSON", "raw": result.extracted_content}
        except Exception as e:
            return {"error": f"Pydantic 验证失败: {e}", "raw": result.extracted_content}

    async def _search_solution_urls(self, problem_id: str) -> List[Dict[str, str]]:
        """[子任务] 异步执行同步的 URL 搜索。"""
        loop = asyncio.get_running_loop()
        # 在一个单独的线程中运行同步的 blocking IO
        results = await loop.run_in_executor(
            None, self._sync_search_solutions, problem_id
        )
        return results

    def _sync_search_solutions(self, problem_id: str) -> List[Dict[str, str]]:
        """[子任务] 同步使用 requests 搜索题解 URL。"""
        search_url = f"https://www.luogu.com.cn/article?keyword={problem_id}&page=1"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        print(f"[CrawlerAgent.Search] 正在用 requests 搜索: {search_url} ...")
        
        try:
            response = requests.get(search_url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            article_links = soup.find_all('a', href=re.compile(r'^/article/[a-zA-Z0-9]{8}$'))
            
            if not article_links:
                print("[CrawlerAgent.Search] 失败：没有找到任何 /article/... 链接。")
                return []

            results = []
            seen_urls = set()
            for link in article_links:
                href = link.get('href')
                if href in seen_urls:
                    continue
                
                title = link.get_text(strip=True)
                if href and (problem_id in title or problem_id.lower() in title):
                    results.append({"title": title, "url": href})
                    seen_urls.add(href)

            print(f"[CrawlerAgent.Search] 成功：找到 {len(results)} 篇相关题解链接。")
            return results
            
        except requests.RequestException as e:
            print(f"[CrawlerAgent.Search] 异常: {e}")
            return []

    async def _fetch_solution_content(self, article: Dict[str, str]) -> Dict[str, Any]:
        """[子任务] 爬取并提取单篇题解的详细内容。"""
        full_url = f"https://www.luogu.com.cn{article['url']}"
        print(f"[CrawlerAgent.Solution] 正在提取: {full_url} ...")
        
        config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS, # 题解页不应缓存
            extraction_strategy=self.solution_strategy,
            delay_before_return_html=1
        )
        result = await self.crawler.arun(full_url, config=config)
        
        if not (result.success and result.extracted_content):
             return {"error": "crawl4ai 爬取题解失败"}
             
        try:
            data_list = json.loads(result.extracted_content)
            if not data_list:
                return {"error": "LLM 从题解页返回了空列表"}
            
            raw_data = data_list[0]
            clean_data = SolutionDetails.model_validate(raw_data)
            
            if not clean_data.solution_text:
                return {"error": "LLM 返回了空内容"}
            
            # 附加上 title 和 url
            final_data = clean_data.model_dump()
            final_data['title'] = article['title']
            final_data['url'] = article['url']
            return final_data

        except json.JSONDecodeError:
            return {"error": "LLM 返回了无效的 JSON", "raw": result.extracted_content}
        except Exception as e:
            return {"error": f"Pydantic 验证失败: {e}", "raw": result.extracted_content}

async def main():
    TEST_PROBLEM_ID = "P1238"
    
    brouser_config = BrowserConfig(headless=True, proxy=None)
    
    async with AsyncWebCrawler(config=brouser_config) as crawler:
        
        agent = LuoguCrawlerAgent(DMX_API_KEY, DMX_BASE_URL, crawler, cache_dir=CACHE_DIR)
        
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