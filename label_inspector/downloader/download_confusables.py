import collections
import copy
import json
import sys
import os
from pathlib import Path

import ens_normalize
import requests
from contextlib import contextmanager
import unicodedata

from ens_normalize import DisallowedSequence

import label_inspector.common.myunicode as myunicode
from typing import List, Dict, Callable

import regex
from tqdm import tqdm

from label_inspector.common.myunicode import script_of

LIST_OF_NONCONFUSABLES = [
    # keycaps
    '0⃣',  # 0
    '1⃣',  # 1
    '2⃣',  # 2
    '3⃣',  # 3
    '4⃣',  # 4
    '5⃣',  # 5
    '6⃣',  # 6
    '7⃣',  # 7
    '8⃣',  # 8
    '9⃣',  # 9
    '*⃣',  # *
    '#⃣',  # #
]

CUSTOM_MAPPING = {' ': ['\xa0'],
               'A': ['A', 'Ⓐ', 'Ａ', 'À', 'Á', 'Â', 'Ầ', 'Ấ', 'Ẫ', 'Ẩ', 'Ã', 'Ā', 'Ă', 'Ằ', 'Ắ', 'Ẵ', 'Ẳ', 'Ȧ', 'Ǡ', 'Ä',
                     'Ǟ', 'Ả', 'Å', 'Ǻ', 'Ǎ', 'Ȁ', 'Ȃ', 'Ạ', 'Ậ', 'Ặ', 'Ḁ', 'Ą', 'Ⱥ', 'Ɐ'],
               'AA': ['Ꜳ'],
               'AE': ['Æ', 'Ǽ', 'Ǣ'],
               'AO': ['Ꜵ'],
               'AU': ['Ꜷ'],
               'AV': ['Ꜹ', 'Ꜻ'],
               'AY': ['Ꜽ'],
               'B': ['B', 'Ⓑ', 'Ｂ', 'Ḃ', 'Ḅ', 'Ḇ', 'Ƀ', 'Ƃ', 'Ɓ', 'ß'],
               'C': ['C', 'Ⓒ', 'Ｃ', 'Ć', 'Ĉ', 'Ċ', 'Č', 'Ç', 'Ḉ', 'Ƈ', 'Ȼ', 'Ꜿ'],
               'D': ['D', 'Ⓓ', 'Ｄ', 'Ḋ', 'Ď', 'Ḍ', 'Ḑ', 'Ḓ', 'Ḏ', 'Đ', 'Ƌ', 'Ɗ', 'Ɖ', 'Ꝺ'],
               'DZ': ['Ǳ', 'Ǆ'],
               'Dz': ['ǲ', 'ǅ'],
               'E': ['E', 'Ⓔ', 'Ｅ', 'È', 'É', 'Ê', 'Ề', 'Ế', 'Ễ', 'Ể', 'Ẽ', 'Ē', 'Ḕ', 'Ḗ', 'Ĕ', 'Ė', 'Ë', 'Ẻ', 'Ě', 'Ȅ',
                     'Ȇ', 'Ẹ', 'Ệ', 'Ȩ', 'Ḝ', 'Ę', 'Ḙ', 'Ḛ', 'Ɛ', 'Ǝ'],
               'F': ['F', 'Ⓕ', 'Ｆ', 'Ḟ', 'Ƒ', 'Ꝼ'],
               'G': ['G', 'Ⓖ', 'Ｇ', 'Ǵ', 'Ĝ', 'Ḡ', 'Ğ', 'Ġ', 'Ǧ', 'Ģ', 'Ǥ', 'Ɠ', 'Ꞡ', 'Ᵹ', 'Ꝿ'],
               'H': ['H', 'Ⓗ', 'Ｈ', 'Ĥ', 'Ḣ', 'Ḧ', 'Ȟ', 'Ḥ', 'Ḩ', 'Ḫ', 'Ħ', 'Ⱨ', 'Ⱶ', 'Ɥ'],
               'I': ['I', 'Ⓘ', 'Ｉ', 'Ì', 'Í', 'Î', 'Ĩ', 'Ī', 'Ĭ', 'İ', 'Ï', 'Ḯ', 'Ỉ', 'Ǐ', 'Ȉ', 'Ȋ', 'Ị', 'Į', 'Ḭ',
                     'Ɨ'],
               'J': ['J', 'Ⓙ', 'Ｊ', 'Ĵ', 'Ɉ'],
               'K': ['K', 'Ⓚ', 'Ｋ', 'Ḱ', 'Ǩ', 'Ḳ', 'Ķ', 'Ḵ', 'Ƙ', 'Ⱪ', 'Ꝁ', 'Ꝃ', 'Ꝅ', 'Ꞣ'],
               'L': ['L', 'Ⓛ', 'Ｌ', 'Ŀ', 'Ĺ', 'Ľ', 'Ḷ', 'Ḹ', 'Ļ', 'Ḽ', 'Ḻ', 'Ł', 'Ƚ', 'Ɫ', 'Ⱡ', 'Ꝉ', 'Ꝇ', 'Ꞁ'],
               'LJ': ['Ǉ'],
               'Lj': ['ǈ'],
               'M': ['M', 'Ⓜ', 'Ｍ', 'Ḿ', 'Ṁ', 'Ṃ', 'Ɱ', 'Ɯ'],
               'N': ['N', 'Ⓝ', 'Ｎ', 'Ǹ', 'Ń', 'Ñ', 'Ṅ', 'Ň', 'Ṇ', 'Ņ', 'Ṋ', 'Ṉ', 'Ƞ', 'Ɲ', 'Ꞑ', 'Ꞥ'],
               'NJ': ['Ǌ'],
               'Nj': ['ǋ'],
               'O': ['O', 'Ⓞ', 'Ｏ', 'Ò', 'Ó', 'Ô', 'Ồ', 'Ố', 'Ỗ', 'Ổ', 'Õ', 'Ṍ', 'Ȭ', 'Ṏ', 'Ō', 'Ṑ', 'Ṓ', 'Ŏ', 'Ȯ', 'Ȱ',
                     'Ö', 'Ȫ', 'Ỏ', 'Ő', 'Ǒ', 'Ȍ', 'Ȏ', 'Ơ', 'Ờ', 'Ớ', 'Ỡ', 'Ở', 'Ợ', 'Ọ', 'Ộ', 'Ǫ', 'Ǭ', 'Ø', 'Ǿ', 'Ɔ',
                     'Ɵ', 'Ꝋ', 'Ꝍ'],
               'OI': ['Ƣ'],
               'OO': ['Ꝏ'],
               'OU': ['Ȣ'],
               'P': ['P', 'Ⓟ', 'Ｐ', 'Ṕ', 'Ṗ', 'Ƥ', 'Ᵽ', 'Ꝑ', 'Ꝓ', 'Ꝕ'],
               'Q': ['Q', 'Ⓠ', 'Ｑ', 'Ꝗ', 'Ꝙ', 'Ɋ'],
               'R': ['R', 'Ⓡ', 'Ｒ', 'Ŕ', 'Ṙ', 'Ř', 'Ȑ', 'Ȓ', 'Ṛ', 'Ṝ', 'Ŗ', 'Ṟ', 'Ɍ', 'Ɽ', 'Ꝛ', 'Ꞧ', 'Ꞃ'],
               'S': ['S', 'Ⓢ', 'Ｓ', 'Ś', 'Ṥ', 'Ŝ', 'Ṡ', 'Š', 'Ṧ', 'Ṣ', 'Ṩ', 'Ș', 'Ş', 'Ȿ', 'Ꞩ', 'Ꞅ'],
               'T': ['T', 'Ⓣ', 'Ｔ', 'Ṫ', 'Ť', 'Ṭ', 'Ț', 'Ţ', 'Ṱ', 'Ṯ', 'Ŧ', 'Ƭ', 'Ʈ', 'Ⱦ', 'Ꞇ'],
               # 'Th': ['Þ'],
               'TZ': ['Ꜩ'],
               'U': ['U', 'Ⓤ', 'Ｕ', 'Ù', 'Ú', 'Û', 'Ũ', 'Ṹ', 'Ū', 'Ṻ', 'Ŭ', 'Ü', 'Ǜ', 'Ǘ', 'Ǖ', 'Ǚ', 'Ủ', 'Ů', 'Ű', 'Ǔ',
                     'Ȕ', 'Ȗ', 'Ư', 'Ừ', 'Ứ', 'Ữ', 'Ử', 'Ự', 'Ụ', 'Ṳ', 'Ų', 'Ṷ', 'Ṵ', 'Ʉ'],
               'V': ['V', 'Ⓥ', 'Ｖ', 'Ṽ', 'Ṿ', 'Ʋ', 'Ꝟ', 'Ʌ'],
               'VY': ['Ꝡ'],
               'W': ['W', 'Ⓦ', 'Ｗ', 'Ẁ', 'Ẃ', 'Ŵ', 'Ẇ', 'Ẅ', 'Ẉ', 'Ⱳ'],
               'X': ['X', 'Ⓧ', 'Ｘ', 'Ẋ', 'Ẍ'],
               'Y': ['Y', 'Ⓨ', 'Ｙ', 'Ỳ', 'Ý', 'Ŷ', 'Ỹ', 'Ȳ', 'Ẏ', 'Ÿ', 'Ỷ', 'Ỵ', 'Ƴ', 'Ɏ', 'Ỿ'],
               'Z': ['Z', 'Ⓩ', 'Ｚ', 'Ź', 'Ẑ', 'Ż', 'Ž', 'Ẓ', 'Ẕ', 'Ƶ', 'Ȥ', 'Ɀ', 'Ⱬ', 'Ꝣ'],
               'a': ['a', 'ⓐ', 'ａ', 'ẚ', 'à', 'á', 'â', 'ầ', 'ấ', 'ẫ', 'ẩ', 'ã', 'ā', 'ă', 'ằ', 'ắ', 'ẵ', 'ẳ', 'ȧ', 'ǡ',
                     'ä', 'ǟ', 'ả', 'å', 'ǻ', 'ǎ', 'ȁ', 'ȃ', 'ạ', 'ậ', 'ặ', 'ḁ', 'ą', 'ⱥ', 'ɐ', 'ɑ'],
               'aa': ['ꜳ'],
               'ae': ['æ', 'ǽ', 'ǣ'],
               'ao': ['ꜵ'],
               'au': ['ꜷ'],
               'av': ['ꜹ', 'ꜻ'],
               'ay': ['ꜽ'],
               'b': ['b', 'ⓑ', 'ｂ', 'ḃ', 'ḅ', 'ḇ', 'ƀ', 'ƃ', 'ɓ', 'ß'],
               'c': ['c', 'ⓒ', 'ｃ', 'ć', 'ĉ', 'ċ', 'č', 'ç', 'ḉ', 'ƈ', 'ȼ', 'ꜿ', 'ↄ'],
               'd': ['d', 'ⓓ', 'ｄ', 'ḋ', 'ď', 'ḍ', 'ḑ', 'ḓ', 'ḏ', 'đ', 'ƌ', 'ɖ', 'ɗ', 'ꝺ'],
               'dz': ['ǳ', 'ǆ'],
               'e': ['e', 'ⓔ', 'ｅ', 'è', 'é', 'ê', 'ề', 'ế', 'ễ', 'ể', 'ẽ', 'ē', 'ḕ', 'ḗ', 'ĕ', 'ė', 'ë', 'ẻ', 'ě', 'ȅ',
                     'ȇ', 'ẹ', 'ệ', 'ȩ', 'ḝ', 'ę', 'ḙ', 'ḛ', 'ɇ', 'ɛ', 'ǝ'],
               'f': ['f', 'ⓕ', 'ｆ', 'ḟ', 'ƒ', 'ꝼ'],
               'ff': ['ﬀ'],
               'fi': ['ﬁ'],
               'fl': ['ﬂ'],
               'ffi': ['ﬃ'],
               'ffl': ['ﬄ'],
               'g': ['g', 'ⓖ', 'ｇ', 'ǵ', 'ĝ', 'ḡ', 'ğ', 'ġ', 'ǧ', 'ģ', 'ǥ', 'ɠ', 'ꞡ', 'ᵹ', 'ꝿ'],
               'h': ['h', 'ⓗ', 'ｈ', 'ĥ', 'ḣ', 'ḧ', 'ȟ', 'ḥ', 'ḩ', 'ḫ', 'ẖ', 'ħ', 'ⱨ', 'ⱶ', 'ɥ'],
               'hv': ['ƕ'],
               'i': ['i', 'ⓘ', 'ｉ', 'ì', 'í', 'î', 'ĩ', 'ī', 'ĭ', 'ï', 'ḯ', 'ỉ', 'ǐ', 'ȉ', 'ȋ', 'ị', 'į', 'ḭ', 'ɨ',
                     'ı'],
               'j': ['j', 'ⓙ', 'ｊ', 'ĵ', 'ǰ', 'ɉ'],
               'k': ['k', 'ⓚ', 'ｋ', 'ḱ', 'ǩ', 'ḳ', 'ķ', 'ḵ', 'ƙ', 'ⱪ', 'ꝁ', 'ꝃ', 'ꝅ', 'ꞣ'],
               'l': ['l', 'ⓛ', 'ｌ', 'ŀ', 'ĺ', 'ľ', 'ḷ', 'ḹ', 'ļ', 'ḽ', 'ḻ', 'ſ', 'ł', 'ƚ', 'ɫ', 'ⱡ', 'ꝉ', 'ꞁ', 'ꝇ'],
               'lj': ['ǉ'],
               'm': ['m', 'ⓜ', 'ｍ', 'ḿ', 'ṁ', 'ṃ', 'ɱ', 'ɯ'],
               'n': ['n', 'ñ', 'n', 'ⓝ', 'ｎ', 'ǹ', 'ń', 'ñ', 'ṅ', 'ň', 'ṇ', 'ņ', 'ṋ', 'ṉ', 'ƞ', 'ɲ', 'ŉ', 'ꞑ', 'ꞥ', 'л',
                     'ԉ'],
               'nj': ['ǌ'],
               'o': ['߀', 'o', 'ⓞ', 'ｏ', 'ò', 'ó', 'ô', 'ồ', 'ố', 'ỗ', 'ổ', 'õ', 'ṍ', 'ȭ', 'ṏ', 'ō', 'ṑ', 'ṓ', 'ŏ', 'ȯ',
                     'ȱ', 'ö', 'ȫ', 'ỏ', 'ő', 'ǒ', 'ȍ', 'ȏ', 'ơ', 'ờ', 'ớ', 'ỡ', 'ở', 'ợ', 'ọ', 'ộ', 'ǫ', 'ǭ', 'ø', 'ǿ',
                     'ɔ', 'ꝋ', 'ꝍ', 'ɵ'],
               'oe': ['Œ', 'œ'],
               'oi': ['ƣ'],
               'ou': ['ȣ'],
               'oo': ['ꝏ'],
               'p': ['p', 'ⓟ', 'ｐ', 'ṕ', 'ṗ', 'ƥ', 'ᵽ', 'ꝑ', 'ꝓ', 'ꝕ'],
               'q': ['q', 'ⓠ', 'ｑ', 'ɋ', 'ꝗ', 'ꝙ'],
               'r': ['r', 'ⓡ', 'ｒ', 'ŕ', 'ṙ', 'ř', 'ȑ', 'ȓ', 'ṛ', 'ṝ', 'ŗ', 'ṟ', 'ɍ', 'ɽ', 'ꝛ', 'ꞧ', 'ꞃ'],
               's': ['s', 'ⓢ', 'ｓ', 'ś', 'ṥ', 'ŝ', 'ṡ', 'š', 'ṧ', 'ṣ', 'ṩ', 'ș', 'ş', 'ȿ', 'ꞩ', 'ꞅ', 'ẛ'],
               't': ['t', 'ⓣ', 'ｔ', 'ṫ', 'ẗ', 'ť', 'ṭ', 'ț', 'ţ', 'ṱ', 'ṯ', 'ŧ', 'ƭ', 'ʈ', 'ⱦ', 'ꞇ'],
               'tz': ['ꜩ'],
               'u': ['u', 'ⓤ', 'ｕ', 'ù', 'ú', 'û', 'ũ', 'ṹ', 'ū', 'ṻ', 'ŭ', 'ü', 'ǜ', 'ǘ', 'ǖ', 'ǚ', 'ủ', 'ů', 'ű', 'ǔ',
                     'ȕ', 'ȗ', 'ư', 'ừ', 'ứ', 'ữ', 'ử', 'ự', 'ụ', 'ṳ', 'ų', 'ṷ', 'ṵ', 'ʉ'],
               'v': ['v', 'ⓥ', 'ｖ', 'ṽ', 'ṿ', 'ʋ', 'ꝟ', 'ʌ'],
               'vy': ['ꝡ'],
               'w': ['w', 'ⓦ', 'ｗ', 'ẁ', 'ẃ', 'ŵ', 'ẇ', 'ẅ', 'ẘ', 'ẉ', 'ⱳ'],
               'x': ['x', 'ⓧ', 'ｘ', 'ẋ', 'ẍ'],
               'y': ['y', 'ⓨ', 'ｙ', 'ỳ', 'ý', 'ŷ', 'ỹ', 'ȳ', 'ẏ', 'ÿ', 'ỷ', 'ẙ', 'ỵ', 'ƴ', 'ɏ', 'ỿ'],
               'z': ['z', 'ⓩ', 'ｚ', 'ź', 'ẑ', 'ż', 'ž', 'ẓ', 'ẕ', 'ƶ', 'ȥ', 'ɀ', 'ⱬ', 'ꝣ']}

