"""
测试LangChain的结构化输出
"""
import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

llm = ChatOpenAI(
    model="qwen-plus",
    api_key=os.getenv("LLM_API_KEY", "sk-167fb3abf53749f6812b685a90cf9169"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    temperature=0.7,
    model_kwargs={
        "response_format": {"type": "json_object"}
    }
)

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一位专业的GALGAME策划分析师。请分析用户的故事创意并提取关键信息，必须以JSON格式返回。"),
    ("human", "请分析以下故事创意:一个现代校园背景的故事。请以JSON格式返回genre、themes、tone等字段。")
])

try:
    chain = prompt | llm
    response = chain.invoke({})
    print("成功!")
    print(f"响应类型: {type(response.content)}")
    print(f"响应内容:\n{response.content}")
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
