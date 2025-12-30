"""
测试 MainRouteAgent - 根据策略文本生成主线章节
"""
import json
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.route_planning.main_route_agent import MainRouteAgent
from agents.route_planning.main_route_fixer_agent import MainRouteFixerAgent
from agents.route_planning.route_consistency_agent import RouteConsistencyAgent


def load_story_outline():
    """加载故事大纲数据"""
    story_outline_path = "/Users/lyra/Desktop/GAL-Dreamer/output/20251230_050843/story_outline.json"

    if not Path(story_outline_path).exists():
        print(f"错误: {story_outline_path} 不存在")
        return None

    print(f"加载故事大纲: {story_outline_path}")
    with open(story_outline_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_strategy_text():
    """加载路线战略文本"""
    strategy_path = "/Users/lyra/Desktop/GAL-Dreamer/output/route_strategy_test/route_strategy.txt"

    if not Path(strategy_path).exists():
        print(f"错误: {strategy_path} 不存在")
        return None

    print(f"加载路线战略: {strategy_path}")
    with open(strategy_path, 'r', encoding='utf-8') as f:
        content = f.read()
        # 跳过前两行（战略ID和来源大纲），只取策略文本
        lines = content.split('\n')
        if len(lines) > 2:
            return '\n'.join(lines[2:])
        return content


def test_main_route_with_strategy(use_regeneration: bool = False):
    """测试 MainRouteAgent 根据策略文本生成主线

    Args:
        use_regeneration: 是否使用重新生成模式（修复问题时重新生成而非直接修复）

    Returns:
        dict: 包含原始结果、修复后结果、检查报告、修复历史的字典
        None: 测试失败
    """
    print("\n" + "=" * 60)
    print("MainRouteAgent 测试 - 根据策略文本生成主线")
    print("=" * 60)

    story_outline = load_story_outline()
    if not story_outline:
        return None

    strategy_text = load_strategy_text()
    if not strategy_text:
        return None

    user_idea = story_outline.get("input", {}).get("user_idea", "")
    print(f"\n原始创意: {user_idea[:100]}...")
    print(f"策略文本长度: {len(strategy_text)} 字符")

    # 初始化输出目录
    output_dir = project_root / "output" / "main_route_test"
    output_dir.mkdir(parents=True, exist_ok=True)

    # 初始化返回结果
    test_result = {
        "original_route": None,
        "final_route": None,
        "initial_report": None,
        "final_report": None,
        "fix_history": [],
        "output_dir": str(output_dir)
    }

    # 根据策略文本生成主线
    print("\n" + "=" * 60)
    print("生成主线章节...")
    print("=" * 60)

    main_route_agent = MainRouteAgent()

    # 初始化返回结果
    test_result = {
        "original_route": None,
        "final_route": None,
        "initial_report": None,
        "final_report": None,
        "fix_history": [],
        "output_dir": str(output_dir)
    }

    try:
        result = main_route_agent.process(
            story_outline_data=story_outline,
            strategy_text=strategy_text,
            user_idea=user_idea
        )

        print("\n" + "=" * 60)
        print("✅ MainRouteAgent 测试成功!")
        print("=" * 60)

        # 打印详细结果
        result_dict = result.model_dump()
        test_result["original_route"] = result_dict
        print(f"\n📋 结构ID: {result_dict.get('structure_id')}")
        print(f"📋 预计总章节: {result_dict.get('total_estimated_chapters')}章")
        print(f"📋 共通线占比: {result_dict.get('common_ratio')*100:.0f}%")

        # 状态框架
        state = result_dict.get('state', {})
        if state:
            print(f"\n📊 状态框架:")
            for hid, hdata in state.items():
                print(f"  {hid}: {hdata.get('description')} (初始值:{hdata.get('initial')}, 范围:{hdata.get('min')}-{hdata.get('max')})")

        # 分支框架
        branches = result_dict.get('branches', [])
        if branches:
            print(f"\n🔀 分支框架:")
            for b in branches:
                print(f"  [{b.get('id')}]")
                print(f"    目标: {b.get('target')}")
                print(f"    描述: {b.get('desc')}")
                print(f"    长度: {b.get('chapters')}章")
                print(f"    返回: {b.get('return')}")
                print(f"    奖励: {b.get('reward')}")

        # 结局分支框架
        endings = result_dict.get('endings', [])
        if endings:
            print(f"\n🎭 结局分支框架:")
            for e in endings:
                print(f"  [{e.get('id')}] {e.get('type')}")
                print(f"    目标: {e.get('target')}")
                print(f"    描述: {e.get('desc')}")
                print(f"    长度: {e.get('chapters')}章")

        # 章节列表
        chapters = result_dict.get('chapters', [])
        print(f"\n📁 章节列表:")
        print(f"  章节数: {len(chapters)}章")

        for ch in chapters:
            print(f"\n  [{ch.get('id')}] {ch.get('summary')}")
            if ch.get('scene'):
                print(f"    场景: {ch.get('scene')}")

            choices = ch.get('choices', [])
            if choices:
                print(f"    选择点:")
                for c in choices:
                    print(f"      - {c.get('text')}")
                    print(f"        目标: {c.get('target')}")
                    branch = c.get('branch')
                    if branch:
                        print(f"        跳转: {branch}")
                    visible = c.get('visible')
                    if visible:
                        print(f"        可见: {visible}")
                    effect = c.get('effect', {})
                    if effect:
                        print(f"        效果: {effect}")

        # 保存结果
        main_route_file = output_dir / "main_route_framework.json"
        with open(main_route_file, 'w', encoding='utf-8') as f:
            json.dump(result_dict, f, ensure_ascii=False, indent=2)
        print(f"\n主线框架已保存到: {main_route_file}")

        # 执行一致性检查
        print("\n" + "=" * 60)
        print("执行路线一致性检查...")
        print("=" * 60)

        consistency_agent = RouteConsistencyAgent()
        report = consistency_agent.process(route_framework=result_dict)
        test_result["initial_report"] = report

        print(f"\n📊 检查状态: {report.get('overall_status')}")
        print(f"📊 问题总数: {report.get('total_issues')}个")

        issues = report.get('issues', [])
        if issues:
            print(f"\n⚠️ 发现的问题:")
            for i, issue in enumerate(issues, 1):
                print(f"  {i}. [{issue.get('severity')}] {issue.get('category')}")
                print(f"     描述: {issue.get('description')}")
                print(f"     位置: {issue.get('location')}")
                print(f"     建议: {issue.get('fix_suggestion')}")
        else:
            print("\n✅ 没有发现路线设计问题")

        # 保存检查报告
        report_file = output_dir / "consistency_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"\n检查报告已保存到: {report_file}")

        # 审核修改循环
        MAX_FIX_ROUNDS = 3
        current_route = result_dict
        fix_history = []

        for fix_round in range(1, MAX_FIX_ROUNDS + 1):
            # 获取关键和高优先级问题
            critical_issues = [i for i in issues if i.get('severity') == 'critical']
            high_issues = [i for i in issues if i.get('severity') == 'high']

            # 退出条件：无critical和high问题
            if len(critical_issues) == 0 and len(high_issues) == 0:
                print("\n✅ 无需要修复的关键或高优先级问题")
                break

            print("\n" + "=" * 60)
            print(f"🔧 第{fix_round}轮修复 (共{len(critical_issues)}个关键问题, {len(high_issues)}个高优先级问题)")
            print("=" * 60)

            # 执行修复
            all_issues = critical_issues + high_issues

            if use_regeneration and fix_round == 1:
                # 第一轮使用重新生成模式，把问题传递给MainRouteAgent
                print("   模式: 重新生成（传递修改意见）")
                main_route_agent = MainRouteAgent()
                regenerated = main_route_agent.process(
                    story_outline_data=story_outline,
                    strategy_text=strategy_text,
                    user_idea=user_idea,
                    previous_issues=all_issues
                )
                fixed_result = regenerated.model_dump()
                fixed_result["regenerated"] = True
            else:
                # 使用MainRouteFixerAgent直接修复当前框架
                print(f"   模式: 直接修复（第{fix_round}轮）")
                fixer_agent = MainRouteFixerAgent()
                fixed_result = fixer_agent.process(
                    route_framework=current_route,
                    issues=all_issues,
                    fix_round=fix_round
                )

            print(f"\n🔧 第{fix_round}轮修复完成")
            print(f"📋 修复后结构ID: {fixed_result.get('structure_id')}")
            print(f"📋 修复问题数: {len(all_issues)}个")

            # 记录修复历史
            fix_history.append({
                "round": fix_round,
                "issues_count": len(all_issues),
                "fix_count": fixed_result.get("fix_count", len(all_issues))
            })
            test_result["fix_history"] = fix_history

            # 重新检查
            print("\n📊 重新检查路线一致性...")
            consistency_agent = RouteConsistencyAgent()
            new_report = consistency_agent.process(route_framework=fixed_result)

            new_critical = [i for i in new_report.get('issues', []) if i.get('severity') == 'critical']
            new_high = [i for i in new_report.get('issues', []) if i.get('severity') == 'high']

            print(f"📊 检查结果: {len(new_critical)}个关键问题, {len(new_high)}个高优先级问题")

            # 更新状态
            current_route = fixed_result
            report = new_report
            issues = new_report.get('issues', [])

            # 记录到返回结果
            test_result["final_route"] = current_route
            test_result["final_report"] = report

            # 保存中间结果
            round_file = output_dir / f"main_route_framework_round{fix_round}.json"
            with open(round_file, 'w', encoding='utf-8') as f:
                json.dump(fixed_result, f, ensure_ascii=False, indent=2)
            print(f"   中间结果已保存到: {round_file}")

            # 保存检查报告
            round_report_file = output_dir / f"consistency_report_round{fix_round}.json"
            with open(round_report_file, 'w', encoding='utf-8') as f:
                json.dump(new_report, f, ensure_ascii=False, indent=2)
            print(f"   检查报告已保存到: {round_report_file}")

            # 如果没有问题了，结束循环
            if len(new_critical) == 0 and len(new_high) == 0:
                print("\n✅ 修复完成，所有关键和高优先级问题已解决")
                break

        # 检查是否达到最大轮次
        if fix_round >= MAX_FIX_ROUNDS:
            critical_remaining = [i for i in issues if i.get('severity') == 'critical']
            high_remaining = [i for i in issues if i.get('severity') == 'high']
            if critical_remaining or high_remaining:
                print(f"\n⚠️ 已达到最大修复轮次({MAX_FIX_ROUNDS})，仍有{len(critical_remaining)}个关键问题和{len(high_remaining)}个高优先级问题")

        # 保存最终结果
        final_file = output_dir / "main_route_framework_final.json"
        with open(final_file, 'w', encoding='utf-8') as f:
            json.dump(current_route, f, ensure_ascii=False, indent=2)
        print(f"\n📁 最终主线框架已保存到: {final_file}")

        # 保存最终检查报告
        final_report_file = output_dir / "consistency_report_final.json"
        with open(final_report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"📁 最终检查报告已保存到: {final_report_file}")

        # 打印修复历史
        if fix_history:
            print(f"\n📋 修复历史:")
            for h in fix_history:
                print(f"  第{h['round']}轮: 发现{h['issues_count']}个问题, 修复{h['fix_count']}个")

        # 如果没有修复循环，也要设置返回值
        if test_result["final_route"] is None:
            test_result["final_route"] = result_dict
        if test_result["final_report"] is None:
            test_result["final_report"] = report

        return test_result

    except Exception as e:
        print(f"\n❌ MainRouteAgent 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    result = test_main_route_with_strategy()
    exit(0 if result is not None else 1)