UNICODE_VERSION = '16.0.0'

CONFUSABLES_URL = f'https://www.unicode.org/Public/security/{UNICODE_VERSION}/confusables.txt'

CONFUSABLES_TXT_PATH = Path(__file__).resolve().parent / 'confusables.txt'
CONFUSABLES_JSON_PATH = Path(__file__).resolve().parent / 'confusables.json'


def is_normalized(character):
    if len(character) == 1 and ord(character) in ens_normalize.normalization.NORMALIZATION.valid: return True
    return ens_normalize.is_ens_normalized(character)


@contextmanager
def download_confusables():
    """Download confusables.txt and cleanup afterward."""
    assert not CONFUSABLES_TXT_PATH.exists(), 'confusables.txt already exists!'
    r = requests.get(CONFUSABLES_URL)
    try:
        os.makedirs(CONFUSABLES_TXT_PATH.parent, exist_ok=True)
        with open(CONFUSABLES_TXT_PATH, 'w') as f:
            f.write(r.text)
        yield
    finally:
        CONFUSABLES_TXT_PATH.unlink(missing_ok=True)


def hex_to_char(hex_string: str) -> str:
    """Convert hex string to character (e.g. '0061' to 'a')."""
    return chr(int(hex_string, 16))


SIMPLE = regex.compile(r'^[a-z0-9-]$')


