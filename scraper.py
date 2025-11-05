from pydantic import BaseModel, Field
import json, asyncio, os
from crawl4ai import *
import json
from typing import List
from constant import DMX_API_KEY

class ProblemDetails(BaseModel):
    background: str = Field(..., description="提取题目背景，如果没有则返回 '无'")
    description: str = Field(..., description="提取完整的题目描述")
    input_format: str = Field(..., description="提取输入格式说明")
    output_format: str = Field(..., description="提取输出格式说明")
    examples: List[dict] = Field(..., description="提取所有的输入输出样例。每个样例是一个字典，包含 'input' 和 'output' 键")
    notes: str = Field(..., description="提取说明/提示部分。注意：必须保留所有的数学符号、上标和格式。如果没有则返回 '无'")

strategy = LLMExtractionStrategy(
    llm_config=LLMConfig(
        provider="openai/gpt-4o", 
        api_token=DMX_API_KEY,
        base_url="https://www.dmxapi.cn/v1"
    ),

    schema=ProblemDetails.model_json_schema(),
    
    extraction_type="schema", #
    
    instruction="你是一个爬虫助手，请从给定的网页 Markdown 中提取算法题目的关键信息。", #
    
    apply_chunking=False,
    
    input_format="markdown", #
    
    extra_args={"temperature": 0.1, "max_tokens": 2000} 
)


test_url = "https://www.luogu.com.cn/problem/P1268"

async def main():
    brouser_config = BrowserConfig(headless=True, proxy=None)

    config = CrawlerRunConfig(
        cache_mode=CacheMode.ENABLED,
        extraction_strategy=strategy,
        delay_before_return_html=3
    )

    async with AsyncWebCrawler(config=brouser_config) as crawler:
        print(f"正在爬取 {test_url} 并提取...")
        result = await crawler.arun(test_url, config=config)
        if result.success and result.extracted_content:
            try:
                # 官方示例说，成功后，extracted_content 就是 JSON
                data = json.loads(result.extracted_content)
                print("--- 提取成功 ---")
                print(json.dumps(data, indent=2, ensure_ascii=False))
                
                # 打印 Token 消耗
                strategy.show_usage() 
                
            except json.JSONDecodeError:
                print("--- 提取失败 ---")
                print("LLM 返回的不是一个有效的 JSON:")
                print(result.extracted_content)
        else:
            print("--- 提取失败 ---")
            print("爬虫或提取步骤出错。")
            if result.error_message:
                print(f"错误信息: {result.error_message}")


if __name__ == "__main__":
    asyncio.run(main())