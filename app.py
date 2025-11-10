import streamlit as st
import asyncio, sys, subprocess

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
import traceback

from crawl4ai import AsyncWebCrawler, BrowserConfig

from luogu_agent.crawler import LuoguCrawlerAgent
from luogu_agent.analysist import AnalysisAgent
from luogu_agent.core.constant import *
from compare_agent.compare import CompareAgent


@st.cache_resource
def install_playwright():
    """
    一个只运行一次的函数,用于在 Streamlit Cloud 启动时
    安装 Playwright 所需的浏览器。
    """
    print("--- [Playwright] 正在安装浏览器... ---")

    command = [sys.executable, "-m", "playwright", "install", "chromium"]

    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        print(f"--- [Playwright] 安装成功: {result.stdout} ---")
    except subprocess.CalledProcessError as e:
        print(f"--- [Playwright] 安装失败: {e.stderr} ---")
        st.error(f"Playwright 浏览器安装失败: {e.stderr}")
        st.stop()
    except FileNotFoundError:
        st.error("无法执行 Playwright 命令。请确保 'playwright' 在 requirements.txt 中。")
        st.stop()


install_playwright()

# -----------------------------------------------------------------
# [1] 侧边栏：获取密钥和页面选择
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
    value="https://www.dmxapi.cn/v1",
    help="输入你的 API Base URL"
)