class Confusable:
    def __init__(self):
        self.canonical_confusables: List[str] = []
        self.noncanonical_confusables: List[str] = []

    def set_canonical(self, canonical: str):
        try:
            self.canonical_confusables.remove(canonical)
        except ValueError:
            pass
        try:
            self.noncanonical_confusables.remove(canonical)
        except ValueError:
            pass
        self.canonical_confusables.insert(0, canonical)

    def set_canonical_if_not_set(self, canonical: str):
        if canonical not in self.canonical_confusables:
            self.canonical_confusables.append(canonical)
        try:
            self.noncanonical_confusables.remove(canonical)
        except ValueError:
            pass

    def append_potential_canonical(self, confusable: str):
        self.canonical_confusables.append(confusable)

    def all_confusables(self):
        return self.canonical_confusables + self.noncanonical_confusables

    def append_noncanonical(self, confusable: str):
        """It also changes canonical if is ASCII"""
        if SIMPLE.match(confusable):
            self.set_canonical_if_not_set(confusable)
        else:
            if confusable not in self.all_confusables():
                self.noncanonical_confusables.append(confusable)

    def extend_noncanonical(self, confusables: List[str]):
        for confusable in confusables:
            self.append_noncanonical(confusable)

    def extend_potential_canonical(self, confusables: List[str]):
        for confusable in confusables:
            self.append_potential_canonical(confusable)

    def update(self, c):
        self.extend_noncanonical(c.noncanonical_confusables)
        for ca in c.canonical_confusables:
            self.set_canonical_if_not_set(ca)

    def uniq(self, remove_char=None):
        self.canonical_confusables = uniq(self.canonical_confusables)
        if remove_char in self.canonical_confusables[1:]:
            self.canonical_confusables.remove(remove_char)

        self.noncanonical_confusables = uniq_additional(self.noncanonical_confusables, self.canonical_confusables)
        if remove_char in self.noncanonical_confusables:
            self.noncanonical_confusables.remove(remove_char)

    def to_json(self):
        return [self.canonical_confusables[0], self.canonical_confusables[1:] + self.noncanonical_confusables]

    def __eq__(self, other): 
        if not isinstance(other, Confusable):
            return NotImplemented

        return self.canonical_confusables == other.canonical_confusables and self.noncanonical_confusables == other.noncanonical_confusables

