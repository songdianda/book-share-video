#!/usr/bin/env python3
"""Build local narration and measured captions; mux without overwriting a final."""
import argparse
import json
import math
import shutil
import subprocess
import tempfile
import wave
from pathlib import Path

KINDS = {'quote', 'paraphrase', 'interpretation', 'example'}
RATE = 48000


def run(args):
    return subprocess.run([str(x) for x in args], check=True, capture_output=True, text=True)


def duration(path):
    value = float(run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                      '-of', 'default=nw=1:nk=1', path]).stdout)
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f'Invalid audio duration: {path}')
    return value


def srt_time(seconds):
    ms = round(seconds * 1000)
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f'{h:02}:{m:02}:{s:02},{ms:03}'


def validate(spec):
    segments = spec.get('segments')
    if not isinstance(segments, list) or not segments:
        raise ValueError('segments must be a nonempty list')
    for key, default in [('lead', 1), ('tail', 1.5), ('gap', .5)]:
        val = spec.get(key, default)
        if isinstance(val, bool) or not isinstance(val, (int, float)) or not math.isfinite(val) or not 0 <= val <= 30:
            raise ValueError(f'{key} must be 0..30 seconds')
    for segment in segments:
        for key in ('text', 'caption'):
            if not isinstance(segment.get(key), str) or not segment[key].strip():
                raise ValueError(f'Each segment needs {key}')
        if segment.get('kind') not in KINDS:
            raise ValueError('Each segment needs an attribution kind')
    return spec


def resolve_audio(project, value):
    if not isinstance(value, str):
        raise ValueError('audio must be a local project-relative path')
    path = (project / value).resolve()
    if not path.is_relative_to(project) or not path.is_file():
        raise ValueError('Input audio must be a file within the project')
    return path


def generate(project, voice='Tingting', rate=195):
    spec = validate(json.loads((project / 'segments.json').read_text()))
    outputs = [project / 'timeline.json', project / 'captions.srt', project / 'audio/voiceover.wav']
    if any(path.exists() for path in outputs):
        raise FileExistsError('Narration/timeline exists. Use a new versioned project.')
    for item in spec['segments']:
        if 'audio' in item:
            resolve_audio(project, item['audio'])
    if any('audio' not in item for item in spec['segments']) and not shutil.which('say'):
        raise RuntimeError('macOS say unavailable; provide per-segment local audio')
    audio_dir = project / 'audio'
    audio_dir.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.narration-', dir=audio_dir) as scratch:
        scratch = Path(scratch)
        position = round(spec.get('lead', 1) * RATE)
        entries, chunks = [], []
        for index, item in enumerate(spec['segments']):
            if 'audio' in item:
                source = resolve_audio(project, item['audio'])
            else:
                textfile = scratch / f'{index:03}.txt'
                textfile.write_text(item['text'], encoding='utf-8')
                source = scratch / f'{index:03}.aiff'
                run(['say', '-v', voice, '-r', rate, '-f', textfile, '-o', source])
            actual = duration(source)
            pcm = scratch / f'{index:03}.wav'
            run(['ffmpeg', '-v', 'error', '-n', '-i', source, '-ar', RATE,
                 '-ac', '1', '-c:a', 'pcm_s16le', pcm])
            with wave.open(str(pcm)) as wavefile:
                count = wavefile.getnframes()
                chunks.append(wavefile.readframes(count))
            entry = dict(item, a=position / RATE, b=(position + count) / RATE,
                         measured_source_duration=actual)
            entries.append(entry)
            position += count
            if index < len(spec['segments']) - 1:
                position += round(spec.get('gap', .5) * RATE)
        end = (position + round(spec.get('tail', 1.5) * RATE)) / RATE
        with wave.open(str(scratch / 'voiceover.wav'), 'wb') as target:
            target.setnchannels(1)
            target.setsampwidth(2)
            target.setframerate(RATE)
            target.writeframes(b'\0\0' * round(spec.get('lead', 1) * RATE))
            for i, chunk in enumerate(chunks):
                target.writeframes(chunk)
                if i < len(chunks) - 1:
                    target.writeframes(b'\0\0' * round(spec.get('gap', .5) * RATE))
            target.writeframes(b'\0\0' * round(spec.get('tail', 1.5) * RATE))
        timeline = {'title': spec.get('title', ''), 'end': end, 'fps': 30,
                    'voice': voice, 'segments': entries}
        captions = '\n\n'.join(f"{i+1}\n{srt_time(e['a'])} --> {srt_time(e['b'])}\n{e['caption']}"
                                for i, e in enumerate(entries)) + '\n'
        (project / 'timeline.json').write_text(json.dumps(timeline, ensure_ascii=False, indent=2) + '\n')
        (project / 'captions.srt').write_text(captions, encoding='utf-8')
        (scratch / 'voiceover.wav').replace(audio_dir / 'voiceover.wav')
    print(f'Created narration and timeline: {end:.3f}s, {len(entries)} segments')


def mux(project):
    timeline = json.loads((project / 'timeline.json').read_text())
    end = timeline['end']
    if not isinstance(end, (int, float)) or not math.isfinite(end) or end <= 0:
        raise ValueError('Invalid timeline duration')
    out = project / 'renders/final.mp4'
    if out.exists():
        raise FileExistsError('final.mp4 exists. Use a new versioned project.')
    raw, voice, score = [project / x for x in ['renders/raw.mp4', 'audio/voiceover.wav', 'audio/score.wav']]
    for path in [raw, voice]:
        if abs(duration(path) - end) > .1:
            raise ValueError(f'Duration differs from narration timeline: {path}')
    args = ['ffmpeg', '-v', 'error', '-n', '-i', raw, '-i', voice]
    if score.exists():
        if abs(duration(score) - end) > .1:
            raise ValueError('score.wav must cover the measured timeline')
        args += ['-i', score, '-filter_complex',
                 '[1:a]volume=1[v];[2:a]volume=0.12[m];[v][m]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-16:TP=-1.5:LRA=9[a]']
    else:
        args += ['-filter_complex', '[1:a]loudnorm=I=-16:TP=-1.5:LRA=9[a]']
    args += ['-map', '0:v:0', '-map', '[a]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
             '-ar', RATE, '-t', str(end), '-movflags', '+faststart']
    with tempfile.TemporaryDirectory(prefix='.mux-', dir=out.parent) as scratch:
        rendered = Path(scratch) / 'final.mp4'
        run(args + [rendered])
        if abs(duration(rendered) - end) > .1:
            raise ValueError('Mux duration mismatch')
        # A hard link publishes without overwriting a concurrently created destination.
        out.hardlink_to(rendered)
    print(out)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('project', type=Path)
    parser.add_argument('--voice', default='Tingting')
    parser.add_argument('--rate', type=int, default=195)
    parser.add_argument('--mux', action='store_true')
    args = parser.parse_args()
    if not 80 <= args.rate <= 350:
        parser.error('rate must be 80..350')
    project = args.project.expanduser().resolve()
    try:
        mux(project) if args.mux else generate(project, args.voice, args.rate)
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as error:
        parser.exit(1, f'Error: {error}\n')


if __name__ == '__main__':
    main()
