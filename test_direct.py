"""
直接测试OpenAI API的结构化输出
"""
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("LLM_API_KEY", "sk-167fb3abf53749f6812b685a90cf9169"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

completion = client.chat.completions.create(
    model="qwen-plus",
    messages=[
        {
            "role": "system",
            "content": "你是一位专业的GALGAME策划分析师。请分析用户的故事创意并提取关键信息，必须以JSON格式返回。"
        },
        {
            "role": "user",
            "content": """请分析以下故事创意并提取信息:

一个现代校园背景的故事。主角是一个普通高中生,突然班里来了一个转校生。

请以JSON格式返回,包含:
- genre: 题材
- themes: 主题列表
- tone: 基调
- must_have: 必备元素列表
- forbidden: 禁止元素列表"""
        },
    ],
    response_format={"type": "json_object"}
)

print("LLM响应:")
print(completion.choices[0].message.content)
print("\n" + "="*60)