def read_confusables_txt(path=CONFUSABLES_TXT_PATH) -> Dict[str, Confusable]:
    """Read confusables.txt"""
    rules = collections.defaultdict(lambda: Confusable())
    for line in open(path, 'r'):
        if line.startswith('#'):
            continue
        line = line[:-1] if line[-1] == '\n' else line
        row = line.split(' ;\t')
        if len(row) >= 2:
            a = ''.join([hex_to_char(hex_string) for hex_string in row[0].split(' ')])
            b = ''.join([hex_to_char(hex_string) for hex_string in row[1].split(' ')])
            rules[a].append_potential_canonical(b)
    return rules


def uniq(l: List) -> List:
    """Return list with unique elements."""
    used = set()
    return [x for x in l if x not in used and (used.add(x) or True)]


def uniq_additional(l: List, additional: List) -> List:
    """Return list with unique elements."""
    used = set(additional)
    return [x for x in l if x not in used and (used.add(x) or True)]


def uniq_filter(l: List) -> List:
    """Return list with unique non-empty elements."""
    return [x for x in uniq(l) if x]


def custom() -> Dict[str, Confusable]:
    # https://www.npmjs.com/package/diacritic
    rules = collections.defaultdict(lambda: Confusable())
    for base, confusables in CUSTOM_MAPPING.items():
        for confusable in confusables:
            rules[confusable].append_potential_canonical(base)
    return rules


