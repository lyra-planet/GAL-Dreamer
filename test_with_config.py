"""
使用配置管理的测试脚本
"""
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from utils.config import config
from utils.logger import log

# 初始化日志
log.info("初始化GAL-Dreamer测试")

# 显示配置信息
log.info(f"使用LLM提供商: {config.LLM_PROVIDER}")
log.info(f"使用模型: {config.LLM_MODEL}")

# 使用配置创建LLM
llm = ChatOpenAI(
    model=config.LLM_MODEL,
    api_key=config.LLM_API_KEY,
    base_url=config.LLM_BASE_URL,
    temperature=config.LLM_TEMPERATURE,
    max_tokens=config.LLM_MAX_TOKENS,
    timeout=config.LLM_TIMEOUT,
)

# 创建prompt
prompt = ChatPromptTemplate.from_messages([
    ("system", ""),
    ("human", "{question}")
])

# 创建链
chain = prompt | llm

# 测试调用
log.info("开始测试LLM调用...")
result = chain.invoke({"question": "你是谁?"})

log.info("LLM响应:")
log.success(result.content)

print("\n" + "="*50)
print(result.content)
print("="*50)
