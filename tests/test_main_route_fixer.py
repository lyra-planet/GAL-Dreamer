"""
测试 MainRouteFixerAgent - 直接修改主线框架中的问题
"""
import json
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.route_planning.main_route_fixer_agent import MainRouteFixerAgent
from utils.route_consistency_checker import check_route_consistency


def load_json_file(file_path: str) -> dict:
    """加载JSON文件"""
    path = Path(file_path)
    if not path.exists():
        print(f"错误: {file_path} 不存在")
        return None

    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def test_main_route_fixer():
    """测试 MainRouteFixerAgent"""
    print("\n" + "=" * 60)
    print("MainRouteFixerAgent 测试")
    print("=" * 60)

    # 加载主线框架
    route_file = "/Users/lyra/Desktop/GAL-Dreamer/output/main_route_test/main_route_framework.json"
    route_data = load_json_file(route_file)
    if not route_data:
        return None

    print(f"\n加载主线框架: {route_file}")
    print(f"  结构ID: {route_data.get('structure_id')}")
    print(f"  章节数: {len(route_data.get('chapters', []))}")
    print(f"  分支数: {len(route_data.get('branches', []))}")
    print(f"  结局数: {len(route_data.get('endings', []))}")

    # 使用脚本检查问题
    print("\n" + "=" * 60)
    print("检查路线一致性...")
    print("=" * 60)

    report_data = check_route_consistency(route_data)

    print(f"\n📊 检查状态: {report_data.get('overall_status')}")
    print(f"📊 问题总数: {report_data.get('total_issues')}")
    print(f"📊 摘要: {report_data.get('summary')}")

    issues = report_data.get('issues', [])
    if issues:
        print(f"\n需要修复的问题:")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. [{issue.get('severity')}] {issue.get('category')}")
            print(f"     描述: {issue.get('description')}")
            print(f"     位置: {issue.get('location')}")
    else:
        print("\n✅ 没有发现问题，无需修复")
        return None

    # 执行修复
    print("\n" + "=" * 60)
    print("执行修复...")
    print("=" * 60)

    fixer_agent = MainRouteFixerAgent()

    try:
        fixed_result = fixer_agent.process(
            route_framework=route_data,
            issues=issues,
            fix_round=1
        )

        print("\n" + "=" * 60)
        print("✅ 修复完成!")
        print("=" * 60)

        print(f"\n📋 修复后结构ID: {fixed_result.get('structure_id')}")
        print(f"📋 章节数: {len(fixed_result.get('chapters', []))}")
        print(f"📋 分支数: {len(fixed_result.get('branches', []))}")
        print(f"📋 结局数: {len(fixed_result.get('endings', []))}")

        # 保存修复后的结果
        output_dir = project_root / "output" / "main_route_test"
        output_dir.mkdir(parents=True, exist_ok=True)

        fixed_file = output_dir / "main_route_framework_fixed.json"
        with open(fixed_file, 'w', encoding='utf-8') as f:
            json.dump(fixed_result, f, ensure_ascii=False, indent=2)
        print(f"\n修复后的框架已保存到: {fixed_file}")

        # 重新检查
        print("\n" + "=" * 60)
        print("重新检查修复后的框架...")
        print("=" * 60)

        new_report = check_route_consistency(fixed_result)

        print(f"\n📊 检查状态: {new_report.get('overall_status')}")
        print(f"📊 问题总数: {new_report.get('total_issues')}个")

        new_issues = new_report.get('issues', [])
        if new_issues:
            print(f"\n⚠️ 修复后仍有问题:")
            for i, issue in enumerate(new_issues, 1):
                print(f"  {i}. [{issue.get('severity')}] {issue.get('category')}")
                print(f"     描述: {issue.get('description')}")
        else:
            print("\n✅ 修复后没有发现问题!")

        # 保存检查报告
        new_report_file = output_dir / "consistency_report_after_fix.json"
        with open(new_report_file, 'w', encoding='utf-8') as f:
            json.dump(new_report, f, ensure_ascii=False, indent=2)
        print(f"\n检查报告已保存到: {new_report_file}")

        return {
            "fixed_result": fixed_result,
            "new_report": new_report
        }

    except Exception as e:
        print(f"\n❌ 修复失败: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    result = test_main_route_fixer()
    exit(0 if result is not None else 1)