def normalizations() -> Dict[str, Confusable]:
    """Create confusable rules by normalizations."""
    upto = sys.maxunicode + 1
    rules = collections.defaultdict(lambda: Confusable())
    for i in range(0, upto):
        char = chr(i)
        variants = uniq_filter(all_variants(char))
        if len(variants) > 1 or (len(variants) == 1 and variants[0] != char):
            rules[char].extend_noncanonical(variants)
    return rules


def all_variants(s: str) -> List[str]:
    """Return all normalizations."""
    nfkd_form = unicodedata.normalize('NFKD', s)
    nfd_form = unicodedata.normalize('NFD', s)
    nfc_form = unicodedata.normalize('NFC', s)
    nfkc_form = unicodedata.normalize('NFKC', s)
    result = [nfkd_form, nfd_form, nfc_form, nfkc_form]
    if s in result:
        result.remove(s)
    return result


def remove_accents(input_str):
    """Removes accents by stripping combining characters after decomposition."""
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return u"".join([c for c in nfkd_form if not myunicode.combining(c)])


def apply_all_chars(func: Callable, noncanonical=True) -> Dict[str, Confusable]:
    """Applies a transformation for every Unicode char."""
    upto = sys.maxunicode + 1
    rules = collections.defaultdict(lambda: Confusable())
    for i in range(0, upto):
        char = chr(i)
        stripped = func(char)
        variants = uniq_filter([stripped] + all_variants(stripped))
        if len(variants) > 1 or (len(variants) == 1 and variants[0] != char):
            if noncanonical:
                rules[char].extend_noncanonical(variants)
            else:
                rules[char].extend_potential_canonical(variants)
    return rules


