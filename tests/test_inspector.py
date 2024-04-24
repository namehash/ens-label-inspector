import pytest
import os

from label_inspector.config import initialize_inspector_config
from label_inspector.components.features import Features
from label_inspector.inspector import Inspector, remove_accents, strip_accents
from helpers import TESTS_DATA_PATH


@pytest.fixture(scope="module")
def analyse_label():
    with initialize_inspector_config("prod_config") as config:
        inspector = Inspector(config)
        return lambda label, *args, **kwargs: inspector.analyse_label(label, *args, **kwargs).model_dump()


def test_inspector_character_name():
    with initialize_inspector_config("prod_config") as config:
        f = Features(config)
        assert f.unicodedata_name('a') == 'LATIN SMALL LETTER A'
        assert f.unicodedata_name('🟢') == 'LARGE GREEN CIRCLE'
        assert f.script_name('\ufffe') == 'Unknown'
        assert f.unicodeblock('🧽') == 'Supplemental Symbols and Pictographs'


def test_remove_accents():
    chars = {'ą': 'a', 'ś': 's', 'ó': 'o', 'ź': 'z', 'ώ': 'ω', 'ῴ': 'ω'}
    # {'ł':'l','ό':'o'} dont work
    for char, canonical in chars.items():
        assert remove_accents(char) == canonical
        assert strip_accents(char) == canonical


@pytest.mark.execution_timeout(10)
def test_inspector_long(analyse_label):
    analyse_label('miinibaashkiminasiganibiitoosijiganibadagwiingweshiganibakwezhigan')


def test_inspector_cured_label(analyse_label):
    input = 'a a'
    r = analyse_label(input, omit_cure=False)
    assert r['cured_label'] == 'aa'
    r = analyse_label(input, omit_cure=True)
    assert r['cured_label'] is None

@pytest.mark.execution_timeout(2)
def test_inspector_cured_label_long(analyse_label):
    input = '⎛⎝⎞⎠' * 1000
    r = analyse_label(input, omit_cure=True)
    assert r['cured_label'] is None

@pytest.mark.execution_timeout(10)
def test_inspector_long2(analyse_label):
    analyse_label('a' * 40000)


@pytest.mark.execution_timeout(10)
def test_inspector_limit_confusables(analyse_label):

    result = analyse_label('ąlaptop', truncate_confusables=1)
    assert len(result['graphemes'][0]['confusables_other']) == 1

    result = analyse_label('ąlaptop', truncate_confusables=None)
    assert len(result['graphemes'][0]['confusables_other']) > 1


@pytest.mark.execution_timeout(10)
def test_inspector_disable_chars_output(analyse_label):
    result = analyse_label('ąlaptop', truncate_graphemes=0)
    all_chars = [c for grapheme in result['graphemes'] for c in grapheme['chars']]
    assert len(all_chars) == 0
    assert len(result['any_types']) >= 1

    result = analyse_label('ąlaptop', truncate_graphemes=None)
    all_chars = [c for grapheme in result['graphemes'] for c in grapheme['chars']]
    assert len(all_chars) == 7

    result = analyse_label('ąlaptop', truncate_graphemes=3)
    all_chars = [c for grapheme in result['graphemes'] for c in grapheme['chars']]
    assert len(all_chars) == 3


@pytest.mark.skip('disabled option disable_char_analysis')
@pytest.mark.execution_timeout(10)
def test_inspector_disable_char_analysis(analyse_label):
    result = analyse_label('ąlaptop', disable_char_analysis=True)
    assert result['graphemes'] is None
    assert 'any_types' not in result

    result = analyse_label('ąlaptop', disable_char_analysis=False)
    all_chars = [c for grapheme in result['graphemes'] for c in grapheme['chars']]
    assert len(all_chars) == 7


