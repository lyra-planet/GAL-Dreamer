"""
JSON工具函数
处理JSON格式转换和验证
"""
import json
from typing import Any, Dict, Type, TypeVar
from pydantic import BaseModel, ValidationError
from utils.logger import log

T = TypeVar('T', bound=BaseModel)


def safe_parse_json(json_str: str) -> Dict[str, Any]:
    """
    安全解析JSON,处理常见错误

    Args:
        json_str: JSON字符串

    Returns:
        解析后的字典,失败返回空字典
    """
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        log.error(f"JSON解析失败: {e}")
        return {}


def validate_and_convert(data: Dict[str, Any], model_class: Type[T]) -> T:
    """
    验证数据并转换为Pydantic模型

    Args:
        data: 原始数据字典
        model_class: 目标Pydantic模型类

    Returns:
        模型实例

    Raises:
        ValueError: 验证失败
    """
    try:
        # 尝试直接转换
        return model_class(**data)
    except ValidationError as e:
        log.error(f"模型验证失败: {e}")
        log.error(f"错误详情: {e.errors()}")
        log.info(f"原始数据: {data}")

        # 尝试修复常见问题
        fixed_data = _try_fix_common_issues(data, model_class)
        if fixed_data:
            try:
                return model_class(**fixed_data)
            except ValidationError:
                pass

        # 如果修复失败,抛出原始错误
        raise ValueError(f"数据验证失败: {e}")


def _try_fix_common_issues(data: Dict[str, Any], model_class: Type[T]) -> Dict[str, Any]:
    """
    尝试修复常见的数据问题

    Args:
        data: 原始数据
        model_class: 目标模型类

    Returns:
        修复后的数据,失败返回None
    """
    if not data:
        return None

    fixed = data.copy()

    # 获取模型的字段定义
    if hasattr(model_class, '__annotations__'):
        annotations = model_class.__annotations__

        # 处理可选字段
        for field, field_type in annotations.items():
            if field not in fixed or fixed[field] is None:
                # 检查是否是Optional类型
                if hasattr(field_type, '__origin__') and field_type.__origin__ is Union:
                    fixed[field] = None
                elif field_type == str:
                    fixed[field] = ""
                elif field_type == int:
                    fixed[field] = 0
                elif field_type == float:
                    fixed[field] = 0.0
                elif hasattr(field_type, '__origin__') and field_type.__origin__ is list:
                    fixed[field] = []

    return fixed if fixed != data else None


def merge_json(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    合并两个JSON字典

    Args:
        base: 基础字典
        override: 覆盖字典

    Returns:
        合并后的字典
    """
    result = base.copy()
    result.update(override)
    return result