def removed_accents() -> Dict[str, Confusable]:
    return apply_all_chars(remove_accents, noncanonical=False)


def strip_accents(s: str, categories=('Mn',), n='NFD') -> str:
    """Removes accents by stripping characters within given categories."""
    return ''.join(c for c in unicodedata.normalize(n, s)
                   if myunicode.category(c) not in categories)


def strip_accents_nfd() -> Dict[str, Confusable]:
    return apply_all_chars(lambda x: strip_accents(x, n='NFD', categories=['Mn']), noncanonical=False)


def strip_accents_nfkd() -> Dict[str, Confusable]:
    return apply_all_chars(
        lambda x: strip_accents(x, n='NFKD', categories=['Mn', 'Zs', 'Nd', 'Sm', 'Po', 'Lm', 'Lo', 'Mc', 'So']),
        noncanonical=False)


def reorder(l: List[str]) -> List[str]:
    """Reorder list of string so in the first place is a character [a-z0-9-]."""
    simple = None
    for el in l:
        if regex.match(r'^[a-z0-9-]$', el):
            simple = el
            break
    if simple is not None:
        l.remove(simple)
        return [simple] + l
    else:
        return l


def uniq_and_reorder(c: Dict[str, Confusable]):
    """Remove duplicates from values of confusable rules and reorder them."""
    for key, confusable in c.items():
        confusable.uniq(key)
        # c[key] = reorder(u)


