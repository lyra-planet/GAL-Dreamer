#!/usr/bin/env python3
"""
模块化主线规划测试脚本
快速测试四模块生成流程
"""
import json
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipelines.route_planning.modular_main_route_pipeline import ModularMainRoutePipeline


def load_latest_story_outline():
    """加载最新的故事大纲"""
    output_dir = Path("./output")
    if not output_dir.exists():
        return None

    import re
    timestamp_dirs = [
        d for d in output_dir.iterdir()
        if d.is_dir() and re.match(r"\d{8}_\d{6}", d.name)
    ]

    if not timestamp_dirs:
        return None

    latest_dir = sorted(timestamp_dirs)[-1]
    outline_path = latest_dir / "story_outline.json"

    if outline_path.exists():
        print(f"✓ 找到故事大纲: {outline_path}")
        with open(outline_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    return None


def create_minimal_test_outline():
    """创建最小测试用故事大纲"""
    return {
        "structure_id": "test_minimal_001",
        "input": {
            "user_idea": """
            故事背景：现代都市校园
            主角：一名转校生
            主要角色：
            - 女主A（雪乃）：校园偶像，外表开朗但内心孤独
            - 女主B（文香）：文学社社长，安静内向，喜欢推理小说
            - 女主C（葵）：运动健将，直率热情
            核心冲突：主角发现每个人都有秘密，需要用真心去了解
            """
        },
        "steps": {
            "premise": {
                "premise_id": "test_premise",
                "genre": "现代校园恋爱",
                "theme": "理解与共鸣",
                "core_conflict": "揭开每个人的秘密"
            },
            "cast_arc": {
                "heroines": [
                    {"id": "heroine_001", "name": "雪乃", "archetype": "外表开朗内心孤独"},
                    {"id": "heroine_002", "name": "文香", "archetype": "安静内向"},
                    {"id": "heroine_003", "name": "葵", "archetype": "直率热情"}
                ]
            },
            "conflict_engine": {
                "map": {"conflict_map_id": "test_conflict_map"}
            }
        }
    }


def print_summary(result):
    """打印结果摘要"""
    print("\n" + "=" * 60)
    print("📊 生成结果摘要")
    print("=" * 60)

    final = result.get("final_output", {})

    print(f"\n结构ID: {final.get('structure_id', 'N/A')}")
    print(f"预计总章节: {final.get('total_estimated_chapters', 0)}章")
    print(f"共通线占比: {final.get('common_ratio', 0) * 100:.0f}%")
    print(f"\n实际生成:")
    print(f"  章节数: {len(final.get('chapters', []))}")
    print(f"  分支数: {len(final.get('branches', []))}")
    print(f"  结局数: {len(final.get('endings', []))}")

    # 各模块统计
    print(f"\n各模块统计:")
    for module_name, framework in result.get("module_frameworks", {}).items():
        chapters = len(framework.get('chapters', []))
        branches = len(framework.get('branches', []))
        endings = len(framework.get('endings', []))
        print(f"  {module_name}模块: {chapters}章, {branches}分支, {endings}结局")


def main():
    """主测试函数"""
    print("=" * 60)
    print("GAL-Dreamer 模块化主线规划测试")
    print("=" * 60)

    # 尝试加载现有故事大纲
    story_outline_data = load_latest_story_outline()

    if not story_outline_data:
        print("\n⚠️ 未找到现有故事大纲，使用测试数据")
        story_outline_data = create_minimal_test_outline()

    # 初始化 Pipeline
    print("\n初始化 ModularMainRoutePipeline...")
    pipeline = ModularMainRoutePipeline()

    # 运行生成
    print("\n开始生成主线框架...")
    print("-" * 60)

    result = pipeline.generate(
        story_outline_data=story_outline_data,
        total_chapters=27,
        output_dir="./output/modular_main_route_test"
    )

    # 打印摘要
    print_summary(result)

    print("\n" + "=" * 60)
    print("✅ 测试完成!")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    try:
        exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断")
        exit(1)
    except Exception as e:
        print(f"\n\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
