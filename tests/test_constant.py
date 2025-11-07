import sys, os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

print(f"PYTHONPATH 已临时设置为: {project_root}\n")

try:
    from luogu_agent.core import constant

    print("--- 🚀 开始测试 constant.py ---")

    print(f"\n[路径检查]")
    print(f"PROJECT_ROOT: {constant.PROJECT_ROOT}")
    print(f"CACHE_DIR: {constant.CACHE_DIR}")
    print(f"ANALYSIS_CACHE_DIR: {constant.ANALYSIS_CACHE_DIR}")

    # 检查路径是否存在 (可选，但推荐)
    print(f"CACHE_DIR 是否存在? {os.path.isdir(constant.CACHE_DIR)}")
    print(f"ANALYSIS_CACHE_DIR 是否存在? {os.path.isdir(constant.ANALYSIS_CACHE_DIR)}")

    print(f"\n[API 密钥加载检查]")
    # 为了安全，我们不打印密钥本身，只检查它是否被加载
    print(f"ZHIPU_API_KEY 是否加载? {bool(constant.ZHIPU_API_KEY)}")
    print(f"DMX_API_KEY 是否加载? {bool(constant.DMX_API_KEY)}")

    if not constant.ZHIPU_API_KEY:
        print("⚠️ 警告: ZHIPU_API_KEY 未从 .env 加载!")

    print("\n--- ✅ 测试完毕 ---")

except ImportError as e:
    print(f"--- ❌ 导入失败 ---")
    print(f"出错了: {e}")
    print("请确保你是从项目根目录运行此脚本，或者 check_config.py 里的 sys.path 设置正确。")

except Exception as e:
    print(f"--- ❌ 发生意外错误 ---")
    print(f"{e}")