st.sidebar.markdown("---")
st.sidebar.title("📑 功能选择")
page = st.sidebar.radio(
    "选择功能",
    ["题解分析", "自动对拍"],
    index=0
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
        code_lang = "cpp"

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
# 初始化 Agent
# -----------------------------------------------------------------
@st.cache_resource
def get_analysis_agent(api_key, base_url):
    print(f"--- [Streamlit] 正在尝试初始化 AnalysisAgent... ---")
    return AnalysisAgent(api_key, base_url)


@st.cache_resource
def get_compare_agent(api_key):
    print(f"--- [Streamlit] 正在尝试初始化 CompareAgent... ---")
    return CompareAgent(api_key)


# -----------------------------------------------------------------
# 页面1：题解分析功能（原有功能）
# -----------------------------------------------------------------
if page == "题解分析":
    st.title("🦜🔗 Luogu Agent - 题解分析")

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
        st.stop()

    problemid = st.text_input("输入洛谷题目 ID (例如: P1238)", "P1238")

    if st.button("🚀 开始分析"):
        if not problemid:
            st.warning("请输入题目 ID")
            st.stop()

        placeholder = st.empty()
        raw_crawler_data = {}

        # 爬虫阶段
        try:
            with st.status(f"🔍 正在爬取 {problemid} 题目和题解...", expanded=True) as status:
                brouser_config = BrowserConfig(headless=True, proxy=None)


                async def crawl_main():
                    async with AsyncWebCrawler(config=brouser_config) as crawler:
                        agent = LuoguCrawlerAgent(api_key_input, base_url_input, crawler, cache_dir=CACHE_DIR)
                        st.write(f"正在抓取 {problemid}...(第一次抓取可能需要较长的时间⏳)")
                        data = await agent.run(problemid, max_solutions=3)
                        st.write("✅ 抓取完成")
                        return data


                raw_crawler_data = asyncio.run(crawl_main())
                status.update(label="爬取成功!", state="complete")

        except Exception as e:
            placeholder.error(f"爬虫阶段失败: {e}")
            traceback.print_exc()
            st.stop()

        # 检查爬虫数据
        problem_data = raw_crawler_data.get("problem", {})
        solutions_data = raw_crawler_data.get("solutions", [])
        if "error" in problem_data or not problem_data:
            placeholder.error(f"爬虫未获取到有效数据: {problem_data.get('error', '未知错误')}")
            st.stop()

        # 调用 LLM (流式)
        placeholder.info("🧠 正在调用 LLM...")

        try:
            system_prompt, user_prompt = analysis_agent._build_prompts(problem_data, solutions_data)

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
            stream_display = ""

            for chunk in stream:
                if not chunk.choices: continue
                delta = chunk.choices[0].delta
                if hasattr(delta, 'content') and delta.content:
                    full_content += delta.content
                    stream_display += delta.content
                    placeholder.write(stream_display + "▌")

            placeholder.code(full_content, language="json")
            st.success("✅ LLM 流式响应接收完毕")

        except Exception as e:
            placeholder.error(f"LLM 调用失败: {e}")
            traceback.print_exc()
            st.stop()

        # 解析并覆盖显示
        with st.spinner("正在解析结果并生成报告..."):
            extracted_str = analysis_agent._extract_json_string(full_content)
            parsed_data = analysis_agent._parse_to_dict(extracted_str)

            if parsed_data:
                final_md = build_markdown_from_data(problemid, parsed_data)
                placeholder.markdown(final_md)

                try:
                    analysis_agent._save_json_result(problemid, parsed_data)
                    analysis_agent._save_markdown_result(problemid, parsed_data)
                except Exception as e:
                    st.warning(f"保存文件时出错 (但不影响显示): {e}")

            else:
                st.error("❌ 无法解析 LLM 的 JSON 响应。")
                analysis_agent._save_error(problemid, full_content)


# -----------------------------------------------------------------
# 页面2：自动对拍功能
# -----------------------------------------------------------------
elif page == "自动对拍":
    st.title("🎯 Luogu Agent - 自动对拍")

    # 检查必要的 API Keys
    if not (api_key_input and base_url_input):
        st.info("👈 请在左侧边栏输入 API Key 和 Base URL 来启动爬虫功能。")
        st.stop()


    # 初始化 CompareAgent
    try:
        compare_agent = get_compare_agent(api_key_input)
    except Exception as e:
        st.error(f"🚫 CompareAgent 初始化失败: {e}")
        st.stop()

    st.markdown("""
    ### 使用说明
    1. 输入洛谷题目 ID
    2. 粘贴你的代码（待对拍代码）
    3. 点击"开始对拍"按钮
    4. 系统将自动：
       - 爬取题目描述和标准代码
       - 推理差异样例
       - 分析错误原因
    """)

    problemid = st.text_input("输入洛谷题目 ID (例如: P1001)", "P1001", key="compare_problemid")

    user_code = st.text_area(
        "粘贴你的代码 (C++)",
        height=300,
        placeholder="""#include <iostream>
using namespace std;
int main() {
    int a, b;
    cin >> a >> b;
    cout << a + b << endl;
    return 0;
}""",
        key="user_code"
    )

    if st.button("🎯 开始对拍", key="start_compare"):
        if not problemid:
            st.warning("请输入题目 ID")
            st.stop()

        if not user_code.strip():
            st.warning("请输入你的代码")
            st.stop()

        # 创建两个占位符，用于显示不同阶段的结果
        crawl_placeholder = st.empty()
        result_placeholder = st.empty()

        raw_crawler_data = {}

        # 阶段1：爬虫获取题目和标准代码
        try:
            with st.status(f"🔍 正在爬取 {problemid} 题目和题解...", expanded=True) as status:
                brouser_config = BrowserConfig(headless=True, proxy=None)


                async def crawl_main():
                    async with AsyncWebCrawler(config=brouser_config) as crawler:
                        agent = LuoguCrawlerAgent(api_key_input, base_url_input, crawler, cache_dir=CACHE_DIR)
                        st.write(f"正在抓取 {problemid}...(第一次抓取可能需要较长的时间⏳)")
                        data = await agent.run(problemid, max_solutions=1)  # 只需要一个题解即可
                        st.write("✅ 抓取完成")
                        return data


                raw_crawler_data = asyncio.run(crawl_main())
                status.update(label="爬取成功!", state="complete")

        except Exception as e:
            crawl_placeholder.error(f"爬虫阶段失败: {e}")
            traceback.print_exc()
            st.stop()

        # 检查爬虫数据
        problem_data = raw_crawler_data.get("problem", {})
        solutions_data = raw_crawler_data.get("solutions", [])

        print('===================solution_dat================')
        print(solutions_data)

        if "error" in problem_data or not problem_data:
            crawl_placeholder.error(f"爬虫未获取到有效数据: {problem_data.get('error', '未知错误')}")
            st.stop()

        if not solutions_data or len(solutions_data) == 0:
            crawl_placeholder.error("未找到题解，无法获取标准代码")
            st.stop()

        # 提取标准代码
        std_code = solutions_data[0].get('code', '')

        if not std_code:
            crawl_placeholder.error("题解中未找到可用的代码")
            st.stop()

        crawl_placeholder.success(f"✅ 成功获取题目和标准代码")

        # 显示爬取到的信息
        with st.expander("📋 查看爬取到的题目信息"):
            st.markdown(f"**题目背景:** {problem_data.get('background', '无')}")
            st.markdown(f"**题目描述:** {problem_data.get('description', '无')[:200]}...")
            st.markdown(f"**输入格式:** {problem_data.get('input_format', '无')}")
            st.markdown(f"**输出格式:** {problem_data.get('output_format', '无')}")

        with st.expander("💻 查看标准代码"):
            st.code(std_code, language="cpp")

        # 阶段2：调用 CompareAgent 进行对拍
        result_placeholder.info("🧠 正在进行智能对拍分析...")

        try:
            with st.spinner("LLM 正在分析中..."):
                compare_result = compare_agent.run(
                    problem=problem_data,
                    std=std_code,
                    test=user_code
                )

            result_placeholder.success("✅ 对拍分析完成！")

            # 显示对拍结果
            st.markdown("---")
            st.markdown("## 📊 对拍结果")

            # 差异样例
            st.markdown("### 🔍 差异样例")
            with st.container():
                st.markdown(compare_result.get("diff_result", "[无结果]"))

            st.markdown("---")

            # 错误分析
            st.markdown("### 🧩 错误分析与修改建议")
            with st.container():
                st.markdown(compare_result.get("analysis", "[分析失败]"))

        except Exception as e:
            result_placeholder.error(f"对拍分析失败: {e}")
            traceback.print_exc()
            st.stop()