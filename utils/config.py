"""
配置管理模块
从环境变量和.env文件加载配置
"""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()


class Config:
    """配置类"""

    # ================================
    # LLM 配置
    # ================================
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "qwen")
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_BASE_URL: str = os.getenv(
        "LLM_BASE_URL",
        "https://dashscope.aliyuncs.com/compatible-mode/v1"
    )
    LLM_MODEL: str = os.getenv("LLM_MODEL", "qwen-plus")
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "4000"))
    LLM_TIMEOUT: int = int(os.getenv("LLM_TIMEOUT", "120"))

    # ================================
    # 项目配置
    # ================================
    PROJECT_OUTPUT_DIR: Path = Path(os.getenv("PROJECT_OUTPUT_DIR", "./output"))
    PROJECT_TEMP_DIR: Path = Path(os.getenv("PROJECT_TEMP_DIR", "./temp"))
    PROJECT_LOG_DIR: Path = Path(os.getenv("PROJECT_LOG_DIR", "./logs"))

    # ================================
    # 日志配置
    # ================================
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: Path = Path(os.getenv("LOG_FILE", "logs/gal_dreamer.log"))
    LOG_CONSOLE: bool = os.getenv("LOG_CONSOLE", "true").lower() == "true"

    # ================================
    # 开发模式
    # ================================
    DEV_MODE: bool = os.getenv("DEV_MODE", "false").lower() == "true"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    VERBOSE: bool = os.getenv("VERBOSE", "true").lower() == "true"

    @classmethod
    def validate(cls) -> bool:
        """验证配置是否有效"""
        errors = []

        # 检查必填项
        if not cls.LLM_API_KEY:
            errors.append("LLM_API_KEY is required")

        if cls.LLM_PROVIDER == "openai" and not cls.LLM_API_KEY:
            errors.append("OpenAI API key is required when LLM_PROVIDER is 'openai'")

        # 创建必要的目录
        cls.PROJECT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        cls.PROJECT_TEMP_DIR.mkdir(parents=True, exist_ok=True)
        cls.PROJECT_LOG_DIR.mkdir(parents=True, exist_ok=True)

        if errors:
            raise ValueError("Configuration errors:\n" + "\n".join(errors))

        return True

    @classmethod
    def display(cls) -> str:
        """显示配置信息(隐藏敏感信息)"""
        info = f"""
===============================
GAL-Dreamer 配置信息
===============================

LLM配置:
  提供商: {cls.LLM_PROVIDER}
  模型: {cls.LLM_MODEL}
  API Key: {'*' * 10 + cls.LLM_API_KEY[-4:] if cls.LLM_API_KEY else '未设置'}
  Base URL: {cls.LLM_BASE_URL}
  温度: {cls.LLM_TEMPERATURE}

项目配置:
  输出目录: {cls.PROJECT_OUTPUT_DIR}
  临时目录: {cls.PROJECT_TEMP_DIR}
  日志目录: {cls.PROJECT_LOG_DIR}

日志配置:
  级别: {cls.LOG_LEVEL}
  文件: {cls.LOG_FILE}
  控制台输出: {cls.LOG_CONSOLE}

开发模式:
  开发模式: {cls.DEV_MODE}
  调试模式: {cls.DEBUG}
  详细输出: {cls.VERBOSE}
===============================
        """
        return info


# 创建全局配置实例
config = Config()


if __name__ == "__main__":
    # 验证配置
    try:
        config.validate()
        print("✓ 配置验证通过")
    except ValueError as e:
        print(f"✗ 配置错误:\n{e}")

    # 显示配置
    print(config.display())
