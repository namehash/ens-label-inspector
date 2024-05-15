import pytest
import unicodedata
import itertools
import regex as re
from typing import Optional
import os

from label_inspector.common import myunicode
from helpers import TESTS_DATA_PATH, load_new_unicode_chars


@pytest.mark.parametrize(
    'chr,expected',
    [
        ('a', 'LATIN SMALL LETTER A'),
        ('ア', 'KATAKANA LETTER A'),
        ('ἀ', 'GREEK SMALL LETTER ALPHA WITH PSILI'),
        ('יִ', 'HEBREW LETTER YOD WITH HIRIQ'),
        ('\u3099', 'COMBINING KATAKANA-HIRAGANA VOICED SOUND MARK'),
        ('\U0001FAB7', 'LOTUS'),  # Unicode 14
        ('\U0001B155', 'KATAKANA LETTER SMALL KO'),  # Unicode 15
        ('\U0002000B', 'CJK UNIFIED IDEOGRAPH-2000B'),  # Unicode < 14 CJK
        ('\U0002b736', 'CJK UNIFIED IDEOGRAPH-2B736'),  # Unicode 14 CJK
        ('\u0089', '<control>'),
    ]
)
def test_name(chr, expected):
    assert myunicode.name(chr) == expected
    assert myunicode.name(chr, 'default') == expected


@pytest.mark.parametrize(
    'chr,expected',
    [
        ('a', 'LATIN SMALL LETTER A'),
        ('\ufffe', 'default'),
    ]
)
def test_name_default(chr, expected):
    assert myunicode.name(chr, default='default') == expected


@pytest.mark.parametrize('chr', ['\ufffe'])
def test_name_throws_on_missing(chr):
    with pytest.raises(ValueError, match='no such name'):
        myunicode.name(chr)


@pytest.mark.parametrize('chr', ['abc', 'aア', ''])
def test_name_throws_on_str(chr):
    with pytest.raises(TypeError, match=r'name\(\) argument 1 must be a unicode character, not str'):
        myunicode.name(chr)
    with pytest.raises(TypeError, match=r'name\(\) argument 1 must be a unicode character, not str'):
        myunicode.name(chr, 'default')


@pytest.mark.parametrize(
    'chr,expected',
    [
        ('a', 'Ll'),
        ('ア', 'Lo'),
        ('\u0600', 'Cf'),
        ('\ufffe', 'Cn'),
        ('\U0001FAB7', 'So'),  # Unicode 14
        ('\U0001B155', 'Lo'),  # Unicode 15
        ('\U0002000B', 'Lo'),  # Unicode < 14 CJK
        ('\U0002b736', 'Lo'),  # Unicode 14 CJK
        ('\u0089', 'Cc'),  # control
    ]
)
def test_category(chr, expected):
    assert myunicode.category(chr) == expected


@pytest.mark.parametrize('chr', ['abc', 'aア', ''])
def test_category_throws_on_str(chr):
    with pytest.raises(TypeError, match=r'category\(\) argument must be a unicode character, not str'):
        myunicode.category(chr)


@pytest.mark.parametrize(
    'chr,expected',
    [
        ('a', 0),
        ('🩶', 0),
        ('\u3099', 8),
        ('\U0001FAB7', 0),  # Unicode 14
        ('\U0001B155', 0),  # Unicode 15
        ('\U0002000B', 0),  # Unicode < 14 CJK
        ('\U0002b736', 0),  # Unicode 14 CJK
        ('\u0089', 0),  # control
    ]
)
def test_combining(chr, expected):
    assert myunicode.combining(chr) == expected


@pytest.mark.parametrize('chr', ['abc', 'aア', ''])
def test_combining_throws_on_str(chr):
    with pytest.raises(TypeError, match=r'combining\(\) argument must be a unicode character, not str'):
        myunicode.combining(chr)


@pytest.mark.parametrize(
    'chr,expected',
    [
        ('a', 'Basic Latin'),
        ('ア', 'Katakana'),
        ('🩶', 'Symbols and Pictographs Extended-A'),
        ('\U0001FAB7', 'Symbols and Pictographs Extended-A'),  # Unicode 14
        ('\U0001B155', 'Small Kana Extension'),  # Unicode 15
        ('\U0002000B', 'CJK Unified Ideographs Extension B'),  # Unicode < 14 CJK
        ('\U0002b736', 'CJK Unified Ideographs Extension C'),  # Unicode 14 CJK
    ]
)
def test_block_of(chr, expected):
    assert myunicode.block_of(chr) == expected


@pytest.mark.parametrize('chr', ['abc', 'aア', ''])
def test_block_of_throws_on_str(chr):
    with pytest.raises(Exception, match=r'block_of\(\) argument must be a unicode character, not str'):
        myunicode.block_of(chr)


