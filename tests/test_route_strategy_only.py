"""
只测试 RouteStrategyAgent
"""
import json
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.route_planning.route_strategy_agent import RouteStrategyAgent


def main():
    # 加载故事大纲
    output_dir = Path("./output")
    if not output_dir.exists():
        print("错误: 找不到 output 目录")
        return 1

    # 查找最新的故事大纲
    import re
    timestamp_dirs = [d for d in output_dir.iterdir() if d.is_dir() and re.match(r"\d{8}_\d{6}", d.name)]

    if not timestamp_dirs:
        print("错误: 找不到故事大纲")
        return 1

    latest_dir = sorted(timestamp_dirs)[-1]
    outline_path = latest_dir / "story_outline.json"
    if not outline_path.exists():
        print(f"错误: 找不到故事大纲 {outline_path}")
        return 1

    print(f"使用故事大纲: {outline_path}")

    with open(outline_path, 'r', encoding='utf-8') as f:
        story_outline_data = json.load(f)

    # 加载世界观设定
    world_setting_path = latest_dir / "world_setting.json"
    world_setting_data = None
    if world_setting_path.exists():
        print(f"使用世界观设定: {world_setting_path}")
        with open(world_setting_path, 'r', encoding='utf-8') as f:
            world_setting_data = json.load(f)
    else:
        print(f"警告: 找不到世界观设定 {world_setting_path}")

    print("\n" + "=" * 60)
    print("只运行 RouteStrategyAgent")
    print("=" * 60)

    agent = RouteStrategyAgent()
    result = agent.process(
        story_outline_data=story_outline_data,
        world_setting_data=world_setting_data
    )

    print("\n" + "=" * 60)
    print("RouteStrategyAgent 生成完成!")
    print("=" * 60)

    print(f"\n📋 战略ID: {result.strategy_id}")
    print(f"📋 来源大纲: {result.source_outline}")
    print(f"📋 推荐章节数: {result.recommended_chapters}")
    print(f"📋 女主数量: {result.heroine_count}")
    print(f"📋 主线概要: {result.main_plot_summary}")
    print(f"📋 章节数: {len(result.chapters)}")

    # 显示大冲突
    if result.major_conflicts:
        print("\n" + "=" * 60)
        print("大冲突规划:")
        print("=" * 60)
        for idx, conflict in enumerate(result.major_conflicts, 1):
            print(f"\n【大冲突{idx}】")
            print(f"  ID: {conflict.get('conflict_id', '')}")
            print(f"  名称: {conflict.get('name', '')}")
            print(f"  章节: {conflict.get('position_chapter', '')}")
            print(f"  描述: {conflict.get('description', '')}")

    print("\n" + "=" * 60)
    print("详细章节规划:")
    print("=" * 60)
    for ch in result.chapters:
        print(f"\n=== 第{ch.get('chapter', '?')}章 ({ch.get('id', 'unknown')}) ===")
        print(f"标题: {ch.get('title', '')}")
        print(f"阶段: {ch.get('story_phase', '')}")
        print(f"场景: {ch.get('location', '')}")
        print(f"时间: {ch.get('time_of_day', '')}")
        print(f"人物: {', '.join(ch.get('characters', []))}")
        print(f"目标: {ch.get('goal', '')}")
        print(f"信息: {ch.get('information', '')}")
        print(f"情绪: {ch.get('mood', '')}")
        print(f"事件: {ch.get('event', '')}")
        major_conflict = ch.get('major_conflict')
        if major_conflict:
            print(f"🔥 大冲突: {major_conflict}")

    # 保存结果
    save_dir = latest_dir / "route_strategy"
    save_dir.mkdir(parents=True, exist_ok=True)

    result_file = save_dir / "route_strategy.json"
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(result.model_dump(), f, ensure_ascii=False, indent=2)
    print(f"\n结果已保存到: {result_file}")

    # 单独保存章节规划
    chapters_file = save_dir / "chapters.json"
    with open(chapters_file, 'w', encoding='utf-8') as f:
        json.dump(result.chapters, f, ensure_ascii=False, indent=2)
    print(f"章节规划已保存到: {chapters_file}")

    return 0


if __name__ == "__main__":
    exit(main())
