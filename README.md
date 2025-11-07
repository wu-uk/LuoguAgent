# LuoguAgent

面向Luogu平台的算法竞赛辅导Agent，通过url自动爬取题目、题解并进行辅导。

针对本项目是如何构建的，我在[博客文章](https://www.google.com/search?q=https://wu-uk.github.io/wuuuk/project/LuoguAgent/index)中有详细介绍。

## ✨ 功能特性

  * **题目爬取:** 输入洛谷题目 URL，自动抓取题目正文、输入输出、样例数据。
  * **题解分析:** 自动爬取该题目的现有题解，并将其提交给 LLM（大语言模型）进行分析。
  * **智能辅导:** LLM 基于对题目和现有题解的分析，生成一份更详细、更具启发性的全新题解和代码实现。
  * **Web 界面:** 使用 Streamlit 搭建的交互式前端，方便输入 URL 并查看结果。

## 🛠️ 技术栈

  * **核心:** Python 3.12
  * **前端:** Streamlit
  * **爬虫:** crawl4ai
  * **LLM / Agent:** glm-4.6, deepseek-chat

## ⚡云端体验

点击链接即可直接访问[LuoguAgent](https://luoguagent.streamlit.app/)!

## 🚀 本地部署

### 1\. 克隆仓库

```bash
git clone https://github.com/你的用户名/LuoguAgent.git
cd LuoguAgent
```

### 2\. 安装依赖

建议使用虚拟环境。

```bash
# (可选) 创建并激活虚拟环境
python -m venv venv
source venv/bin/activate  # on Windows, use `venv\Scripts\activate`

# 安装所有必需的库
pip install -r requirements.txt
```

### 3\. 配置环境变量(可选)

> 目前api_key和base_url从前端输入，不需要配置！

在项目根目录（与 `app.py` 同级）创建一个 `.env` 文件。这是你的 `constant.py` 脚本加载 API 密钥的地方。

```shell
# .env
ZHIPU_API_KEY=sk-你的智谱API密钥
DMX_API_KEY=你的DMX-API密钥
```

### 4\. 运行应用

确保你在项目根目录。

```bash
streamlit run app.py
```

启动后，在浏览器中打开 `http://localhost:8501` 即可开始使用。

## 📂 项目结构

```
.
├── .env                # (你需要自己创建) 存放 API 密钥
├── .gitignore
├── app.py              # 👈 Streamlit 应用入口
├── requirements.txt    # 依赖列表
├── packages.txt        # 给 streamlit cloud 使用的所需依赖
│
├── luogu_agent/        # 📦 核心逻辑包
│   ├── __init__.py
│   ├── analysis.py     # 分析 Agent (LLM)
│   ├── crawler.py      # 爬虫 Agent
│   │
│   └── core/           # 🧬 核心定义 (配置、数据结构)
│       ├── __init__.py
│       ├── constant.py   # 常量
│       ├── prompts.py    # 提示词
│       ├── schema.py     # Pydantic 数据模型
│       └── strategy.py   # 爬虫解析策略
│
├── tests/              # 🧪 测试脚本
│   ├── test_agent.ipynb
│   └── ...
│
├── luogu_cache/        # (自动生成) 爬虫缓存
└── analysis_cache/     # (自动生成) 分析缓存
```

## 📄 许可证

本项目采用 [MIT](https://github.com/wu-uk/LuoguAgent/blob/main/LICENSE) 许可证。