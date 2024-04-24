from typing import List, Tuple, Any, Iterable
import requests
import os
import regex
from pathlib import Path
import json


UNICODE_VERSION = '15.1.0'
EMOJI_UNICODE_VERSION = '.'.join(UNICODE_VERSION.split('.')[:2])

ROOT_PATH = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT_PATH / 'common' / 'myunicode'

# e.g. simple character:
#   0023;NUMBER SIGN;Po;0;ET;;;;;N;;;;;
# or character range First/Last:
#   F0000;<Plane 15 Private Use, Last>;Co;0;L;;;;;N;;;;;
CHARACTER_REGEX = regex.compile(r'^(?<code>[\da-fA-F]+);(?:(?:<(?<range>[^\n;]+), (?<range_type>First|Last)>)|(?<name>[^\n;]+));(?<category>[a-zA-Z]+);(?<combining>\d+)(?:;[^\n;]*){11}$')

# e.g. 11AB0..11ABF; Unified Canadian Aboriginal Syllabics Extended-A
BLOCK_REGEX = regex.compile(r'^(?<start>[0-9a-fA-F]+)..(?<stop>[0-9a-fA-F]+)\s*;(?<name>.+)$')

# e.g. 0000..001F    ; Common # Cc  [32] <control-0000>..<control-001F>
# or   0020          ; Common # Zs       SPACE
SCRIPT_REGEX = regex.compile(r'^(?<start>[0-9a-fA-F]+)(?:..(?<stop>[0-9a-fA-F]+))?\s*;(?<script>[^#]+)#.*$')

# e.g  003A	COLON
# or       * also used to denote division or scale; for that mathematical use 2236 is preferred
NAMES_LIST_REGEX = regex.compile(r'^(?P<code>[0-9A-Fa-f]+)\t(?P<name>.*)$')

# e.g. 1FA74         ; Extended_Pictographic# E13.0  [1] (🩴)       thong sandal
# or   1FA75..1FA77  ; Extended_Pictographic# E0.0   [3] (🩵..🩷)    <reserved-1FA75>..<reserved-1FA77>
EMOJI_REGEX = regex.compile(r'^(?<start>[0-9a-fA-F]+)(?:..(?<stop>[0-9a-fA-F]+))?\s*;.*(?<version>E\d+\.\d+).*$')

# e.g. 231A..231B    ; Basic_Emoji          ; watch                # E1.1  [2] (⌚..⌛)
# or   1F1F9 1F1F1   ; Emoji_Flag_Sequence  ; flag: Timor-Leste    # E6.0  [1] (🇹🇱)
EMOJI_SEQ_REGEX = regex.compile(r'^(?P<sequence>[^#;\n]*)[^\S\r\n]*;(?P<field_type>[^#;\n]*)[^\S\r\n]*;(?P<name>[^#;\n]*)[^\S\r\n]*# *(?P<version>E\d+\.\d+) [^\r\n]*$')

# e.g. 1F468 200D 1F466 ; RGI_Emoji_ZWJ_Sequence ; family: man, boy # E4.0 [1] (👨‍👦)
EMOJI_ZWJ_SEQ_REGEX = regex.compile(r'^(?<sequence>[0-9a-fA-F ]+);[^;]+;(?<name>[^#]+).*# *(?<version>E\d+\.\d+).*$')

# 09BC          ; 1.1 #       BENGALI SIGN NUKTA
# 09BE..09C4    ; 1.1 #   [7] BENGALI VOWEL SIGN AA..BENGALI VOWEL SIGN VOCALIC RR
DERIVED_AGE_REGEX = regex.compile(r'^(?<start>[0-9a-fA-F]+)(?:..(?<stop>[0-9a-fA-F]+))?\s*;\s*(?<version>\d+\.\d+)\s*#.*$')


def get_data_lines(lines: Iterable[str]) -> Iterable[str]:
    lines = map(str.strip, lines)
    return (l for l in lines if len(l) > 0 and not l.startswith('#'))