@pytest.mark.parametrize(
    'chr,expected',
    [
        ('יִ', 'Hebrew'),
        ('a', 'Latin'),
        ('abc', 'Latin'),
        ('ア', 'Katakana'),
        ('アア', 'Katakana'),
        ('aア', None),  # mixed scripts
        ('Mały kotek', 'Latin'),
        ('その目、誰の目？', None),  # mixed scripts
        ('そのめ、だれのめ？', 'Hiragana'),
        ('そのめ,だれのめ...?', 'Hiragana'),
        ('لوحة المفاتيح العربية', 'Arabic'),
        ('Those eyes, だれのめ?', None),  # mixed scripts
        (' ,. co jak na początku jest common?', 'Latin'),
        (' ,.?', 'Common'),
        ('', None),
        ('\U0001FAB7', 'Common'),  # Unicode 14
        ('\U0001B155', 'Katakana'),  # Unicode 15
        ('\U0002000B', 'Han'),  # Unicode < 14 CJK
        ('\U0002b736', 'Han'),  # Unicode 14 CJK
        ('\ufffe', 'Unknown'),  # invalid unicode character
        ('abc\ufffe.', None),  # Latin + Unknown (invalid) + Common
        ('abc\ufffe', None),  # Latin + Unknown (invalid)
        ('\ufffe.', 'Unknown'),  # Unknown (invalid) + Common
        ('\u0485', 'Inherited'),  # COMBINING CYRILLIC DASIA PNEUMATA
        ('\u0485\ufffe', 'Unknown'),  # Inherited + Unknown (invalid)
        ('\ufffe\u0485', 'Unknown'),  # Unknown (invalid) + Inherited
        ('\u0485.', 'Common'),  # Inherited + Common
        ('.\u0485', 'Common'),  # Common + Inherited
        ('そのめ、た\u3099れのめ？', 'Hiragana'),  # X, Inherited (ta + dakuten)
        ('そのめ、だれのめ...？', 'Hiragana'),  # X, Common (...)
        ('そのめ、た\u3099れのめ...？', 'Hiragana'),  # X, Common, Inherited
    ]
)
def test_script_of(chr, expected):
    assert myunicode.script_of(chr) == expected


@pytest.mark.parametrize(
    'chr,expected',
    [
        ('🫶', True),
        ('😫', True),
        ('🤔', True),
        ('a', False),
        ('1', False),
        ('#', False),
        ('*', False),
        ('ア', False),
        ('\U0000200D', False),  # ZWJ
        ('\U0000200C', False),  # ZWNJ
        ('\U0001FAB7', True),  # Unicode 14
        ('\U0001B155', False),  # Unicode 15
        ('\U0002000B', False),  # Unicode < 14 CJK
        ('\U0002b736', False),  # Unicode 14 CJK
    ]
)
def test_is_emoji_char(chr, expected):
    assert myunicode.is_emoji_char(chr) == expected


@pytest.mark.parametrize(
    'chr',
    [
        'abc',
        '🫶😫🤔',
        '🫶😫🤔a',
        '',
        '\U0000200D\U0000200D',
        '🏳️‍🌈',  # ZWJ sequence
    ]
)
def test_is_emoji_throws_on_str(chr):
    with pytest.raises(TypeError):
        myunicode.is_emoji_char(chr)


@pytest.mark.parametrize(
    'text, expected',
    [
        ('🇵🇱', True),
        ('🇺🇦', True),
        ('🇵🇱🇺🇦', False),
        ('🗂️', False),  # has FE0F at the end
        ('🗂', True),
        ('♠️', False),  # has FE0F at the end
        ('♠', True),
        ('🙃', True),
        ('🦹🏾', True),
        ('🦹', True),
    ]
)
def test_is_emoji_sequence(text: str, expected: bool):
    assert myunicode.is_emoji_sequence(text) == expected


@pytest.mark.parametrize(
    'text,expected',
    [
        ('', False),
        ('a', False),
        ('\u2705', False),  # single emoji
        ('🇪🇹', False),  # RGI
        ('\U0001F469\U0001F3FB\U0000200D\U0001F91D\U0000200D\U0001F469\U0001F3FC', True),
        ('\U0001F469\U0001F3FB\U0000200D\U0001F91D\U0000200D\U0000200D\U0001F469\U0001F3FC', False),  # 2 ZWJs
    ]
)
def test_is_emoji_zwj_sequence(text, expected):
    assert myunicode.is_emoji_zwj_sequence(text) == expected


@pytest.mark.parametrize(
    'text,expected',
    [
        ('*️⃣', False),
        ('*⃣', True),
        ('*', False),
        ('*\ufe0f', False),
        ('🇪🇹', True),
        ('\u2705', True),  # single emoji
        ('🇵🇱🇺🇦', False),
    ]
)
def test_is_emoji(text: str, expected: bool):
    assert myunicode.is_emoji(text) == expected


