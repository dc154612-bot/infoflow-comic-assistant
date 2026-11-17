"""Check shared links, export files and the main shot-format regressions."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.check_shots import validate
from scripts.export_chatgpt import FILES, export


def shot(n, start, end, audio="", action="抬眼"):
    return f"""镜头{n}｜{start}—{end}秒
【对应音频】{audio}
【景别】近景
【人物动作与表情】阿澄{action}，不说话。
【走位】柜台左侧。
【镜头运动】固定镜头，平视。
【光线】暖白顶光。
【时间】白天"""


def openings():
    return "\n".join(
        f"开头方案{n}｜0—5秒\n{shot(1, 0, 2, '雨停了，')}\n{shot(2, 2, 5, '她抬头。')}"
        for n in range(1, 9)
    )


class ShotTest(unittest.TestCase):
    def test_openings_audio_and_structure(self):
        self.assertEqual(validate(openings(), "openings", audio="雨停了，她抬头。"), [])

    def test_openings_require_eight_plans(self):
        bad = openings().split("开头方案8", 1)[0]
        self.assertTrue(validate(bad, "openings"))

    def test_openings_first_shot_maximum_three_seconds(self):
        bad = openings().replace("镜头1｜0—2秒", "镜头1｜0—4秒", 1)
        self.assertTrue(any("超过三秒" in error for error in validate(bad, "openings")))

    def test_openings_preserve_punctuation_in_every_plan(self):
        bad = openings().replace("雨停了，", "雨停了。", 1)
        self.assertEqual(validate(bad, "openings", audio="雨停了，她抬头。"),
                         ["开头方案1的对应音频和原文不一致。"])

    def test_insert_can_change_action(self):
        original = shot(12, 21, 24, "门锁响了。")
        updated = shot(12, 21, 24, "门锁响了。", action="攥紧钥匙")
        self.assertEqual(validate(updated, "insert", original=original), [])

    def test_insert_rejects_changed_slot_or_audio(self):
        original = shot(12, 21, 24, "门锁响了。")
        for bad in (shot(11, 21, 24, "门锁响了。"), shot(12, 20, 24, "门锁响了。"),
                    shot(12, 21, 24, "门锁响了！")):
            self.assertTrue(validate(bad, "insert", original=original))

    def test_scene_is_opt_in(self):
        with_scene = shot(1, 0, 2) + "\n【场景】雨巷"
        self.assertTrue(validate(with_scene, "insert"))
        self.assertEqual(validate(with_scene, "insert", scene=True), [])

    def test_scale_and_order(self):
        bad = shot(1, 0, 2).replace("【景别】近景", "【景别】近景仰拍")
        self.assertTrue(validate(bad, "insert"))
        bad = shot(1, 0, 2).replace("【光线】", "【时间】").replace("【时间】白天", "【光线】白天")
        self.assertTrue(validate(bad, "insert"))

    def test_storyboard_tail_uses_actual_duration(self):
        text = f"分镜头组1｜0—8秒\n{shot(1, 0, 2, '一，')}\n{shot(2, 2, 5, '二，')}\n{shot(3, 5, 8, '三。')}"
        self.assertEqual(validate(text, "storyboard", duration=8, audio="一，二，三。"), [])
        self.assertTrue(validate(text, "storyboard"))

    def test_short_storyboard_final_group(self):
        for duration in (31, 32):
            with self.subTest(duration=duration):
                text = f"分镜头组4｜30—{duration}秒\n{shot(10, 30, duration, '她抬头。')}"
                self.assertEqual(validate(text, "storyboard", duration=duration, group=4,
                                          audio="她抬头。"), [])

    def test_targeted_group_keeps_global_shot_numbering(self):
        text = f"分镜头组3｜20—30秒\n{shot(8, 20, 22)}\n{shot(9, 22, 25)}\n{shot(10, 25, 30)}"
        self.assertEqual(validate(text, "storyboard", group=3), [])
        self.assertTrue(validate(text.replace("镜头9", "镜头7"), "storyboard", group=3))

    def test_time_must_use_integers_and_be_continuous(self):
        with self.assertRaises(ValueError):
            validate(shot(1, 0, "2.5"), "insert")
        text = f"分镜头组1｜0—10秒\n{shot(1, 0, 2)}\n{shot(2, 3, 5)}\n{shot(3, 5, 10)}"
        self.assertTrue(any("空档" in error for error in validate(text, "storyboard", group=1)))


class ExportTest(unittest.TestCase):
    def test_project_sources_have_unique_names_and_named_links(self):
        with TemporaryDirectory() as folder:
            destination = Path(folder)
            export(destination)
            self.assertEqual({p.name for p in destination.iterdir()}, set(FILES.values()) | {"项目指令.txt"})
            entry = (destination / FILES["SKILL.md"]).read_text(encoding="utf-8")
            for source in ("skills/infoflow-script-breakdown/SKILL.md",
                           "skills/infoflow-character-prompts/SKILL.md", "skills/infoflow-storyboard-prompts/SKILL.md",
                           "skills/infoflow-eight-openings/SKILL.md", "templates/project-brief.md"):
                self.assertIn(f"《{FILES[source]}》", entry)
            self.assertNotIn("skills/", entry)
