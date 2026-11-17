"""Export the current rules as individually named ChatGPT project files."""
from pathlib import Path
import argparse
import re


ROOT = Path(__file__).resolve().parents[1]
FILES = {
    "SKILL.md": "00-信息流助手入口.md",
    "skills/infoflow-character-prompts/SKILL.md": "01-人物提示词.md",
    "skills/infoflow-storyboard-prompts/SKILL.md": "02-分镜提示词.md",
    "skills/infoflow-eight-openings/SKILL.md": "03-八个开头.md",
    "shared/shot-rules.md": "04-分镜共用规则.md",
    "skills/infoflow-character-prompts/references/appearance-library.md": "05-人物美型库.md",
    "skills/infoflow-character-prompts/references/three-views.md": "06-三视图模板.md",
    "templates/project-brief.md": "07-项目交接单.md",
    "skills/infoflow-script-breakdown/SKILL.md": "08-剧本拆解.md",
}
PROJECT_INSTRUCTIONS = """你是信息流漫剧制作助手。每次新会话、切换剧本、改变任务或续做时，先读取项目资料里的《00-信息流助手入口.md》，随后只读取它指定的当前任务资料。新剧本按本轮明确提供的素材工作。续做时只承接用户点名的项目、版本和已确认资料，不从其他聊天自行延续角色、剧本、格式例外或进度。未明确当前任务或缺少关键资料时，只简短询问对应缺项。临时改动只用于当前任务。"""


def export(destination):
    destination.mkdir(parents=True, exist_ok=True)
    for source, filename in FILES.items():
        source_path = ROOT / source
        content = source_path.read_text(encoding="utf-8")

        def project_reference(match):
            target = (source_path.parent / match[2]).resolve().relative_to(ROOT)
            return f"{match[1]}（项目资料《{FILES[target.as_posix()]}》）"

        rendered = re.sub(r"\[([^\]\n]+)\]\(([^):#\n]+\.md)\)", project_reference, content)
        (destination / filename).write_text(rendered, encoding="utf-8")
    (destination / "项目指令.txt").write_text(PROJECT_INSTRUCTIONS + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "dist" / "chatgpt")
    export(parser.parse_args().output)
