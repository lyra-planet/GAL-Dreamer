"""
最小化测试Story Intake Agent
"""
import sys
from pathlib import Path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import os

print("1. 创建LLM...")
llm = ChatOpenAI(
    model="qwen-plus",
    api_key=os.getenv("LLM_API_KEY", "sk-167fb3abf53749f6812b685a90cf9169"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    temperature=0.7,
    model_kwargs={"response_format": {"type": "json_object"}}
)

print("2. 创建prompt...")
system_prompt = """你是一位专业的GALGAME策划分析师。请分析用户的故事创意并提取关键信息，必须以JSON格式返回。

genre必须是单个明确的题材(字符串),不能是列表!
tone必须是单个基调描述(字符串),不能是列表!"""

human_prompt = """请分析以下用户给出的故事创意，并提取关键信息，必须以JSON格式返回。

用户创意:
{user_idea}

请输出JSON格式的分析结果，包含:
- genre: 游戏类型/题材
- themes: 主题列表
- tone: 整体基调
- must_have: 必须包含的元素列表
- forbidden: 禁止的元素列表(如果没有则为空)"""

print("3. 创建ChatPromptTemplate...")
try:
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", human_prompt)
    ])
    print("✓ Prompt创建成功")
except Exception as e:
    print(f"✗ Prompt创建失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("4. 构建chain...")
try:
    chain = prompt | llm
    print("✓ Chain创建成功")
except Exception as e:
    print(f"✗ Chain创建失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("5. 调用LLM...")
try:
    response = chain.invoke({"user_idea": "一个校园恋爱故事"})
    print("✓ LLM调用成功")
    print(f"响应: {response.content[:200]}")
except Exception as e:
    print(f"✗ LLM调用失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n测试完成!")
