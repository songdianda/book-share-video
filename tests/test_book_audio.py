import importlib.util
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('book_audio', Path(__file__).parents[1] / 'scripts/book_audio.py')
audio = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audio)

class BookAudioTests(unittest.TestCase):
    def test_srt_rounding_carries_minutes(self):
        self.assertEqual(audio.srt_time(59.9998), '00:01:00,000')
    def test_invalid_timing_and_attribution_rejected(self):
        base = {'segments': [{'text': '解说', 'caption': '字幕', 'kind': 'example'}]}
        audio.validate(base)
        for value in [float('nan'), -1, True]:
            with self.assertRaises(ValueError):
                audio.validate(dict(base, gap=value))
        with self.assertRaises(ValueError):
            audio.validate({'segments':[{'text':'x','caption':'x','kind':'invented-fact'}]})
    def test_audio_cannot_escape_project(self):
        with tempfile.TemporaryDirectory() as root:
            project = Path(root) / 'project'
            project.mkdir()
            outside = Path(root) / 'secret.wav'
            outside.write_bytes(b'not audio')
            with self.assertRaises(ValueError):
                audio.resolve_audio(project.resolve(), '../secret.wav')
    def test_existing_timeline_is_preserved(self):
        with tempfile.TemporaryDirectory() as root:
            project = Path(root)
            (project / 'segments.json').write_text('{"segments":[{"text":"x","caption":"x","kind":"quote"}]}')
            (project / 'timeline.json').write_text('existing user timeline')
            with self.assertRaises(FileExistsError):
                audio.generate(project)
            self.assertEqual((project / 'timeline.json').read_text(), 'existing user timeline')
