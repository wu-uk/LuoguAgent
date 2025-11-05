import requests
from bs4 import BeautifulSoup
import re
import json
import asyncio
import os
from pydantic import BaseModel, Field
from typing import List, Optional 
from crawl4ai import *
from constant import DMX_API_KEY 

# --- 第 1 阶段：搜索 (requests + bs4) ---
async def search_for_solution_urls(problem_id: str) -> List[dict]:
    search_url = f"https://www.luogu.com.cn/article?keyword={problem_id}&page=1"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    print(f"[Phase 1] 正在用 requests 搜索: {search_url} ...")
    
    try:
        response = requests.get(search_url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        article_links = soup.find_all('a', href=re.compile(r'^/article/[a-zA-Z0-9]{8}$'))
        
        if not article_links:
            print("[Phase 1] 失败：没有找到任何 /article/... 链接。")
            return []

        results = []
        for link in article_links:
            href = link.get('href')
            title = link.get_text(strip=True)
            
            if href and (problem_id in title or problem_id in href):
                if href not in [r['url'] for r in results]: 
                    results.append({"title": title, "url": href})

        print(f"[Phase 1] 成功：找到 {len(results)} 篇相关题解链接。")
        return results
        
    except requests.RequestException as e:
        print(f"[Phase 1] 异常: {e}")
        return []

# --- 第 2 阶段：提取 (crawl4ai + LLM) ---
class SolutionDetails(BaseModel):
    solution_text: str = Field(..., description="提取完整的题解思路和文字说明 (必须保留所有 LaTeX 数学公式)")
    author: Optional[str] = Field(None, description="提取题解的作者用户名")
    code: Optional[str] = Field(None, description="提取该题解对应的完整代码块")
    code_language: Optional[str] = Field(None, description="提取代码块的编程语言 (例如 C++, Python)")

strategy = LLMExtractionStrategy(
    llm_config=LLMConfig(
        provider="deepseek/deepseek-chat", 
        api_token=DMX_API_KEY,
        base_url="https://www.dmxapi.cn/v1"
    ),
    schema=SolutionDetails.model_json_schema(),
    extraction_type="schema",
    instruction="你是一个爬虫助手，请从给定的文章页中提取作者、题解思路和代码。",
    apply_chunking=False,
    input_format="markdown", 
    extra_args={"temperature": 0.1, "max_tokens": 4096} 
)

async def extract_solution_content(article_url: str, crawler: AsyncWebCrawler) -> dict:
    """
    使用 crawl4ai 提取一篇公开文章页的具体内容。
    """
    full_url = f"https://www.luogu.com.cn{article_url}"
    print(f"[Phase 2] 正在用 crawl4ai 提取: {full_url} ...")
    
    config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS, 
        extraction_strategy=strategy,
        delay_before_return_html=3 
    )
    
    result = await crawler.arun(full_url, config=config)
    
    if result.success and result.extracted_content:
        try:
            data_list = json.loads(result.extracted_content)
            if not data_list:
                return {"error": "LLM 返回了空列表"}
            
            raw_data = data_list[0] 
            
            clean_data_model = SolutionDetails.model_validate(raw_data)
            
            return clean_data_model.model_dump()

        except json.JSONDecodeError:
            return {"error": "LLM 返回了无效的 JSON", "raw_content": result.extracted_content}
        except Exception as e:
            return {"error": f"Pydantic 验证失败: {e}", "raw_data": raw_data}
    else:
        return {"error": "crawl4ai 爬取失败"}

async def main():
    PROBLEM_ID = "P1268"
    
    article_urls = await search_for_solution_urls(PROBLEM_ID)
    
    if not article_urls:
        print("没有找到任何题解 URL，程序退出。")
        return
        
    print(f"\n--- 准备提取 {len(article_urls)} 篇文章的详细内容 ---")
    
    brouser_config = BrowserConfig(headless=True, proxy=None)
    
    async with AsyncWebCrawler(config=brouser_config) as crawler:
        all_solutions = []
        for article in article_urls[:3]:
            solution_data = await extract_solution_content(article['url'], crawler)
            
            if "error" in solution_data:
                print(f"提取 {article['url']} 失败: {solution_data['error']}")
            elif not solution_data.get("solution_text"):
                print(f"提取 {article['url']} 失败: LLM 返回了空内容。")
            else:
                solution_data['title'] = article['title']
                solution_data['url'] = article['url']
                all_solutions.append(solution_data)
            
            await asyncio.sleep(1) # 别爬太快

    print("\n\n--- 爬取完毕：所有提取成功的题解 ---")
    print(json.dumps(all_solutions, indent=2, ensure_ascii=False))
    print(f"\n成功从 {len(article_urls)} 个链接中提取了 {len(all_solutions)} 篇题解。")


if __name__ == "__main__":
    asyncio.run(main())