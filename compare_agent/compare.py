from openai import OpenAI, api_key
import textwrap
import traceback


class _CompareAgent:
    """
    AI 驱动的自动对拍智能体。
    功能：
      - 根据题目、标准代码、用户代码推理差异样例
      - 分析逻辑错误与修复建议
    """

    def __init__(self, api_key=None, base_url=None, model="glm-4.6"):
        """
        初始化对拍智能体

        Args:
            api_key: API密钥
            base_url: API基础URL，默认使用智谱AI
            model: 使用的模型名称
        """
        # 如果没有指定 base_url，使用默认的智谱AI地址
        if base_url is None:
            base_url = "https://www.dmxapi.cn/v1"

        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    def _ask(self, prompt: str, temperature: float = 0.5):
        """安全调用 LLM，并自动捕获错误"""
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            print("❌ LLM 调用失败：", e)
            traceback.print_exc()
            return f"[LLM 调用失败] {e}"

    # ========== ① 虚拟对拍（生成差异样例） ==========
    def virtual_diff(self, problem_text: str, std: str, test: str):
        prompt = textwrap.dedent(f"""
        你是一名算法竞赛评测专家。
        现在有一份题目、一个参考正确程序（std），以及一个可能有错误的用户程序（test）。
        请推理出一个输入样例，使得两者输出不同。
        如果找不到差异，也请推理出可能出现问题的边界输入。

        ---
        【题目描述】
        {problem_text}

        【参考正确程序 (std)】
        ```cpp
        {std}
        ```

        【用户程序 (test)】
        ```cpp
        {test}
        ```

        ---
        请输出以下四部分内容：
        【触发错误的输入】
        <输入文本>

        【参考程序输出】
        <正确输出>

        【用户程序输出】
        <错误输出>

        【推理说明】
        说明为什么这个输入会触发不同的输出。
        """)
        return self._ask(prompt, temperature=0.6)

    # ========== ② 错误分析（逻辑诊断） ==========
    def analyze_error(self, problem_text: str, std: str, test: str, diff_result: str):
        prompt = textwrap.dedent(f"""
        你是一名算法竞赛辅导教练。
        根据以下题目描述、参考代码、用户代码，以及推理出的错误样例，
        分析用户程序可能的错误原因，并提供简洁的修改建议。

        ---
        【题目描述】
        {problem_text}

        【参考程序 (标准实现)】
        ```cpp
        {std}
        ```

        【用户程序 (错误实现)】
        ```cpp
        {test}
        ```

        【LLM 推理出的对拍差异】
        {diff_result}

        ---
        请输出以下格式：
        【错误分析】
        ...
        【修改建议】
        ...
        【输入特征】
        ...
        """)
        return self._ask(prompt, temperature=0.5)

    # ========== ③ 一键执行全流程 ==========
    def auto_judge(self, problem_text, std, test):
        # 自动将题目转成字符串
        problem_text = str(problem_text)

        print("🧩 Step 1: 正在推理差异输入样例...")
        diff = self.virtual_diff(problem_text, std, test)

        print("\n✅ Step 2: 差异样例推理完成，正在分析错误逻辑...\n")
        analysis = self.analyze_error(problem_text, std, test, diff)

        return {
            "diff_result": diff or "[无结果]",
            "analysis": analysis or "[分析失败]"
        }


class CompareAgent:
    """
    外层封装，用于在 Streamlit / Flask / CLI 中直接调用。
    """

    def __init__(self, api_key, base_url=None):
        """
        初始化 CompareAgent

        Args:
            api_key: API密钥
            base_url: API基础URL（可选）
        """
        self.agent = _CompareAgent(api_key=api_key, base_url=base_url, model="glm-4.6")

    def run(self, problem, std, test):
        # 兼容 Luogu 爬虫的 dict 结构，补齐字段防止 Pydantic 验证错误
        if isinstance(problem, dict):
            for key in ["background", "description", "input_format", "output_format", "examples", "notes"]:
                problem.setdefault(key, "")
        return self.agent.auto_judge(problem, std, test)


# ================= 测试入口（可直接运行） =================
if __name__ == "__main__":
    # api_key = input("请输入 API Key: ").strip()
    # base_url = input("请输入 Base URL (直接回车使用默认): ").strip()
    #
    # if not base_url:
    #     base_url = "https://www.dmxapi.cn/v1"
    api_key = 'sk-T98AY3wQEEgKxgjtlMbt2tt569gp8tqmZl5dNleYv25YTC7R'
    base_url = 'https://www.dmxapi.cn/v1'
    cmp = CompareAgent(api_key, base_url)

    problem = """
    ## 题目描述
    输入两个整数 a, b，输出它们的和。
    ## 输入格式
    两个整数，以空格分隔。
    ## 输出格式
    输出它们的和。
    """

    std = """
    #include <iostream>
    using namespace std;
    int main() {
        int a, b;
        cin >> a >> b;
        cout << a + b << endl;
        return 0;
    }
    """

    test = """
    #include <iostream>
    using namespace std;
    int main() {
        short a, b;
        cin >> a >> b;
        cout << a - b << endl;
        return 0;
    }
    """

    result = cmp.run(problem, std, test)
    print("\n==================== 差异样例 ====================")
    print(result["diff_result"])
    print("\n==================== 错误分析 ====================")
    print(result["analysis"])