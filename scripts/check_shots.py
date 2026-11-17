"""Validate the structure and source audio of a production storyboard."""
import argparse
from dataclasses import dataclass, field
from pathlib import Path
import re


FIELDS = ("对应音频", "景别", "人物动作与表情", "走位", "镜头运动", "光线", "时间")
SCALES = {"大远景", "远景", "全景", "中景", "中近景", "近景", "特写", "大特写"}
HEADER = re.compile(r"(分镜头组|开头方案|镜头)([0-9]+)｜([0-9]+)—([0-9]+)秒")
FIELD = re.compile(r"【([^】]+)】(.*)")


@dataclass
class Shot:
    number: int
    start: int
    end: int
    fields: list = field(default_factory=list)


@dataclass
class Section:
    kind: str
    number: int
    start: int
    end: int
    shots: list = field(default_factory=list)


def parse(text):
    sections = []
    section = Section("", 0, 0, 0)
    shot = None
    lines = text.strip().splitlines()
    if len(lines) >= 2 and re.fullmatch(r"```(?:markdown|text|md)?", lines[0]) and lines[-1] == "```":
        lines = lines[1:-1]
    for line in lines:
        heading = HEADER.fullmatch(line.strip())
        label = FIELD.fullmatch(line.lstrip())
        if heading:
            kind, n, start, end = heading.groups()
            if kind == "镜头":
                shot = Shot(int(n), int(start), int(end))
                section.shots.append(shot)
            else:
                if section.shots and not sections:
                    raise ValueError("分组标题前已有镜头。")
                section = Section(kind, int(n), int(start), int(end))
                sections.append(section)
                shot = None
        elif label and shot is not None:
            shot.fields.append(label.groups())
        elif line.strip() and line.strip(" *") not in {"需按实际音频对齐", "需按实际音频对齐。"}:
            raise ValueError(f"无法识别的分镜行：{line[:55]}")
    return sections or [section]


def validate(text, mode, *, audio=None, duration=40, group=None, scene=False, original=None):
    sections = parse(text)
    fields = FIELDS + (("场景",) if scene else ())
    errors = []
    next_shot = None if group is not None or mode == "insert" else 1

    if mode == "storyboard":
        expected = [(n, begin, min(begin + 10, duration))
                    for n, begin in enumerate(range(0, duration, 10), 1)
                    if group is None or group == n]
        if not expected or [(s.number, s.start, s.end) for s in sections] != expected or any(
            s.kind != "分镜头组" for s in sections
        ):
            errors.append("正文分组编号或时间范围错误。")
    elif mode == "openings":
        if [(s.kind, s.number, s.start, s.end) for s in sections] != [
            ("开头方案", n, 0, 5) for n in range(1, 9)
        ]:
            errors.append("开头需包含八套从零到五秒的编号方案。")
    elif len(sections) != 1 or sections[0].kind or len(sections[0].shots) != 1:
        errors.append("补镜只允许输出一个镜头。")

    audio_parts = []
    for section in sections:
        if mode == "openings":
            next_shot = 1
        low, high = {"storyboard": (3, 4), "openings": (2, 3), "insert": (1, 1)}[mode]
        if not low <= len(section.shots) <= high:
            errors.append(f"{section.kind or '补镜'}{section.number or ''}的镜头数量错误。")
        last_end = section.start if mode != "insert" else None
        block_audio = []
        for shot in section.shots:
            position = f"第{shot.number}镜"
            if shot.number < 1 or (next_shot is not None and shot.number != next_shot):
                errors.append(position + "编号不连续。")
            next_shot = shot.number + 1

            if shot.end <= shot.start or (last_end is not None and shot.start != last_end):
                errors.append(position + "时间有空档、重叠或不足一秒。")
            last_end = shot.end

            values = dict(shot.fields)
            if tuple(name for name, _ in shot.fields) != fields or any(
                not value.strip() and name != "对应音频" for name, value in shot.fields
            ):
                errors.append(position + "字段缺失、重复、为空或顺序不符。")
            if values.get("景别") not in SCALES:
                errors.append(position + "景别须为一个有效景别词。")
            block_audio.append(values.get("对应音频", ""))

        if mode != "insert" and last_end != section.end:
            errors.append(f"{section.kind}{section.number}的结尾与标题不一致。")
        if mode == "openings":
            if section.shots and section.shots[0].end > 3:
                errors.append(f"开头方案{section.number}的第一镜超过三秒。")
            if audio is not None and "".join(block_audio) != audio:
                errors.append(f"开头方案{section.number}的对应音频和原文不一致。")
        audio_parts.extend(block_audio)

    if mode != "openings" and audio is not None and "".join(audio_parts) != audio:
        errors.append("对应音频和原文不一致。")
    if mode == "insert" and original is not None:
        old = parse(original)
        if len(old) != 1 or old[0].kind or len(old[0].shots) != 1:
            raise ValueError("原稿须为包含原镜头标题的单镜文本。")
        if not errors:
            before, after = old[0].shots[0], sections[0].shots[0]
            if (before.number, before.start, before.end, dict(before.fields).get("对应音频")) != (
                after.number, after.start, after.end, dict(after.fields).get("对应音频")
            ):
                errors.append("补镜改变了原编号、原时间或原音频。")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("storyboard", "openings", "insert"))
    parser.add_argument("file", type=Path)
    parser.add_argument("--audio", type=Path, help="对应音频原文。检查某组时用该组原文。")
    parser.add_argument("--original", type=Path, help="补镜用的原镜头。")
    parser.add_argument("--duration", type=int, help="整数秒，默认 40。")
    parser.add_argument("--group", type=int, help="只检查指定正文分组。")
    parser.add_argument("--scene", action="store_true")
    args = parser.parse_args()
    if args.duration is not None and not (args.mode == "storyboard" and 1 <= args.duration <= 40):
        parser.error("--duration 仅用于正文，取值为 1—40。")
    if args.group is not None and not (args.mode == "storyboard" and 1 <= args.group <= 4):
        parser.error("--group 仅用于正文，取值为 1—4。")
    if args.original is not None and args.mode != "insert":
        parser.error("--original 仅用于补镜。")
    try:
        result = validate(
            args.file.read_text(encoding="utf-8-sig"), args.mode,
            audio=args.audio.read_text(encoding="utf-8-sig").rstrip("\n") if args.audio else None,
            duration=args.duration or 40, group=args.group, scene=args.scene,
            original=args.original.read_text(encoding="utf-8-sig") if args.original else None,
        )
    except (OSError, ValueError) as exc:
        result = [str(exc)]
    print("\n".join(result) if result else "结构检查通过。")
    return int(bool(result))


if __name__ == "__main__":
    raise SystemExit(main())
