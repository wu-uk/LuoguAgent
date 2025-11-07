import streamlit as st
import asyncio, sys, subprocess
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
import traceback

# --- 关键导入 ---
# 1. 导入你的 Agent
from analysis_agent import AnalysisAgent

# 2. 导入爬虫依赖（因为爬虫是第一步）
from crawler_agent import LuoguCrawlerAgent
from crawl4ai import AsyncWebCrawler, BrowserConfig
from constant import *


@st.cache_resource
def install_playwright():
    """
    一个只运行一次的函数，用于在 Streamlit Cloud 启动时
    安装 Playwright 所需的浏览器。
    """
    st.write("正在检查和安装 Playwright 浏览器，请稍候...")
    print("--- [Playwright] 正在安装浏览器... ---")
    
    # 我们调用 "python -m playwright install chromium"
    # "sys.executable" 确保我们用的是当前环境的 python
    command = [sys.executable, "-m", "playwright", "install", "chromium"]
    
    try:
        # 运行命令
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True  # 如果命令失败，则抛出异常
        )
        print(f"--- [Playwright] 安装成功: {result.stdout} ---")
        st.write("浏览器安装成功。")
    except subprocess.CalledProcessError as e:
        # 如果安装失败，显示错误并停止应用
        print(f"--- [Playwright] 安装失败: {e.stderr} ---")
        st.error(f"Playwright 浏览器安装失败: {e.stderr}")
        st.stop()
    except FileNotFoundError:
        st.error("无法执行 Playwright 命令。请确保 'playwright' 在 requirements.txt 中。")
        st.stop()

install_playwright()

# -----------------------------------------------------------------
# [1] 侧边栏：获取密钥
# -----------------------------------------------------------------
st.sidebar.title("🔑 配置 API")
st.sidebar.markdown("密钥不会被存储，仅用于当前会话。")

# 使用 type="password" 来隐藏密钥
api_key_input = st.sidebar.text_input(
    "API Key", 
    type="password",
    help="输入你的 API Key (例如 sk-...)"
)

base_url_input = st.sidebar.text_input(
    "Base URL", 
    value="https://www.dmxapi.cn/v1", # 给个默认值
    help="输入你的 API Base URL"
)

# -----------------------------------------------------------------
# 辅助函数：从解析后的字典构建 Markdown
# -----------------------------------------------------------------
def build_markdown_from_data(problem_id: str, data: dict) -> str:
    """
    在前端复刻 Agent 内部的 Markdown 生成逻辑。
    """
    try:
        solution_text = data.get('detailed_solution', 'LLM 未提供详细题解。')
        sample_code = data.get('sample_code', 'LLM 未提供示例代码。')
        keywords = data.get('keywords', [])
        code_lang = "cpp" # 来自你的 schema

        md_content = f"# {problem_id} 详细题解\n\n"
        md_content += f"{solution_text}\n\n"
        md_content += f"# 参考代码 ({code_lang})\n\n"
        md_content += f"```{code_lang}\n{sample_code}\n```\n\n"
        md_content += "# 核心知识点\n\n"
        if keywords:
            for keyword in keywords:
                md_content += f"* {keyword}\n"
        else:
            md_content += "无\n"
        return md_content
    except Exception as e:
        return f"生成 Markdown 时出错: {e}\n\n原始数据: \n```json\n{data}\n```"


# -----------------------------------------------------------------
# Streamlit 界面
# -----------------------------------------------------------------

st.title("🦜🔗 Luogu Agent")

@st.cache_resource
def get_analysis_agent(api_key, base_url):
    print(f"--- [Streamlit] 正在尝试初始化 AnalysisAgent... ---")
    # [!] 把参数传递给修改后的 __init__
    return AnalysisAgent(api_key, base_url)

analysis_agent = None
if api_key_input and base_url_input:
    try:
        analysis_agent = get_analysis_agent(api_key_input, base_url_input)
    except Exception as e:
        st.error(f"🚫 Agent 初始化失败: {e}")
        st.warning("请检查侧边栏的 API Key 和 Base URL 是否正确。")
        st.stop()
else:
    st.info("👈 请在左侧边栏输入 API Key 和 Base URL 来启动应用。")
    st.stop() # 如果没提供密钥，就停在这里，不显示后续界面