@pytest.mark.parametrize(
    'text,name',
    [
        ('', None),
        ('a', None),
        ('\u2705', None),  # single emoji
        ('\U0001F469\U0001F3FB\U0000200D\U0001F91D\U0000200D\U0001F469\U0001F3FC',
         'WOMEN HOLDING HANDS: LIGHT SKIN TONE, MEDIUM-LIGHT SKIN TONE'),
    ]
)
def test_emoji_zwj_sequence_name(text, name):
    assert myunicode.emoji_zwj_sequence_name(text) == name


@pytest.mark.parametrize(
    'char, is_emoji',
    [
        ('*️⃣', False),
        ('*⃣', True),
        ('*', False),
        ('*\ufe0f', False),
        ('🇪🇹', True),
        ('\u2705', True),  # single emoji
        ('🇵🇱🇺🇦', False),
    ]
)
def test_emoji_iterator(char: str, is_emoji: bool):
    emojis = set(myunicode.emoji_iterator())
    assert (char in emojis) == is_emoji


def test_emoji_iterator_all_emojis():
    for emoji in myunicode.emoji_iterator():
        assert myunicode.is_emoji(emoji)


def test_emoji_iterator_all_characters():
    emojis = set(myunicode.emoji_iterator())
    for i in itertools.count():
        try:
            char = chr(i)
        except ValueError:  # catching getting out of the range of possible characters
            break

        if myunicode.is_emoji(char):
            assert char in emojis


@pytest.mark.parametrize(
    'text,name',
    [
        ('', None),
        ('a', None),
        ('\u2705', 'CHECK MARK BUTTON'),
        ('\U0001F469\U0001F3FB\U0000200D\U0001F91D\U0000200D\U0001F469\U0001F3FC',
         'WOMEN HOLDING HANDS: LIGHT SKIN TONE, MEDIUM-LIGHT SKIN TONE'),
        ('⛏', 'PICK'),
        ('⛵', 'SAILBOAT'),
        ('📷', 'CAMERA'),
        ('🌭', 'HOT DOG'),
        ('💏🏽', 'KISS: MEDIUM SKIN TONE'),
        ('👨🏾‍⚖', 'MAN JUDGE: MEDIUM-DARK SKIN TONE')
    ]
)
def test_emoji_name(text: str, name: Optional[str]):
    assert myunicode.emoji_name(text) == name


@pytest.mark.parametrize(
    'chr,expected',
    [
        ('a', False),
        ('1', True),
        ('🫶', False),
        ('十', False),
        ('１', True),
        ('\U0001FAB7', False),  # Unicode 14
        ('\U0001B155', False),  # Unicode 15
        ('\U0002000B', False),  # Unicode < 14 CJK
        ('\U0002b736', False),  # Unicode 14 CJK
    ])
def test_is_numeric(chr, expected):
    assert myunicode.is_numeric(chr) == expected


def test_is_numeric_throws_on_str():
    with pytest.raises(TypeError):
        myunicode.is_numeric('１０')


@pytest.mark.parametrize(
    'version',
    [
        '14',
        '15',
    ],
)
def test_new_unicode_version(version):
    for char, name in load_new_unicode_chars(version):
        assert myunicode.name(char) == name
        assert myunicode.combining(char) is not None
        assert myunicode.category(char) is not None
        assert myunicode.is_emoji_char(char) is not None
        assert myunicode.is_numeric(char) is not None
        assert myunicode.script_of(char) is not None
        assert myunicode.block_of(char) is not None


@pytest.mark.parametrize(
    'char',
    [
        '\u9FFE',  # Unicode 14
        '\U0002B739',  # Unicode 15
        '\U0002000B',
    ],
)
def test_unicode_cjk(char):
    assert myunicode.name(char) is not None
    assert myunicode.combining(char) is not None
    assert myunicode.category(char) is not None
    assert myunicode.is_emoji_char(char) is not None
    assert myunicode.is_numeric(char) is not None
    assert myunicode.script_of(char) is not None
    assert myunicode.block_of(char) is not None


def test_all_characters():
    SKIP_CHARACETRS = [
        '\u1734',  # HANUNOO SIGN PAMUDPOD
        # category was changed in Unicode 14 from Mn to Mc
    ]

    # from 0 to last block
    for char in map(chr, range(0x10FFFF + 1)):
        if char in SKIP_CHARACETRS:
            continue

        # check if character is in unicodedata database
        try:
            # will throw if character is not found
            unicodedata.name(char)
        except ValueError:
            # character is not known to unicodedata
            # so we cannot check it against myunicode
            continue

        assert myunicode.name(char) == unicodedata.name(char), hex(ord(char))[2:]
        assert myunicode.combining(char) == unicodedata.combining(char), hex(ord(char))[2:]
        assert myunicode.category(char) == unicodedata.category(char), hex(ord(char))[2:]