def ranges_to_bisect(ranges: List[Tuple[int, int, Any]]) -> List[Tuple[int, Any]]:
    # ensure proper order for bisect
    ranges.sort(key=lambda x: x[0])

    # compress continuous ranges
    compressed = []
    for r in ranges:
        # if current script range extends the previous one
        if len(compressed) > 0 and r[0] == compressed[-1][1] + 1 and r[2] == compressed[-1][2]:
            # extend last range
            compressed[-1] = (compressed[-1][0], r[1], compressed[-1][2])
        else:
            # add new range
            compressed.append(r)

    ranges = compressed

    # convert to bisect format (start, name)
    starts = [0]
    names = [None]

    for start, stop, name in ranges:
        # check if there is a gap between the last range and this one
        if starts[-1] == start:  # no gap
            # overwrite previous None range
            # and remove the gap
            names[-1] = name
        else:  # gap
            # insert new range after previous None range
            # keeping the gap
            starts.append(start)
            names.append(name)

        # assume that this range is the last one
        # and insert a None range
        starts.append(stop + 1)
        names.append(None)
    
    return list(zip(starts, names))


def download_character_data():
    r = requests.get(f'https://www.unicode.org/Public/{UNICODE_VERSION}/ucd/UnicodeData.txt')

    character_data = {}
    special_ranges_starts = {}
    special_ranges_stops = {}
    special_ranges_data = {}

    for line in get_data_lines(r.text.splitlines()):
        m = CHARACTER_REGEX.match(line)
        
        assert m is not None, f'Invalid line: {line}'

        code = m.group('code')
        range_name = m.group('range')
        name = m.group('name')
        category = m.group('category')
        combining = int(m.group('combining'))

        if range_name is not None:
            if m.group('range_type') == 'First':
                special_ranges_starts[range_name] = int(code, 16)
            else:
                special_ranges_stops[range_name] = int(code, 16)
            special_ranges_data[range_name] = {
                'name': range_name,
                'category': category,
                'combining': combining
            }
        else:
            character_data[code] = {
                'name': name,
                'category': category,
                'combining': combining,
            }
    
    special_ranges = []
    for range_name, start in special_ranges_starts.items():
        stop = special_ranges_stops[range_name]
        data = special_ranges_data[range_name]
        special_ranges.append((start, stop, data))

    return character_data, ranges_to_bisect(special_ranges)


def download_blocks():
    r = requests.get(f'https://www.unicode.org/Public/{UNICODE_VERSION}/ucd/Blocks.txt')
    blocks = []
    for line in get_data_lines(r.text.splitlines()):
        m = BLOCK_REGEX.search(line)
        start = int(m.group('start'), 16)
        stop = int(m.group('stop'), 16)
        name = m.group('name').strip()

        blocks.append((start, stop, name))

    return ranges_to_bisect(blocks)


def download_scripts():
    r = requests.get(f'https://www.unicode.org/Public/{UNICODE_VERSION}/ucd/Scripts.txt')
    scripts = []
    for line in get_data_lines(r.text.splitlines()):
        m = SCRIPT_REGEX.search(line)
        start = int(m.group('start'), 16)
        stop = int(m.group('stop'), 16) if m.group('stop') is not None else start
        script = m.group('script').strip()

        scripts.append((start, stop, script))

    return ranges_to_bisect(scripts)


def download_names_list():
    r = requests.get(f'https://www.unicode.org/Public/{UNICODE_VERSION}/ucd/NamesList.txt')
    code2name = dict()
    for line in get_data_lines(r.text.splitlines()):
        m = NAMES_LIST_REGEX.match(line)

        if m:
            code = int(m.group('code'), base=16)
            name = m.group('name')

            code2name[code] = name

    return code2name


def download_emoji_ranges():
    r = requests.get(f'https://www.unicode.org/Public/{UNICODE_VERSION}/ucd/emoji/emoji-data.txt')
    versions = {}
    emojis = set()
    for line in get_data_lines(r.text.splitlines()):
        m = EMOJI_REGEX.search(line)
        start = int(m.group('start'), base=16)
        stop = int(m.group('stop'), base=16) if m.group('stop') is not None else start
        version = m.group('version')
        assert version.startswith('E'), f'Invalid version: {version}'

        for e in range(start, stop + 1):
            emojis.add(e)
            versions[chr(e)] = version

    # remove ZWJ
    emojis.remove(0x200D)

    # remove ASCII
    for emoji in list(emojis):
        if chr(emoji).isascii():
            emojis.remove(emoji)

    # extract emoji character code ranges
    ranges = []
    for e in sorted(emojis):
        # if there was a gap
        if len(ranges) == 0 or e > ranges[-1][1] + 1:
            # add new range
            ranges.append((e, e))
        else:
            # extend last range
            ranges[-1] = (ranges[-1][0], e)

    return ranges_to_bisect([(start, stop, True) for start, stop in ranges]), versions


