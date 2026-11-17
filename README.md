# 信息流漫剧助手

把人物提示词、正文分镜、八个开头做成按任务读取的技能。给信息流漫剧制作人员使用。每部剧单独保存已确认的素材和交接单，新会话从指定版本继续。

## 在 Codex 或 Claude Code 使用

在仓库根目录开新会话。首次可直接发送：

> 先按根目录 SKILL.md 开始。新项目《项目名》。这次只做人物提示词。剧本见我本轮提供的素材。

之后可以这样继续：

> 继续《项目名》。读取 projects/项目名/brief.md 和其中指定的分镜稿。只补第 12 镜。

Codex 的仓库入口是 [AGENTS.md](AGENTS.md)，Claude Code 从 [CLAUDE.md](CLAUDE.md) 引用它。制作任务统一转到根入口 [SKILL.md](SKILL.md)。如果在其他工具里能访问仓库文件，可直接点名要求读取根入口。

## 在 ChatGPT 项目使用

1. 下载或克隆本仓库。运行 `python3 scripts/export_chatgpt.py`，在 `dist/chatgpt/` 生成规则文件。
2. 新建 ChatGPT「项目」，上传目录中的八个 Markdown 文件作为项目资料。把生成的 `项目指令.txt` 内容粘到「项目设置 → 项目指令」。更新规则时替换同名的项目资料。
3. 在这个项目里开新对话。每轮点名剧本和任务，只提供本轮的素材或当前交接单。项目资料可以在该项目内的多个会话里复用。

项目内的其他聊天仍可能成为上下文。每部剧独立开项目更容易隔离聊天，或者在同一项目里按剧本分别开会话，每次明确给出文件版本。GitHub 上修改规则后，重新导出并在 ChatGPT 项目内替换相应资料。

## 三条制作入口

| 任务 | 文件 | 使用的资料 |
| --- | --- | --- |
| 人物提示词与三视图 | [人物提示词](skills/infoflow-character-prompts/SKILL.md) | 当前剧本、确认的角色设定。三视图需要角色完整版 |
| 正文与补镜 | [分镜提示词](skills/infoflow-storyboard-prompts/SKILL.md) | 剧本、真实配音时间。补镜需要原镜及相邻镜头 |
| 八个开头 | [八个开头](skills/infoflow-eight-openings/SKILL.md) | 真实前五秒音频文案、正文五秒后的起镜 |

长期规则写在技能文件里。单部剧用[交接单](templates/project-brief.md)记录已确认的人物、剧本版本、音频、分镜和下一步。可把私有生产资料放在本地 `projects/`。

## 测试

```bash
python3 -m unittest discover -s tests -v
python3 scripts/check_shots.py storyboard 分镜稿.md --audio 配音原文.txt
python3 scripts/check_shots.py openings 八个开头.md --audio 前五秒原文.txt
python3 scripts/check_shots.py insert 替换镜头.md --original 原镜头.md
```

校验器覆盖分镜字段与顺序、景别、编号、整数秒、段落结构和逐字音频比对。`storyboard` 可加 `--duration` 检查不足四十秒的正文，或用 `--group` 检查指定组。主动要求场景字段时加 `--scene`。用 `--help` 查看参数。运镜是否好拍、人物是否衔接、八套钩子视觉上是否不同这类判断，由技能按 [复验用例](tests/behavior-cases.md) 检查并由制作人员抽验。

当前生产规则按《信息流助手》2026-11-12 单文件版拆分。参考 [baoyu-skills](https://github.com/JimLiu/baoyu-skills) 的模块和按需引用结构。