def forward_backward_transitive(rules: Dict[str, Confusable]) -> Dict[str, Confusable]:
    """Augments confusable rules. If the rules are: a->b; c->b then a->b,c; c->b,a."""
    reversed_c = collections.defaultdict(list)
    for key, confusable in tqdm(rules.items(), desc='Reversing'):
        for v in confusable.all_confusables():
            if key == v: continue
            reversed_c[v].append(key)

    new_rules = copy.deepcopy(rules)

    for key, confusable in tqdm(rules.items(), desc='Backward transitive'):
        for v in confusable.all_confusables():
            if key == v: continue
            new_rules[key].extend_noncanonical(reversed_c[v])
            # print(f'extend_noncanonical {key} -> {v} so {key} -> {reversed_c[v]}')
    return new_rules


def symmetric(rules: Dict[str, Confusable]) -> Dict[str, Confusable]:
    """Augments confusable rules. If the rules are: a->b then b->a."""
    # new_rules = collections.defaultdict(list)
    # new_rules.update(rules)
    new_rules = copy.deepcopy(rules)
    for key, confusable in tqdm(rules.items(), desc='Symmetric'):
        # new_rules[v].append_potential_canonical(v)
        for v in confusable.all_confusables():
            if key == v: continue
            if key not in new_rules[v].all_confusables():
                print(f'symmetric {key} -> {v} so {v} -> {key}')
            new_rules[v].append_noncanonical(key)
            # if new_rules[v].canonical is None:
            #     logging.warning(f'No canonical for {v}, adding confusable {key} {v == key}')
    return new_rules