@pytest.mark.parametrize(
    'text,graphemes',
    [
        ('', []),
        ('a', ['a']),
        ('abc', ['a', 'b', 'c']),
        ['a\u200db', ['a', '\u200d', 'b']],
        ('🇪🇹', ['🇪🇹']),
        ('\U0001F469\U0001F3FF\U0000200D\U0001F9B2', ['\U0001F469\U0001F3FF\U0000200D\U0001F9B2']),
        ('\U0001F469\U0001F3FF\U0000200D\U0000200D\U0001F9B2',
         ['\U0001F469\U0001F3FF', '\U0000200D', '\U0000200D', '\U0001F9B2']),
        #feofs
        ('6️9', ['6','\ufe0f','9']),
        ('️9', ['\ufe0f','9']),
        ('6️', ['6','\ufe0f']),
        ('🦄️', ['🦄️']),
        ('🦄️️', ['🦄️', '\ufe0f']),
        ('6‍9', ['6','‍','9']),
        ('6‌9', ['6','‌','9']),
        ('6‌‍️9', ['6','‌','‍','\ufe0f','9']),
        ('a	  ­͏b', ['a', '\t', ' ', '\xa0', '\xad', '͏', 'b']),
        ('a؜b', ['a', '\u061c', 'b']),
        ('a​b', ['a', '\u200b', 'b']),
        ('a\ufeffb', ['a', '\ufeff', 'b']),
        ('a\ufe0eb', ['a', '\ufe0e', 'b']),
    ]
)
def test_grapheme_iter(text, graphemes):
    assert myunicode.grapheme.split(text) == graphemes


@pytest.mark.parametrize(
    'grapheme,name',
    [
        ('', None),
        ('a', None),
        ('a\u200d', None),
        ('♍', 'VIRGO'),
        ('🇦🇶', 'FLAG: ANTARCTICA'),
        ('\U0001F469\U0001F3FF\U0000200D\U0001F9B2', 'WOMAN: DARK SKIN TONE, BALD'),
        ('\U0001F469\U0001F3FF\U0000200D\U0001F9B2\ufe0f', 'WOMAN: DARK SKIN TONE, BALD WITH VARIATIONAL SELECTOR(S)'),
        ('\U0001F600', 'GRINNING FACE'),
        ('\U0001F600\ufe0f', 'GRINNING FACE WITH VARIATIONAL SELECTOR(S)'),
        ('👁️‍🗨️', 'EYE IN SPEECH BUBBLE WITH VARIATIONAL SELECTOR(S)'),
        ('👁️‍🗨', 'EYE IN SPEECH BUBBLE WITH VARIATIONAL SELECTOR(S)'),
    ]
)
def test_grapheme_name(grapheme, name):
    assert myunicode.grapheme.name(grapheme) == name


@pytest.mark.parametrize('text,graphemes', [
    ('ᄅ', ['ᄅ']),
    ('ᄅᄅ', ['ᄅ', 'ᄅ']),
    ('ᄅ\u0328', ['ᄅ\u0328']),
    ('ᄅᄅ\u0328', ['ᄅ', 'ᄅ\u0328']),
])
def test_grapheme_iter_hangul(text, graphemes):
    assert myunicode.grapheme.split(text) == graphemes


def test_grapheme_iter_no_hangul():
    with open(os.path.join(TESTS_DATA_PATH, 'primary.csv'), 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for line in lines:
        if any(block.find('Hangul') != -1 and block.find('Jamo') != -1 for c in line for block in [myunicode.block_of(c) or '']):
            continue
        if '\ufe0f' in line or '\u200d' in line or '\u200c' in line:
            continue

        assert myunicode.grapheme.split(line) == re.findall(r'\X', line)


@pytest.mark.parametrize(
    'c,version',
    [
        ('🪿', '15.0'),
        ('🩼', '14.0'),
    ]
)
def test_unicode_version(c, version):
    assert myunicode.unicode_version(c) == version


@pytest.mark.parametrize(
    'emoji,version',
    [
        ('🫏\ufe0f', 'E15.0'),
        ('🫷🏼\ufe0f', 'E15.0'),
        ('🧑‍🧑‍🧒\ufe0f', 'E15.1'),
    ]
)
def test_emoji_version(emoji, version):
    assert myunicode.emoji_version(emoji) == version


@pytest.mark.parametrize(
    'g,version',
    [
        ('🪿', '15.0'),
        ('🩼', '14.0'),
        ('🫏\ufe0f', '15.0'),
        ('🫷🏼\ufe0f', '15.0'),
        ('🧑‍🧑‍🧒\ufe0f', '15.1'),
    ]
)
def test_unicode_min_version(g, version):
    assert myunicode.unicode_min_version(g) == version