def download_emoji_seqs():
    r = requests.get(f'https://unicode.org/Public/emoji/{EMOJI_UNICODE_VERSION}/emoji-sequences.txt')
    names_list = download_names_list()
    emoji2name = {}
    versions = {}
    for line in get_data_lines(r.text.splitlines()):
        m = EMOJI_SEQ_REGEX.match(line)

        sequence_group = m.group('sequence').strip()
        field_type_group = m.group('field_type').strip()
        name_group = m.group('name').strip()
        # characters may be escaped with \x{hex}
        name_group = regex.sub(r'\\x\{([0-9A-Fa-f]+)\}', lambda m: chr(int(m.group(1), 16)), name_group)
        version_group = m.group('version').strip()
        assert version_group.startswith('E'), f'Invalid version: {version_group}'
        
        if '..' in sequence_group:
            from_code, to_code = sequence_group.split('..')
            from_code = int(from_code, 16)
            to_code = int(to_code, 16)
            emojis = [chr(code) for code in range(from_code, to_code+1)]
            names = [names_list[code] for code in range(from_code, to_code+1)]
        else:
            codes = sequence_group.split()
            emojis = [''.join([chr(int(code, 16)) for code in codes])]  # one emoji wrapped in the list
            names = [name_group]

        for emoji, name in zip(emojis, names):
            emoji2name[emoji] = name.upper()
            versions[emoji] = version_group

    return emoji2name, versions


def download_emoji_zwj_seqs():
    r = requests.get(f'https://unicode.org/Public/emoji/{EMOJI_UNICODE_VERSION}/emoji-zwj-sequences.txt')
    names = {}
    versions = {}
    for line in get_data_lines(r.text.splitlines()):
        m = EMOJI_ZWJ_SEQ_REGEX.match(line)
        
        sequence = ''.join(chr(int(code, 16)) for code in m.group('sequence').split())
        name = m.group('name').strip()
        version = m.group('version').strip()
        assert version.startswith('E'), f'Invalid version: {version}'

        names[sequence] = name.upper()
        versions[sequence] = version

    return names, versions


def download_derived_age():
    r = requests.get(f'https://www.unicode.org/Public/{UNICODE_VERSION}/ucd/DerivedAge.txt')
    versions = {}
    for line in get_data_lines(r.text.splitlines()):
        m = DERIVED_AGE_REGEX.match(line)
        start = int(m.group('start'), 16)
        stop = int(m.group('stop'), 16) if m.group('stop') is not None else start
        version = m.group('version')

        for e in range(start, stop + 1):
            versions[chr(e)] = version

    return versions


def create_myunicode_data():
    character_data, special_ranges = download_character_data()
    blocks_bisect = download_blocks()
    scripts_bisect = download_scripts()
    emojis_bisect, emoji_versions = download_emoji_ranges()
    emoji_seqs, emoji_seq_versions = download_emoji_seqs()
    emoji_zwj_seqs, emoji_zwj_seq_versions = download_emoji_zwj_seqs()
    unicode_versions = download_derived_age()

    emoji_versions.update(emoji_seq_versions)
    emoji_versions.update(emoji_zwj_seq_versions)

    data = {
        'name': {code: character_data[code]['name'] for code in character_data},
        'category': {code: character_data[code]['category'] for code in character_data},
        'combining': {code: character_data[code]['combining'] for code in character_data},
        'special': {
            'starts': [start for start, _ in special_ranges],
            'data': [data for _, data in special_ranges],
        },
        'blocks': {
            'starts': [start for start, _ in blocks_bisect],
            'names': [name for _, name in blocks_bisect],
        },
        'scripts': {
            'starts': [start for start, _ in scripts_bisect],
            'names': [name for _, name in scripts_bisect],
        },
        'emojis': {
            'starts': [start for start, _ in emojis_bisect],
            'is_emoji': [is_emoji == True for _, is_emoji in emojis_bisect],
        },
        'emoji_sequences': emoji_seqs,
        'emoji_zwj_sequences': emoji_zwj_seqs,
        'versions': {
            'unicode': unicode_versions,
            'emoji': emoji_versions,
        },
    }

    os.makedirs(DATA_PATH, exist_ok=True)
    with open(DATA_PATH / 'myunicode.json', 'w') as f:
        json.dump(data, f, indent=None, separators=(',', ':'))


if __name__ == "__main__":
    print('Downloading unicode files...')
    create_myunicode_data()
    print('Done')
