"""Book scaffolds protect existing work and preserve one authored timeline."""
import contextlib
import copy
import html.parser
import io
import json
from pathlib import Path
import re
import tempfile
import unittest

from scripts import new_book


class PageParser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_title = False
        self.title = ""
        self.scripts = []
        self.canvases = []

    def handle_starttag(self, tag, attrs):
        if tag == "title":
            self.in_title = True
        elif tag == "script":
            self.scripts.append(dict(attrs))
        elif tag == "canvas":
            self.canvases.append(dict(attrs))

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title += data


class NewBookTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.project = Path(self.tmp.name) / "new book"
        self.timeline = {
            "title": "一本书", "author": "作者", "end": 60, "fps": 30,
            "voice": "none",
            "sections": [
                {"id": 0, "a": 0, "b": 20, "title": "观察"},
                {"id": 1, "a": 20, "b": 60, "title": "行动"},
            ],
            "segments": [
                {"a": 0.6, "b": 6.4, "text": "先观察眼前发生的事。", "kind": "interpretation"},
                {"a": 22.1, "b": 28.8, "text": "然后从一个小行动开始。", "kind": "example"},
            ],
        }

    def read_json(self, name):
        return json.loads((self.project / name).read_text(encoding="utf-8"))

    def read_page(self):
        parser = PageParser()
        parser.feed((self.project / "index.html").read_text(encoding="utf-8"))
        return parser

    def read_javascript_timeline(self):
        source = (self.project / "timeline.js").read_text(encoding="utf-8")
        match = re.match(r"\s*window\.BOOK_TIMELINE\s*=\s*", source)
        self.assertIsNotNone(match)
        data, end = json.JSONDecoder().raw_decode(source, match.end())
        self.assertEqual(source[end:].strip(), ";")
        return data

    def test_default_scaffold_uses_portrait_music_only_production(self):
        supplied = copy.deepcopy(self.timeline)
        for field in ("end", "fps", "voice"):
            supplied.pop(field)
        new_book.create_project(self.project, supplied)
        page = self.read_page()
        canvas = page.canvases[0]
        self.assertEqual((canvas["data-width"], canvas["data-height"]), ("1080", "1920"))
        production = self.read_json("production.json")
        self.assertEqual((production["duration_seconds"], production["fps"], production["voice"]),
                         (60, 30, "none"))
        self.assertFalse(production["rendered_final"])
        self.assertFalse(production["auxiliary_explanatory_labels"])
        self.assertEqual(production["music_fade_in_seconds"], 1.5)
        self.assertEqual(production["music_fade_out_seconds"], 1.5)
        for folder in ("audio", "review", "renders"):
            self.assertTrue((self.project / folder).is_dir())
        self.assertFalse((self.project / "engine").exists())
        self.assertFalse((self.project / "renders/final.mp4").exists())
        self.assertNotIn("end", supplied, "Input planning must not be rewritten")

    def test_existing_directory_and_user_files_are_never_replaced(self):
        self.project.mkdir()
        original = b"user-authored film\x00\xff"
        film = self.project / "film.js"
        film.write_bytes(original)
        with self.assertRaises(FileExistsError):
            new_book.create_project(self.project, self.timeline)
        self.assertEqual(film.read_bytes(), original)
        self.assertEqual([p.name for p in self.project.iterdir()], ["film.js"])

    def test_existing_file_is_not_replaced_with_a_directory(self):
        self.project.write_text("existing note", encoding="utf-8")
        with self.assertRaises(FileExistsError):
            new_book.create_project(self.project, self.timeline)
        self.assertEqual(self.project.read_text(encoding="utf-8"), "existing note")

    def test_existing_symlink_is_refused_including_a_dangling_target(self):
        for index, existing in enumerate((True, False)):
            with self.subTest(target_exists=existing):
                target = Path(self.tmp.name) / f"target-{index}"
                link = Path(self.tmp.name) / f"link-{index}"
                if existing:
                    target.mkdir()
                    (target / "keep.txt").write_text("keep", encoding="utf-8")
                link.symlink_to(target, target_is_directory=True)
                with self.assertRaises(FileExistsError):
                    new_book.create_project(link, self.timeline)
                self.assertTrue(link.is_symlink())
                self.assertEqual(link.readlink(), target)
                if existing:
                    self.assertEqual([p.name for p in target.iterdir()], ["keep.txt"])
                else:
                    self.assertFalse(target.exists())

    def test_special_title_stays_data_in_html_and_javascript(self):
        title = '书名 "引号" & \\路径\n</title><script>alert(1)</script> */\u2028\u2029'
        self.timeline["title"] = title
        new_book.create_project(self.project, self.timeline)
        page = self.read_page()
        self.assertEqual(page.title, title)
        self.assertTrue(page.scripts)
        self.assertTrue(all(script.get("src") for script in page.scripts),
                        "A title must not introduce an inline executable script")
        self.assertEqual(self.read_json("timeline.json")["title"], title)
        self.assertEqual(self.read_javascript_timeline()["title"], title)
        self.assertEqual(self.read_json("segments.json")["title"], title)

    def test_title_with_template_tokens_is_preserved_literally(self):
        title = "书名{{WIDTH}}/{{HEIGHT}}/{{VW_RATIO}}/{{VH_RATIO}}/{{TITLE}}"
        self.timeline["title"] = title
        new_book.create_project(self.project, self.timeline)
        self.assertEqual(self.read_page().title, title)
        self.assertEqual(self.read_json("timeline.json")["title"], title)

    def test_invalid_timelines_leave_no_project_or_parent_directory(self):
        invalid = []

        def changed(mutator):
            timeline = copy.deepcopy(self.timeline)
            mutator(timeline)
            invalid.append(timeline)

        changed(lambda tl: tl.update(end=float("nan")))
        changed(lambda tl: tl.update(end=float("inf")))
        changed(lambda tl: tl.update(end=True))
        changed(lambda tl: tl.update(fps=0))
        changed(lambda tl: tl.update(fps=29.97))
        changed(lambda tl: tl.update(voice="Tingting"))
        changed(lambda tl: tl.update(title="  "))
        changed(lambda tl: tl.update(sections=[]))
        changed(lambda tl: tl["sections"][1].update(a=21))
        changed(lambda tl: tl["sections"][1].update(a=19))
        changed(lambda tl: tl["sections"][1].update(b=59))
        changed(lambda tl: tl["sections"][0].update(a=False))
        changed(lambda tl: tl.update(segments=[]))
        changed(lambda tl: tl["segments"][1].update(a=6))
        changed(lambda tl: tl["segments"][0].update(a=-1))
        changed(lambda tl: tl["segments"][0].update(a=float("nan")))
        changed(lambda tl: tl["segments"][1].update(b=61))
        changed(lambda tl: tl["segments"][0].update(text=" "))
        changed(lambda tl: tl["segments"][0].update(kind="unknown"))
        for index, timeline in enumerate(invalid):
            with self.subTest(case=index):
                parent = Path(self.tmp.name) / f"invalid-{index}"
                project = parent / "book"
                with self.assertRaises(ValueError):
                    new_book.create_project(project, timeline)
                self.assertFalse(parent.exists(), "Validation must finish before creating directories")

    def test_invalid_canvas_dimensions_leave_no_project(self):
        for index, dimensions in enumerate(((1081, 1920), (1080, 1919), (0, 1920),
                                            (1080, True), (1080.0, 1920), (20000, 1920))):
            with self.subTest(dimensions=dimensions):
                project = Path(self.tmp.name) / f"dimensions-{index}"
                with self.assertRaises(ValueError):
                    new_book.create_project(project, self.timeline,
                                            width=dimensions[0], height=dimensions[1])
                self.assertFalse(project.exists())

    def test_srt_carries_seconds_and_minutes_and_all_timeline_copies_agree(self):
        self.timeline["end"] = 3661.1
        self.timeline["fps"] = 24
        self.timeline["sections"] = [{"id": 0, "a": 0, "b": 3661.1, "title": "长时间线"}]
        self.timeline["segments"] = [
            {"a": 59.9996, "b": 60.3334, "text": "跨过一分钟", "kind": "paraphrase"},
            {"a": 3599.9996, "b": 3600.1254, "text": "跨过一小时", "kind": "interpretation"},
            {"a": 3660.0004, "b": 3660.9996, "text": "最后一句", "kind": "example"},
        ]
        expected = copy.deepcopy(self.timeline)
        new_book.create_project(self.project, self.timeline)
        timeline = self.read_json("timeline.json")
        self.assertEqual(timeline, expected)
        self.assertEqual(self.read_javascript_timeline(), expected)
        segments = self.read_json("segments.json")
        self.assertEqual(segments["segments"], expected["segments"])
        self.assertEqual(segments["mode"], "music-only")
        self.assertEqual(self.read_json("production.json")["duration_seconds"], expected["end"])
        self.assertEqual(self.read_json("production.json")["fps"], expected["fps"])
        srt = (self.project / "captions.srt").read_text(encoding="utf-8")
        blocks = srt.strip().split("\n\n")
        self.assertEqual(len(blocks), len(expected["segments"]))
        expected_times = [
            "00:01:00,000 --> 00:01:00,333",
            "01:00:00,000 --> 01:00:00,125",
            "01:01:00,000 --> 01:01:01,000",
        ]
        for index, (block, segment, timing) in enumerate(zip(blocks, expected["segments"], expected_times), 1):
            lines = block.splitlines()
            self.assertEqual(lines[0], str(index))
            self.assertEqual(lines[1], timing)
            self.assertEqual("\n".join(lines[2:]), segment["text"])
        self.assertEqual(self.timeline, expected, "Serializing must not alter supplied values")

    def test_cli_invalid_json_returns_clean_error_without_output(self):
        source = Path(self.tmp.name) / "invalid.json"
        source.write_text("{broken", encoding="utf-8")
        error = io.StringIO()
        with contextlib.redirect_stderr(error), self.assertRaises(SystemExit) as result:
            new_book.main([str(self.project), "--timeline", str(source)])
        self.assertEqual(result.exception.code, 1)
        self.assertIn("Cannot create project", error.getvalue())
        self.assertNotIn("Traceback", error.getvalue())
        self.assertFalse(self.project.exists())


if __name__ == "__main__":
    unittest.main()
