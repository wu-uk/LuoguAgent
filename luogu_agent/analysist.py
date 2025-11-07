import os, re, json, asyncio, traceback, ast
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Tuple, Optional

from crawl4ai import AsyncWebCrawler, BrowserConfig
from zai import ZhipuAiClient

from luogu_agent.crawler import LuoguCrawlerAgent
from luogu_agent.core.constant import *
from luogu_agent.core.prompts import get_system_prompt, get_user_prompt
from luogu_agent.core.schema import ProblemAnalysis


class AnalysisAgent:
    """
    负责调用 LLM 分析问题数据，并处理和保存结果。
    会同时保存 .json (机器可读) 和 .md (人类可读) 两种格式。
    """
    
    def __init__(self, api_key: str, base_url: str):
        try:
            self.llm = ZhipuAiClient(api_key=api_key, base_url=base_url)
        except Exception as e:
            print(f"ZhipuAiClient 初始化失败: {e}")
            raise ValueError(f"ZhipuAiClient 初始化失败。请检查 API Key 和 Base URL。{e}")
        self.schema = ProblemAnalysis  
        self.analysis_cache_dir = ANALYSIS_CACHE_DIR
        os.makedirs(self.analysis_cache_dir, exist_ok=True)
        print(f"[Agent] 初始化完成 (ZhipuAI)，结果保存至 {self.analysis_cache_dir}")

    def _build_prompts(self, problem_data: Dict[str, Any], solutions_data: List[Dict[str, Any]]) -> Tuple[str, str]:
        """构建系统和用户提示词"""
        system_prompt = get_system_prompt(self.schema.model_fields)
        user_prompt = get_user_prompt(problem_data, solutions_data)
        return system_prompt, user_prompt

    def _stream_llm_response(self, system_prompt: str, user_prompt: str) -> str:
        """调用 LLM 并流式获取完整响应"""
        print("[Agent] 正在流式接收 LLM 响应...")
        response = self.llm.chat.completions.create(
            model="glm-4.6", 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            thinking={"type": "disabled"},
            response_format={"type": "json_object"},    
            stream=True
        )

        full_content = ""
        for chunk in response:
            if not chunk.choices: continue
            delta = chunk.choices[0].delta
            if hasattr(delta, 'content') and delta.content:
                full_content += delta.content
                print(delta.content, end="", flush=True) 
            
            if chunk.choices[0].finish_reason:
                print(f"\n\n[Agent] 完成原因: {chunk.choices[0].finish_reason}")
                if hasattr(chunk, 'usage') and chunk.usage:
                    print(f"[Agent] 令牌使用: 输入 {chunk.usage.prompt_tokens}, 输出 {chunk.usage.completion_tokens}")
        
        print("\n[Agent] LLM 响应接收完毕。")
        return full_content

    def _extract_json_string(self, raw_content: str) -> str:
        """从 LLM 的原始输出中提取 { ... } 块"""
        match = re.search(r'\{.*\}', raw_content, re.DOTALL)
        if match:
            print("[Agent] 已从 LLM 响应中提取 { } 块。")
            return match.group(0)
        
        print("[Agent] 无法提取 { } 块，将尝试解析完整响应。")
        return raw_content

    def _parse_to_dict(self, s: str) -> Optional[Dict[str, Any]]:
        """使用双保险 (json / ast) 解析字符串为字典"""
        try:
            parsed = json.loads(s)
            print("[Agent] 成功解析为 JSON。")
            return parsed
        except json.JSONDecodeError:
            print("[Agent] JSON 解析失败，尝试 ast.literal_eval (Python 字典)...")
            try:
                parsed = ast.literal_eval(s)
                print("[Agent] 成功解析为 Python 字面量。")
                return parsed
            except Exception as e:
                print(f"[Agent] 所有解析均失败: {e}")
                return None

    def _save_json_result(self, problem_id: str, data: Dict[str, Any]):
        """将解析成功的字典保存为美化的 .json 文件"""
        save_path = os.path.join(self.analysis_cache_dir, f"{problem_id}_analysis.json")
        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"[Agent] 分析结果 (JSON) 已保存到: {save_path}")
        except Exception as e:
            print(f"[Agent] 保存 .json 文件时出错: {e}")

    def _save_markdown_result(self, problem_id: str, data: Dict[str, Any]):
        """[!] 将解析结果中的关键字段提取并保存为 .md 文件"""
        save_path = os.path.join(self.analysis_cache_dir, f"{problem_id}_analysis.md")
        
        # 1. 从字典中提取内容
        solution_text = data.get('detailed_solution', 'LLM 未提供详细题解。')
        sample_code = data.get('sample_code', 'LLM 未提供示例代码。')
        keywords = data.get('keywords', [])
        
        # 我们的 Pydantic 描述里写了是 C++
        code_lang = "cpp"

        # 2. 构建 Markdown 字符串
        md_content = f"# {problem_id} 详细题解\n\n"
        md_content += f"{solution_text}\n\n"
        
        md_content += f"# 参考代码 ({code_lang})\n\n"
        md_content += f"```{code_lang}\n"
        md_content += f"{sample_code}\n"
        md_content += "```\n\n"
        
        md_content += "# 核心知识点\n\n"
        if keywords:
            for keyword in keywords:
                md_content += f"* {keyword}\n"
        else:
            md_content += "无\n"

        # 3. 保存文件
        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(md_content)
            print(f"[Agent] 分析结果 (Markdown) 已保存到: {save_path}")
        except Exception as e:
            print(f"[Agent] 保存 .md 文件时出错: {e}")

    def _save_error(self, problem_id: str, raw_content: str):
        """保存原始的、无法解析的 LLM 响应"""
        error_path = os.path.join(self.analysis_cache_dir, f"{problem_id}_error.txt")
        try:
            with open(error_path, 'w', encoding='utf-8') as f:
                f.write(raw_content)
            print(f"[Agent] 原始错误响应已保存到: {error_path}")
        except Exception as e:
            print(f"[Agent] 保存 _error.txt 文件时出错: {e}")

    def run(self, problem_id: str, problem_data: Dict[str, Any], solutions_data: List[Dict[str, Any]]) -> str:
        """
        [主入口] 执行完整的分析、解析和保存流程。
        返回 LLM 的原始字符串响应。
        """
        print(f"\n--- [Agent] 开始分析 {problem_id} ---")
        
        # 1. 构建提示
        system_prompt, user_prompt = self._build_prompts(problem_data, solutions_data)
        
        # 2. 获取 LLM 响应
        full_content = self._stream_llm_response(system_prompt, user_prompt)
        if not full_content:
            print("[Agent] LLM 响应为空，任务中止。")
            return full_content

        # 3. 提取
        extracted_str = self._extract_json_string(full_content)
        
        # 4. 解析
        parsed_data = self._parse_to_dict(extracted_str)

        # 5. 保存
        if parsed_data:
            # [!] 同时调用两个保存方法
            self._save_json_result(problem_id, parsed_data)
            self._save_markdown_result(problem_id, parsed_data)
        else:
            self._save_error(problem_id, full_content)
            
        return full_content


