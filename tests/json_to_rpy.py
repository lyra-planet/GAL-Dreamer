"""
将章节JSON转换为Ren'Py脚本格式
"""
import json
from pathlib import Path


def character_id_to_var_name(character_id: str) -> str:
    """将character_id转换为Ren'Py变量名"""
    # 直接使用ID作为变量名，保持原样
    return character_id


def emotion_to_rpy(emotion: str) -> str:
    """将表情转换为Ren'Py表情标签"""
    if not emotion:
        return "normal"

    mapping = {
        "害羞": "shy",
        "开心": "happy",
        "难过": "sad",
        "愤怒": "angry",
        "惊讶": "surprised",
        "温柔": "gentle",
        "无奈": "wry",
        "紧张": "nervous",
        "羞涩": "blush",
        "困惑": "confused",
        "平静": "normal",
        "期待": "hopeful",
        "委屈": "pout",
        "好奇": "curious",
        "认真": "serious",
        "坚定": "determined",
        "雀跃": "delighted",
        "兴奋": "excited",
        "得意": "proud",
        "恍然": "realization",
        "活泼": "lively",
        "微笑": "smile",
    }
    return mapping.get(emotion, "normal")


def convert_chapter_to_rpy(chapter_data: dict) -> str:
    """将章节数据转换为Ren'Py脚本"""
    lines = []

    chapter = chapter_data.get("chapter", 1)
    chapter_id = chapter_data.get("chapter_id", "")
    characters = chapter_data.get("characters", [])
    scenes = chapter_data.get("scenes", [])

    # 角色ID到名字的映射
    char_name_map = {}
    for char in characters:
        char_id = char.get("character_id", "")
        char_name = char.get("character_name", "")
        if char_id:
            char_name_map[char_id] = char_name

    # 角色定义部分
    lines.append("# 角色定义")
    # 定义旁白角色
    lines.append("define n = Character(\"\")")  # 空名字的旁白角色
    lines.append("")
    for char_id, char_name in char_name_map.items():
        var_name = character_id_to_var_name(char_id)
        lines.append(f"define {var_name} = Character(\"{char_name}\")")
    lines.append("")
    lines.append("")

    # 主label
    lines.append("label start:")
    lines.append(f"    # 第{chapter}章 ({chapter_id})")
    lines.append("")

    # 当前显示的角色和表情
    visible_chars = {}

    for scene_idx, scene in enumerate(scenes):
        scene_num = scene.get("scene", scene_idx + 1)
        scene_title = scene.get("title", "")
        location = scene.get("location", "")
        time_of_day = scene.get("time_of_day", "")
        background = scene.get("background", "")
        narration = scene.get("narration", "")
        events = scene.get("events", [])

        # 场景标题
        if scene_title:
            lines.append(f"    # === 第{scene_num}幕: {scene_title} ===")
        else:
            lines.append(f"    # === 第{scene_num}幕 ===")

        # 场景信息
        lines.append(f"    # 场景: {location}, 时间: {time_of_day}")

        # 场景背景描述（注释）
        if background:
            lines.append(f"    # 背景: {background}")

        # 场景切换
        if location:
            lines.append(f"    scene bg {location}")

        lines.append("")

        # 开场旁白
        if narration:
            lines.append(f'    n "{narration}"')
            lines.append("")

        # 处理事件
        for event in events:
            event_type = event.get("type", "")
            speaker = event.get("speaker")
            content = event.get("content", "")
            emotion = event.get("emotion", "")
            action = event.get("action", "")

            if event_type == "narration":
                # 旁白
                lines.append(f'    n "{content}"')
                if action:
                    lines.append(f"    # {action}")

            elif event_type == "dialogue":
                # 对话
                if speaker:
                    var_name = character_id_to_var_name(speaker)

                    # 处理表情变化
                    if emotion:
                        emotion_tag = emotion_to_rpy(emotion)
                        lines.append(f"    show {var_name} {emotion_tag}")
                        visible_chars[speaker] = emotion_tag

                    # 处理动作（作为注释）
                    if action:
                        lines.append(f"    # {action}")

                    # 对话内容
                    lines.append(f'    {var_name} "{content}"')
                else:
                    # 无说话者，作为旁白处理
                    lines.append(f'    n "{content}"')

            elif event_type == "action":
                # 纯动作
                if action:
                    lines.append(f"    # {action}")

            lines.append("")

        # 场景间分隔（移除）
        # lines.append("    \"\"\"")
        # lines.append("")

    # 结尾
    lines.append("    return")
    lines.append("")

    return "\n".join(lines)


def main():
    # 读取章节JSON
    json_path = Path("/Users/lyra/Desktop/GAL-Dreamer/temp_chapters/common_ch1.json")
    output_path = Path("/Users/lyra/Desktop/GAL-Dreamer/test/galDreamer/game/script.rpy")

    if not json_path.exists():
        print(f"错误: 找不到文件 {json_path}")
        return 1

    with open(json_path, 'r', encoding='utf-8') as f:
        chapter_data = json.load(f)

    # 转换为RPY格式
    rpy_content = convert_chapter_to_rpy(chapter_data)

    # 保存
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(rpy_content)

    print(f"✅ 已转换: {json_path} -> {output_path}")

    # 显示角色信息
    characters = chapter_data.get('characters', [])
    if characters:
        char_str = ', '.join([f"{c.get('character_name', '?')}" for c in characters])
        print(f"   角色: {char_str}")
    print(f"   场景数: {len(chapter_data.get('scenes', []))}")

    # 显示角色变量映射
    print("\n角色变量映射:")
    for char in characters:
        char_id = char.get("character_id", "")
        char_name = char.get("character_name", "")
        var_name = character_id_to_var_name(char_id)
        print(f"  {char_id} -> {var_name} ({char_name})")

    return 0


if __name__ == "__main__":
    exit(main())
