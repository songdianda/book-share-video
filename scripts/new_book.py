#!/usr/bin/env python3
"""Create a versioned book-film scaffold from one authored timeline; never overwrite."""
import argparse
import html
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KINDS = {'quote', 'paraphrase', 'interpretation', 'example'}


def number(value, name, *, integer=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
        raise ValueError(f'{name} must be a positive finite number')
    if integer and (not isinstance(value, int) or value > 16384):
        raise ValueError(f'{name} must be an integer <=16384')
    return value


def validate(timeline):
    if not isinstance(timeline, dict):
        raise ValueError('timeline must be an object')
    tl = dict(timeline)
    for key in ('title', 'author'):
        if not isinstance(tl.get(key), str) or not tl[key].strip():
            raise ValueError(f'timeline needs {key}')
    tl.setdefault('end', 60)
    tl.setdefault('fps', 30)
    tl.setdefault('voice', 'none')
    number(tl['end'], 'end')
    number(tl['fps'], 'fps', integer=True)
    if tl['voice'] != 'none':
        raise ValueError('For narration use book_audio.py first; this scaffold owns a music-only timeline')
    previous = 0
    sections = tl.get('sections')
    if not isinstance(sections, list) or not sections:
        raise ValueError('timeline needs nonempty sections')
    for i, section in enumerate(sections):
        if not isinstance(section, dict) or type(section.get('id')) is not int or section['id'] != i:
            raise ValueError('section ids must be sequential integers starting at zero')
        a, b = section.get('a'), section.get('b')
        number(b, 'section b')
        if isinstance(a, bool) or not isinstance(a, (int, float)) or not math.isfinite(a):
            raise ValueError('section a must be finite')
        if abs(a - previous) > 1e-8 or not a < b <= tl['end']:
            raise ValueError('sections must cover the timeline without gaps or overlaps')
        if not isinstance(section.get('title'), str) or not section['title'].strip():
            raise ValueError('each section needs a title')
        previous = b
    if abs(previous - tl['end']) > 1e-8:
        raise ValueError('last section must end at timeline end')
    segments = tl.get('segments')
    if not isinstance(segments, list) or not segments:
        raise ValueError('timeline needs nonempty segments')
    previous = 0
    for segment in segments:
        if not isinstance(segment, dict):
            raise ValueError('segments must be objects')
        a, b = segment.get('a'), segment.get('b')
        number(b, 'caption b')
        if isinstance(a, bool) or not isinstance(a, (int, float)) or not math.isfinite(a):
            raise ValueError('caption a must be finite')
        if not previous <= a < b <= tl['end']:
            raise ValueError('captions must be ordered, non-overlapping and within the film')
        if not isinstance(segment.get('text'), str) or not segment['text'].strip():
            raise ValueError('each caption needs text')
        if segment.get('kind') not in KINDS:
            raise ValueError('each caption needs a quote/paraphrase/interpretation/example kind')
        previous = b
    return tl


def srt_time(seconds):
    ms = round(seconds * 1000)
    hours, ms = divmod(ms, 3600000)
    minutes, ms = divmod(ms, 60000)
    seconds, ms = divmod(ms, 1000)
    return f'{hours:02}:{minutes:02}:{seconds:02},{ms:03}'


def create_project(project, timeline, *, width=1080, height=1920):
    tl = validate(timeline)
    number(width, 'width', integer=True)
    number(height, 'height', integer=True)
    if width % 2 or height % 2:
        raise ValueError('width and height must be even for H.264')
    project = Path(project).expanduser().absolute()
    if project.exists() or project.is_symlink():
        raise FileExistsError('Use a new project directory; existing files are never replaced')
    templates = ROOT / 'assets/portrait'
    # Read every required template before creating output directories.
    files = {name: (templates / name).read_text(encoding='utf-8')
             for name in ('index.html', 'film.js', 'visual-utils.js', 'preview.js')}
    defaults = json.loads((ROOT / 'assets/series-defaults.json').read_text(encoding='utf-8'))
    page = files['index.html']
    for key, value in {'WIDTH': str(width), 'HEIGHT': str(height),
                       'VW_RATIO': f'{width / height * 100:g}', 'VH_RATIO': f'{height / width * 100:g}',
                       'TITLE': html.escape(tl['title'])}.items():
        page = page.replace('{{' + key + '}}', value)
    files['index.html'] = page
    dump = lambda data: json.dumps(data, ensure_ascii=False, indent=2) + '\n'
    files['timeline.json'] = dump(tl)
    files['timeline.js'] = 'window.BOOK_TIMELINE = ' + json.dumps(tl, ensure_ascii=False) + ';\n'
    files['segments.json'] = dump({'title': tl['title'], 'mode': 'music-only', 'segments': tl['segments']})
    files['captions.srt'] = '\n\n'.join(
        f'{i}\n{srt_time(s["a"])} --> {srt_time(s["b"])}\n{s["text"]}'
        for i, s in enumerate(tl['segments'], 1)) + '\n'
    files['production.json'] = dump(dict(defaults, duration_seconds=tl['end'], fps=tl['fps'],
                                         width=width, height=height, stage='scaffold', rendered_final=False))
    files['style.json'] = dump({'book': tl['title'], 'title': tl['title'], 'project': project.name,
                                'status': 'planned', 'family': '', 'material': [], 'composition': [],
                                'motifs': [], 'motion': [], 'typography': '', 'palette': [],
                                'content_fit': '', 'compared_with': [], 'differences': []})
    rows = '\n'.join(f'|{s["a"]}–{s["b"]}|{s["title"]}| | |' for s in tl['sections'])
    files['storyboard.md'] = (f'# {tl["title"]} / {tl["author"]}\n\n'
        f'{tl["end"]}s, {width}×{height}, {tl["fps"]}fps, no narration.\n\n'
        '先完成 sources.md 和 style.json，再按内容绘制主体及动作；这是骨架，不是成片。\n\n'
        '|时间|叙事任务|主体、动作、落点|图文与来源边界|\n|---|---|---|---|\n' + rows + '\n')
    files['sources.md'] = '# 书籍与素材来源\n\n尚未填写核对结果；不能把骨架或未核实文案当成可交付成片。\n'
    project.mkdir(parents=True, exist_ok=False)
    for folder in ('audio', 'review', 'renders'):
        (project / folder).mkdir()
    for name, content in files.items():
        (project / name).write_text(content, encoding='utf-8')
    return project


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('project', type=Path)
    parser.add_argument('--timeline', required=True, type=Path, help='authored timeline JSON, not executable code')
    parser.add_argument('--width', type=int, default=1080)
    parser.add_argument('--height', type=int, default=1920)
    args = parser.parse_args(argv)
    try:
        tl = json.loads(args.timeline.read_text(encoding='utf-8'))
        project = create_project(args.project, tl, width=args.width, height=args.height)
    except (OSError, ValueError, TypeError) as exc:
        parser.exit(1, f'Cannot create project: {exc}\n')
    print(f'Created scaffold: {project}; author scenes and verify sources before rendering.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