# --- 界面 ---
problemid = st.text_input("输入洛谷题目 ID (例如: P1238)", "P1238")

if st.button("🚀 开始分析"):
    if not problemid:
        st.warning("请输入题目 ID")
        st.stop()

    # [!] 核心：这是我们的“舞台”，所有内容都会在这里更新
    placeholder = st.empty()

    raw_crawler_data = {}
    
    # --- 1. 爬虫 (处理异步) ---
    try:
        with st.status(f"🔍 正在爬取 {problemid} 题目和题解...", expanded=True) as status:
            brouser_config = BrowserConfig(headless=True, proxy=None)
            
            async def crawl_main():
                async with AsyncWebCrawler(config=brouser_config) as crawler:
                    agent = LuoguCrawlerAgent(api_key_input, base_url_input, crawler, cache_dir=CACHE_DIR)
                    st.write(f"正在抓取 {problemid}...")
                    data = await agent.run(problemid, max_solutions=3)
                    st.write("✅ 抓取完成")
                    return data
            
            # 在同步的 Streamlit 回调中运行异步爬虫
            raw_crawler_data = asyncio.run(crawl_main()) 
            status.update(label="爬取成功!", state="complete")
            
    except Exception as e:
        placeholder.error(f"爬虫阶段失败: {e}")
        traceback.print_exc() # 打印到终端
        st.stop()
        
    # --- 2. 检查爬虫数据 ---
    problem_data = raw_crawler_data.get("problem", {})
    solutions_data = raw_crawler_data.get("solutions", [])
    if "error" in problem_data or not problem_data:
        placeholder.error(f"爬虫未获取到有效数据: {problem_data.get('error', '未知错误')}")
        st.stop()

    # --- 3. 构建提示 & 调用 LLM (流式) ---
    placeholder.info("🧠 正在调用 LLM...")
    
    try:
        # [!] 调用 Agent 的“零件”
        system_prompt, user_prompt = analysis_agent._build_prompts(problem_data, solutions_data)
        
        # [!] 直接访问 agent 的 llm 属性来获取流
        stream = analysis_agent.llm.chat.completions.create(
            model="glm-4.6", 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            thinking={"type": "disabled"},
            stream=True
        )

        full_content = ""
        stream_display = "" # 这是流式展示给用户的
        
        # [!] 核心：实时更新占位符，显示原始输出
        for chunk in stream:
            if not chunk.choices: continue
            delta = chunk.choices[0].delta
            if hasattr(delta, 'content') and delta.content:
                full_content += delta.content
                stream_display += delta.content
                # 用 .code() 来显示原始的、正在生成的 JSON 字符串
                placeholder.code(stream_display + "▌", language="json")
        
        # 流式结束，显示完整 JSON
        placeholder.code(full_content, language="json")
        st.success("✅ LLM 流式响应接收完毕")

    except Exception as e:
        placeholder.error(f"LLM 调用失败: {e}")
        traceback.print_exc()
        st.stop()

    # --- 4. 解析 & 覆盖 ---
    with st.spinner("正在解析结果并生成报告..."):
        # [!] 复用 Agent 的解析和提取“零件”
        extracted_str = analysis_agent._extract_json_string(full_content)
        parsed_data = analysis_agent._parse_to_dict(extracted_str)
        
        if parsed_data:
            # [!] 用我们前端的辅助函数生成 Markdown
            final_md = build_markdown_from_data(problemid, parsed_data)
            
            # [!] 关键：用 Markdown 覆盖掉 placeholder 里的 code
            placeholder.markdown(final_md)
            
            # (可选) 既然 Agent 有保存功能，我们也帮它调用一下
            try:
                analysis_agent._save_json_result(problemid, parsed_data)
                analysis_agent._save_markdown_result(problemid, parsed_data)
            except Exception as e:
                st.warning(f"保存文件时出错 (但不影响显示): {e}")
        
        else:
            # 解析失败
            st.error("❌ 无法解析 LLM 的 JSON 响应。")
            analysis_agent._save_error(problemid, full_content)
            # 此时 placeholder 里仍然显示的是完整的原始 JSON，方便调试