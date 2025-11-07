import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from luogu_agent.core.constant import DMX_API_KEY, ZHIPU_API_KEY, DMX_BASE_URL, ZHIPU_BASE_URL

API_KEY = DMX_API_KEY
BASE_URL = DMX_BASE_URL
print(API_KEY[:4])

try:
    llm = ChatOpenAI(
        model="glm-4.6",
        api_key=API_KEY,           # 显式传入 Key
        base_url=BASE_URL, # 显式传入 DMX URL
        temperature=0.1
    )

    response = llm.invoke([
        HumanMessage(content="你好，请说'测试成功'。")
    ])
        
    print(response.content)

except Exception as e:
    print(f"异常类型: {type(e)}")
    print(f"异常信息: {e}")