async def main():
    TEST_PROBLEM_ID = "P1117" 
    
    analysis_agent = AnalysisAgent()

    print("--- [Main] 启动爬虫 Agent ---")
    brouser_config = BrowserConfig(headless=True, proxy=None)
    
    raw_crawler_data = {}
    try:
        async with AsyncWebCrawler(config=brouser_config) as crawler:
            # (注意：这里的 LuoguCrawlerAgent 是你上一个文件里的)
            # (确保它被正确导入)
            agent = LuoguCrawlerAgent(crawler, cache_dir=CACHE_DIR)
            raw_crawler_data = await agent.run(TEST_PROBLEM_ID, max_solutions=3)
            
        print("--- [Main] 爬虫 Agent 执行完毕 ---")
    except Exception as e:
        print(f"[Main] 爬虫 Agent 运行时发生异常，详细信息如下:")
        traceback.print_exc()
        return None

    # 3. 检查爬虫数据
    problem_data = raw_crawler_data.get("problem", {})
    solutions_data = raw_crawler_data.get("solutions", [])
    
    if "error" in problem_data or not problem_data:
        print(f"[Main] 爬虫失败，无法启动分析 Agent: {problem_data.get('error', '未知错误')}")
        return None 
    # --- 爬虫逻辑结束 ---

    # 4. [Step 2] 执行分析 Agent (大脑)
    print("--- [Main] 启动分析 Agent ---")
    
    result_raw_string = analysis_agent.run(TEST_PROBLEM_ID, problem_data, solutions_data)
    
    if not result_raw_string:
        print("--- [Main] Agent 没有返回任何结果。 ---")
        return

    # --- [!!] 修改：main 函数的美化打印逻辑 [!!] ---
    print("\n--- [Main] ===== 最终分析结果 (美化打印) ===== ---")
    
    try:
        # 1. 像 Agent 内部一样，先从原始字符串中提取 JSON 块
        json_str = None
        match = re.search(r'\{.*\}', result_raw_string, re.DOTALL)
        if match:
            json_str = match.group(0)
        
        if not json_str:
            print("[Main] 无法从 Agent 的原始输出中找到 {}。正在打印原始文本：")
            print(result_raw_string)
            return

        # 2. 尝试解析 (双重保险)
        parsed_data = None
        try:
            parsed_data = json.loads(json_str) # 尝试 JSON
        except json.JSONDecodeError:
            print("[Main] (非 JSON，尝试 ast.literal_eval...)")
            parsed_data = ast.literal_eval(json_str) # 尝试 Python 字典
        
        # 3. 打印字典中你感兴趣的字段
        #    (print() 会把 "\n" 解释为真正的换行)
        print("--- 📝 详细题解 (Detailed Solution) ---")
        print(parsed_data.get('detailed_solution', '[无题解]'))
        
        print("\n--- 💻 示例代码 (Sample Code) ---")
        print(parsed_data.get('sample_code', '[无代码]'))

        print("\n--- 🔑 关键词 (Keywords) ---")
        keywords = parsed_data.get('keywords', [])
        print(f"[{', '.join(keywords)}]")

    except Exception as e:
        print(f"[Main] 无法解析 Agent 的输出 ({e})。正在打印原始文本：")
        print(result_raw_string) # 回退方案
    
    print("\n--- [Main] ===== 脚本执行完毕 ===== ---")
    return result_raw_string

# 5. 脚本执行入口
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"--- [Main] 脚本顶层捕获到未处理异常 ---")
        traceback.print_exc()