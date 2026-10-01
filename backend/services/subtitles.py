"""Timed transcript parsing and exports, independent of model providers."""

import html
import json
import math
import re
import xml.etree.ElementTree as ET


def timestamp(value):
    value = str(value).strip()
    match = re.fullmatch(r'([0-9.]+)(ms|s|m|h)', value)
    if match:
        return float(match.group(1)) * {'ms': 0.001, 's': 1, 'm': 60, 'h': 3600}[match.group(2)]
    parts = value.replace(',', '.').split(':')
    if len(parts) not in (2, 3):
        raise ValueError('Invalid subtitle timestamp')
    return sum(float(part) * 60 ** index for index, part in enumerate(reversed(parts)))


def normalize_segments(segments):
    result = []
    for segment in segments:
        start, end = float(segment['start']), float(segment['end'])
        text = html.unescape(re.sub(r'<[^>]*>', '', str(segment['text']))).strip()
        text = re.sub(r'\s+', ' ', text)
        if not text or not math.isfinite(start) or not math.isfinite(end) or start < 0 or end <= start:
            continue
        if result and result[-1]['text'] == text and start < result[-1]['end']:
            result[-1]['end'] = max(result[-1]['end'], end)
        else:
            result.append({'start': round(start, 3), 'end': round(end, 3), 'text': text})
    return sorted(result, key=lambda segment: segment['start'])


def parse_subtitles(content, extension):
    segments = []
    if extension in {'json', 'json3'}:
        data = json.loads(content)
        for event in data.get('events', []):
            start = float(event.get('tStartMs', 0)) / 1000
            duration = float(event.get('dDurationMs', 0)) / 1000
            segments.append({'start': start, 'end': start + duration,
                             'text': ''.join(part.get('utf8', '') for part in event.get('segs', []))})
        for cue in data.get('body', []):
            segments.append({'start': cue['from'], 'end': cue['to'], 'text': cue['content']})
    elif extension in {'ttml', 'xml'}:
        root = ET.fromstring(content)
        for node in root.iter():
            if node.tag.rsplit('}', 1)[-1] != 'p':
                continue
            begin, end = node.get('begin'), node.get('end')
            if begin and end:
                segments.append({'start': timestamp(begin), 'end': timestamp(end),
                                 'text': ''.join(node.itertext())})
    elif extension in {'vtt', 'srt'}:
        for block in re.split(r'\n\s*\n', content.replace('\r\n', '\n').lstrip('\ufeff')):
            lines = block.splitlines()
            for index, line in enumerate(lines):
                if '-->' not in line:
                    continue
                begin, end = line.split('-->', 1)
                segments.append({'start': timestamp(begin), 'end': timestamp(end.strip().split()[0]),
                                 'text': ' '.join(lines[index + 1:])})
                break
    else:
        raise ValueError('Unsupported subtitle format')
    result = normalize_segments(segments)
    if not result:
        raise ValueError('No readable timed subtitle text was found')
    return result


def srt_timestamp(seconds):
    milliseconds = max(0, round(float(seconds) * 1000))
    seconds, milliseconds = divmod(milliseconds, 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f'{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}'


def to_srt(segments):
    return '\n\n'.join(f"{index}\n{srt_timestamp(cue['start'])} --> {srt_timestamp(cue['end'])}\n{cue['text']}"
                       for index, cue in enumerate(segments, 1)) + '\n'


def cue_batches(segments, max_characters=6000, max_cues=40):
    batch, size = [], 0
    for index, cue in enumerate(segments):
        text = cue['text']
        if len(text) > max_characters:
            raise ValueError('A subtitle cue is too long for translation')
        if batch and (size + len(text) > max_characters or len(batch) >= max_cues):
            yield batch
            batch, size = [], 0
        batch.append({'id': index, 'text': text})
        size += len(text)
    if batch:
        yield batch