class Confusables():
    """Generate confusable rules."""

    def __init__(self):

        # join rules
        self.rules: Dict[str, Confusable] = collections.defaultdict(lambda: Confusable())

    def generate(self):
        rule_generators = [
            read_confusables_txt,
            custom,
            normalizations,
            removed_accents,
            strip_accents_nfd,
            strip_accents_nfkd,
        ]

        for rule_generator in rule_generators:
            self.run_generator(rule_generator)

        uniq_and_reorder(self.rules)
        # json.dump(rules, open('c.json', 'w'), ensure_ascii=False, indent=2, sort_keys=True)

        # set canonical to itself if it is None
        self.set_canonical_to_itself()

        self.rules = forward_backward_transitive(self.rules)

        self.rules = symmetric(self.rules)

        # if SIMPLE as confusables then set it as canonical
        for character, confusable_obj in self.rules.items():
            if confusable_obj.canonical_confusables and SIMPLE.match(confusable_obj.canonical_confusables[0]):
                continue
            for confusable in confusable_obj.all_confusables():
                if SIMPLE.match(confusable):
                    self.rules[character].set_canonical(confusable)
                    break

        self.set_custom_nonconfusables()
        
        uniq_and_reorder(self.rules)

    def set_canonical_to_itself(self):
        new_rules = copy.deepcopy(self.rules)
        for key, confusable in new_rules.items():
            self.rules[key].set_canonical_if_not_set(key)
            for a_confusable in confusable.all_confusables():
                if a_confusable not in self.rules:
                    self.rules[a_confusable].append_potential_canonical(a_confusable)
                    print(f'{key} -> {a_confusable}, so for {a_confusable} canonical is {a_confusable}')

    def run_generator(self, generator: Callable):
        c_other = generator()
        for key, confusable in c_other.items():
            if key not in self.rules:
                print(f'{generator.__name__} {key} {confusable.canonical_confusables} {confusable.noncanonical_confusables}')
            
            copied = copy.deepcopy(self.rules[key])    
            self.rules[key].update(confusable)
            if copied != self.rules[key]:
                print(
                    f'{generator.__name__} {key} {copied.canonical_confusables} {copied.noncanonical_confusables} {self.rules[key].canonical_confusables} {self.rules[key].noncanonical_confusables}')

        print('added:', len(c_other), 'uniq:', len(self.rules))

    def save(self, path: Path):
        r = {}
        for k, confusable in self.rules.items():
            try:
                r[k] = confusable.to_json()
            except IndexError as e:
                print([k], confusable.canonical_confusables, confusable.noncanonical_confusables)
                raise e
        os.makedirs(path.parent, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(r, f, ensure_ascii=False, indent=2, sort_keys=True)

    def check(self):
        for key, confusable in self.rules.items():
            assert confusable.canonical_confusables
            assert key not in confusable.noncanonical_confusables
            assert key not in confusable.canonical_confusables[1:]





    def set_custom_nonconfusables(self):
        for grapheme in LIST_OF_NONCONFUSABLES:
            self.rules[grapheme].canonical_confusables.clear()
            self.rules[grapheme].noncanonical_confusables.clear()
            self.rules[grapheme].set_canonical(grapheme)


if __name__ == '__main__':
    print('Downloading confusables...')
    with download_confusables():
        print('Processing confusables...')
        confusables = Confusables()
        confusables.generate()

        confusables.check()

        # set ens_normalized as canonical
        for character, confusable_obj in confusables.rules.items():
            if is_normalized(character):
                # check canonical if normalized
                try:
                    if is_normalized(confusable_obj.canonical_confusables[0]):
                        continue
                    normalized_canonical_try = ens_normalize.ens_normalize(confusable_obj.canonical_confusables[0])
                    confusable_obj.set_canonical(normalized_canonical_try)
                except DisallowedSequence:
                    canonical_set=False
                    for confusable in confusable_obj.canonical_confusables[1:] + [character]:
                        try:
                            if is_normalized(confusable):
                                confusable_obj.set_canonical(confusable)
                            else:
                                normalized_confusable_try = ens_normalize.ens_normalize(confusable)
                                confusable_obj.set_canonical(normalized_confusable_try)
                            canonical_set=True
                            break
                        except DisallowedSequence:
                            continue
                    if not canonical_set:
                        confusable_obj.set_canonical(character)

        

        # TODO add ens_normalized confusables to confusables
        
        #TODO need better solution 
        for character, confusable_obj in confusables.rules.items():
            if is_normalized(character):
                canonical = confusable_obj.canonical_confusables[0]
                if character == canonical: continue
                script_confusable = not ens_normalize.is_ens_normalized(character + canonical)
                if script_confusable:
                    confusable_obj.set_canonical(character)
                    print(character, canonical, ens_normalize.is_ens_normalized(character), script_of(character), script_of(canonical), [(x, script_of(x)) for x in confusable_obj.all_confusables() if is_normalized(x)])

        print(f'Saving confusables... {CONFUSABLES_JSON_PATH}')
        confusables.save(CONFUSABLES_JSON_PATH)
        print('Done')