def test_inspector_numerics():
    with initialize_inspector_config("prod_config") as config:
        features = Features(config)

        with open(os.path.join(TESTS_DATA_PATH, 'unicode_numerics.txt'), 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if len(line) == 0 or line.startswith('#'):
                    continue

                char = chr(int(line, 16))
                assert features.is_number(char), f'{line} not detected as number'


# these tests are in test_myunicode, so skipping them here is not a big deal
@pytest.mark.skip('labels are unnormalized')
@pytest.mark.parametrize(
    'label,script',
    [
        ('その目、誰の目？', None),  # mixed
        ('そのめ、だれのめ？', 'Hiragana'),  # simple
        ('そのめ、た\u3099れのめ？', 'Hiragana'),  # X, Inherited (ta + dakuten)
        ('そのめ、だれのめ...？', 'Hiragana'),  # X, Common (...)
        ('そのめ、た\u3099れのめ...？', 'Hiragana'),  # X, Common, Inherited
        ('abc🩷.eth', None),  # Unknown
    ]
)
def test_inspector_all_script(analyse_label, label, script):
    result = analyse_label(label)
    assert result['all_script'] == script


def test_inspector_aggregation_works_before_truncation(analyse_label):
    label = 'abc123'
    result = analyse_label(label, truncate_graphemes=3)
    assert [c['value'] for g in result['graphemes'] for c in g['chars']] == ['a', 'b', 'c']
    assert result['all_type'] == None
    assert sorted(result['any_types']) == sorted(['simple_letter', 'simple_number'])
    assert result['all_script'] == 'Latin'
    assert sorted(result['any_scripts']) == sorted(['Latin', 'Common'])


# probably not possible to test since all unknown chars are disallowed
@pytest.mark.skip('label is unnormalized')
def test_inspector_label_of_unknown_char(analyse_label):
    label = '🩷'
    result = analyse_label(label)
    assert result['graphemes'][0]['chars'][0]['label'] == 'Unknown character in Unknown script'


def test_inspector_grapheme_script(analyse_label):
    label = '١-\u0610'
    result = analyse_label(label)
    assert result['graphemes'][0]['script'] == 'Arabic'
    assert result['graphemes'][1]['script'] == 'Arabic'
    # TODO grapheme with multiple scripts?


def test_inspector_grapheme_class(analyse_label):
    label = 'ع-\u0610👩🏻‍🤝‍👩🏼'
    result = analyse_label(label)
    assert result['graphemes'][0]['type'] == 'other_letter'
    assert result['graphemes'][1]['type'] == 'special'
    assert result['graphemes'][2]['type'] == 'emoji'


def test_inspector_grapheme_label(analyse_label):
    label = '١-\u0610👩🏻‍🤝‍👩🏼'
    result = analyse_label(label)
    assert result['graphemes'][0]['name'] == 'ARABIC-INDIC DIGIT ONE'
    assert result['graphemes'][1]['name'] == 'Combined Character'
    assert result['graphemes'][2]['name'] == 'WOMEN HOLDING HANDS: LIGHT SKIN TONE, MEDIUM-LIGHT SKIN TONE'


@pytest.mark.parametrize(
    'input_label, normalized_input, expected_canonical_label, expected_beautiful_canonical_label',
    [
        ('pure-words', True, 'pure-words', 'pure-words'),  # no confusables
        ('🄓ire', False, None, None),  # not normalized input
        ('yés', True, 'yes', 'yes'),  # "e" has the canonical version
        ('yéś', True, 'yes', 'yes'),  # both "Ŷ" and "Ś" have canonical version
        ('˪pure-words', True, None, None),  # "˪" is confusable, but has no canonical version
        ('-ś', True, '-s', '-s'),  # canonical_label length is less than 3
        # TODO find new example
        pytest.param('𐌂𐌂𐌂', True, 'ccc', 'ccc', marks=pytest.mark.xfail),  # canonical_label gets normalized,
        ('xx\u200d', True, None, None),  # canonical_label cannot be normalized,
        ('🧟‍♂' * 3, True, '🧟' * 3, '🧟\ufe0f' * 3),  # canonical version is a simple zombie
    ]
)
def test_canonical_label(analyse_label,
                         input_label: str,
                         normalized_input: bool,
                         expected_canonical_label: str,
                         expected_beautiful_canonical_label: str):
    result = analyse_label(input_label)
    if normalized_input:
        assert result['normalized_canonical_label'] == expected_canonical_label
        assert result['beautiful_canonical_label'] == expected_beautiful_canonical_label
    else:
        assert result['normalized_canonical_label'] is None
        assert result['beautiful_canonical_label'] is None


@pytest.mark.parametrize('label,script', [
    # case 1
    # most likely all unknown characters are disallowed
    # ('a🩷c', None),
    # case 2
    # not possible because of isolated combining marks
    # ('-\u0328', 'Common'),
    # ('--\u0328', 'Common'),
    # case 3
    ('abcd', 'Latin'),
    ('ab-cd', 'Latin'),
    ('١-\u0610١١', 'Arabic'),
    ('١-\u0610-١١', 'Arabic'),
    ('-', 'Common'),
    # can we have only inherited script?
    # ('\u0328', 'Inherited'),
    # case 4
    ('のtak', None),
    ('の.tak', None),
    # ('のtakb\u0327', None), # unnormalized
])
def test_inspector_all_script(analyse_label, label, script):
    result = analyse_label(label)
    assert result['all_script'] == script


def test_inspector_suggested_replacement(analyse_label):
    result = analyse_label('bs\u0327a')
    assert result['suggested_replacement'][0]['value'] == 'ş'

    result = analyse_label('a\u200db')
    assert len(result['suggested_replacement']) == 0


@pytest.mark.parametrize('label,all_type', [
    ('-', 'hyphen'),
    ('_', 'underscore'),
    ('$', 'dollarsign'),
])
def test_inspector_named_character_types(analyse_label, label, all_type):
    resp = analyse_label(label)
    assert resp['all_type'] == all_type


def test_inspector_multi_char_grapheme_type(analyse_label):
    resp = analyse_label('ᄅᄅᄅ')
    assert resp['graphemes'][0]['type'] == 'other_letter'


def test_problem1_beautiful_flag(analyse_label):
    label = '🇬🇧'
    resp = analyse_label(label)
    assert resp['beautiful_label'] == label


@pytest.mark.parametrize('label', [
    '🧑‍🤝‍🧑🏿', '🤼🏾‍♂', '👩‍❤‍👩🏿', '🧙‍♂🏼🏼🏼🏼'
])
def test_problem2_unnormalized(analyse_label, label):
    resp = analyse_label(label)
    assert resp['status'] == 'unnormalized'


@pytest.mark.parametrize('label,g_link,c_links', [
    ('a', 'https://unicodeplus.com/U+0061', ['https://unicodeplus.com/U+0061']),
    ('-\u0610', 'https://unicode.link/inspect/utf8:2d.d8.90', ['https://unicodeplus.com/U+002D', 'https://unicodeplus.com/U+0610']),
    ('🧌', 'http://📙.la/🧌', ['http://📙.la/🧌']),
    ('👩🏿‍🦲', 'http://📙.la/👩🏿‍🦲', ["http://📙.la/👩", "http://📙.la/🏿", "http://📙.la/‍", "http://📙.la/🦲"]),
])
def test_inspector_char_links(analyse_label, label, g_link, c_links):
    resp = analyse_label(label)
    assert resp['graphemes'][0]['link'] == g_link
    assert [c['link'] for c in resp['graphemes'][0]['chars']] == c_links


def test_inspector_punycode(analyse_label):
    resp = analyse_label('xn--😵💫😵💫😵💫')
    assert resp['dns_hostname_support'] == False
    assert resp['punycode_compatibility'] == 'COMPATIBLE'
    assert resp['punycode_encoding'] == 'xn--xn---8v63caa362abab'

    resp = analyse_label('x' * 64)
    assert resp['dns_hostname_support'] == False
    assert resp['punycode_compatibility'] == 'LABEL_TOO_LONG'
    assert resp['punycode_encoding'] == None


def test_inspector_font_support(analyse_label):
    resp = analyse_label('a✊🏾')
    assert resp['font_support_all_os'] == True
    assert resp['graphemes'][0]['font_support_all_os'] == True
    assert resp['graphemes'][1]['font_support_all_os'] == True

    resp = analyse_label('✊🏾' + chr(5922) + '👊🏿')
    assert resp['font_support_all_os'] == False
    assert resp['graphemes'][0]['font_support_all_os'] == True
    assert resp['graphemes'][1]['font_support_all_os'] == False
    assert resp['graphemes'][2]['font_support_all_os'] == False


def test_simple_confusables(analyse_label):
    resp = analyse_label('Ĳ', simple_confusables=False)
    assert resp['graphemes'][0]['confusables_canonical']['value'] == 'lJ'
    assert 'IJ' in [c['value'] for c in resp['graphemes'][0]['confusables_other']]

    resp = analyse_label('Ĳ', simple_confusables=True)
    assert resp['graphemes'][0]['confusables_canonical'] is None
    assert 'IJ' not in [c['value'] for c in resp['graphemes'][0]['confusables_other']]


def test_canonical_label2(analyse_label):
    resp = analyse_label('ąęćżabcń')
    assert resp['canonical_label'] == 'aeczabcn'

    resp = analyse_label('Ĳ', simple_confusables=True)
    assert resp['canonical_label'] is None

    resp = analyse_label('n’diaye')
    assert resp['canonical_label'] == 'n’diaye'

    resp = analyse_label('n’diaye', simple_confusables=True)
    assert resp['canonical_label'] == 'n’diaye'

@pytest.mark.parametrize('grapheme,type,description', [
    ('a', 'simple_letter', 'A-Z letter'),
    ('0', 'simple_number', '0-9 number'),
    ('ą', 'other_letter', 'Latin letter'),
    ('Ⅷ', 'other_number', 'Latin number'),
    ('-', 'hyphen', 'Hyphen'),
    ('$', 'dollarsign', 'Dollar sign'),
    ('_', 'underscore', 'Underscore'),
    ('😵‍💫', 'emoji', 'Emoji'),
    ('\U0000200D', 'invisible', 'Invisible character'),
    ('\U0000200C', 'invisible', 'Invisible character'),
    ('\ufe0f', 'invisible', 'Invisible character'),
    ('\ufe0e', 'invisible', 'Invisible character'),
    ('!', 'special', 'Special character'),
    ('-\u0610', 'special', 'Special character'),
    ('\ufffe', 'special', 'Special character'),
    ('🧌', 'emoji', 'Emoji'),
    ('🧌️', 'emoji', 'Emoji'),
])
def test_inspector_grapheme_description(analyse_label, grapheme, type, description):
    result = analyse_label(grapheme)
    assert result['graphemes'][0]['description'] == description
    assert result['graphemes'][0]['type'] == type

def test_invisible_characters(analyse_label):
    invisible_characters = {
        '\U00000009': 'CHARACTER TABULATION',
        '\U00000020': 'SPACE',
        '\U000000A0': 'NO-BREAK SPACE',
        '\U000000AD': 'SOFT HYPHEN',
        '\U0000034F': 'COMBINING GRAPHEME JOINER',
        '\U0000061C': 'ARABIC LETTER MARK',
        '\U0000115F': 'HANGUL CHOSEONG FILLER',
        '\U00001160': 'HANGUL JUNGSEONG FILLER',
        '\U000017B4': 'KHMER VOWEL INHERENT AQ',
        '\U000017B5': 'KHMER VOWEL INHERENT AA',
        '\U0000180E': 'MONGOLIAN VOWEL SEPARATOR',
        '\U00002000': 'EN QUAD',
        '\U00002001': 'EM QUAD',
        '\U00002002': 'EN SPACE',
        '\U00002003': 'EM SPACE',
        '\U00002004': 'THREE-PER-EM SPACE',
        '\U00002005': 'FOUR-PER-EM SPACE',
        '\U00002006': 'SIX-PER-EM SPACE',
        '\U00002007': 'FIGURE SPACE',
        '\U00002008': 'PUNCTUATION SPACE',
        '\U00002009': 'THIN SPACE',
        '\U0000200A': 'HAIR SPACE',
        '\U0000200B': 'ZERO WIDTH SPACE',
        '\U0000200C': 'ZERO WIDTH NON-JOINER',
        '\U0000200D': 'ZERO WIDTH JOINER',
        '\U0000200E': 'LEFT-TO-RIGHT MARK',
        '\U0000200F': 'RIGHT-TO-LEFT MARK',
        '\U0000202F': 'NARROW NO-BREAK SPACE',
        '\U0000205F': 'MEDIUM MATHEMATICAL SPACE',
        '\U00002060': 'WORD JOINER',
        '\U00002061': 'FUNCTION APPLICATION',
        '\U00002062': 'INVISIBLE TIMES',
        '\U00002063': 'INVISIBLE SEPARATOR',
        '\U00002064': 'INVISIBLE PLUS',
        '\U0000206A': 'INHIBIT SYMMETRIC SWAPPING',
        '\U0000206B': 'ACTIVATE SYMMETRIC SWAPPING',
        '\U0000206C': 'INHIBIT ARABIC FORM SHAPING',
        '\U0000206D': 'ACTIVATE ARABIC FORM SHAPING',
        '\U0000206E': 'NATIONAL DIGIT SHAPES',
        '\U0000206F': 'NOMINAL DIGIT SHAPES',
        '\U00003000': 'IDEOGRAPHIC SPACE',
        '\U00002800': 'BRAILLE PATTERN BLANK',
        '\U00003164': 'HANGUL FILLER',
        '\U0000FE00': '',
        '\U0000FE01': '',
        '\U0000FE02': '',
        '\U0000FE03': '',
        '\U0000FE04': '',
        '\U0000FE05': '',
        '\U0000FE06': '',
        '\U0000FE07': '',
        '\U0000FE08': '',
        '\U0000FE09': '',
        '\U0000FE0A': '',
        '\U0000FE0B': '',
        '\U0000FE0C': '',
        '\U0000FE0D': '',
        '\U0000FE0E': '',
        '\U0000FE0F': '',
        '\U0000FEFF': 'ZERO WIDTH NO-BREAK SPACE',
        '\U0000FFA0': 'HALFWIDTH HANGUL FILLER',
        '\U0001D159': 'MUSICAL SYMBOL NULL NOTEHEAD',
        '\U0001D173': 'MUSICAL SYMBOL BEGIN BEAM',
        '\U0001D174': 'MUSICAL SYMBOL END BEAM',
        '\U0001D175': 'MUSICAL SYMBOL BEGIN TIE',
        '\U0001D176': 'MUSICAL SYMBOL END TIE',
        '\U0001D177': 'MUSICAL SYMBOL BEGIN SLUR',
        '\U0001D178': 'MUSICAL SYMBOL END SLUR',
        '\U0001D179': 'MUSICAL SYMBOL BEGIN PHRASE',
        '\U0001D17A': 'MUSICAL SYMBOL END PHRASE',
    }
    
    for invisible, name in invisible_characters.items():
        label = f'a{invisible}b'
        result = analyse_label(label)
        print(result['grapheme_length'], label, [label], name, result)
        assert result['grapheme_length'] == 3

        label = f'{invisible}ab'
        result = analyse_label(label)
        print(result['grapheme_length'], label, [label], name, result)
        assert result['grapheme_length'] == 3


@pytest.mark.parametrize(
    'emoji,version',
    [
        ('🫏', 'E15.0'),
        ('🫷🏼', 'E15.0'),
        ('🧑‍🧑‍🧒', 'E15.1'),
    ]
)
def test_emoji_version(analyse_label, emoji, version):
    result = analyse_label(emoji)
    assert result['graphemes'][0]['emoji_version'] == version
