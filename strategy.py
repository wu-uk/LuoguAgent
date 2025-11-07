from crawl4ai import LLMExtractionStrategy, LLMConfig
from constant import DMX_API_KEY
from schema import ProblemDetails, SolutionDetails

def create_problem_strategy(api_key: str, base_url: str):
    problem_strategy = LLMExtractionStrategy(
        llm_config=LLMConfig(
            provider="deepseek/deepseek-chat",
            api_token=api_key,
            base_url=base_url
        ),
        schema=ProblemDetails.model_json_schema(),
        extraction_type="schema",
        instruction="你是一个爬虫助手，请从给定的网页 Markdown 中提取算法题目的关键信息。",
        apply_chunking=False,
        input_format="markdown",
        extra_args={"temperature": 0.1, "max_tokens": 2000}
    )
    return problem_strategy

def create_solution_strategy(api_key: str, base_url: str):
    solution_strategy =  LLMExtractionStrategy(
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
    return solution_strategy
