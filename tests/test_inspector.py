import pytest
import os

from label_inspector.config import initialize_inspector_config
from label_inspector.components.features import Features
from label_inspector.inspector import Inspector, remove_accents, strip_accents
from helpers import TESTS_DATA_PATH


@pytest.fixture(scope="module")
def prod_inspector():
    with initialize_inspector_config("prod_config") as config:
        inspector = Inspector(config)
        return inspector


@pytest.fixture(scope="module")
def inspector_test_config():
    with initialize_inspector_config("test_config") as config:
        inspector = Inspector(config)
        return inspector


def test_inspector(prod_inspector):
    inspector = prod_inspector
    result = inspector.analyse_label('asd')


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
def test_inspector_long(prod_inspector):
    inspector = prod_inspector
    result = inspector.analyse_label('miinibaashkiminasiganibiitoosijiganibadagwiingweshiganibakwezhigan')


@pytest.mark.execution_timeout(10)
def test_inspector_long2(prod_inspector):
    inspector = prod_inspector
    result = inspector.analyse_label('a' * 40000)


@pytest.mark.execution_timeout(10)
def test_inspector_limit_confusables(prod_inspector):
    inspector = prod_inspector

    result = inspector.analyse_label('ąlaptop', truncate_confusables=1)
    assert len(result['graphemes'][0]['confusables_other']) == 1

    result = inspector.analyse_label('ąlaptop', truncate_confusables=None)
    assert len(result['graphemes'][0]['confusables_other']) > 1


@pytest.mark.execution_timeout(10)
def test_inspector_disable_chars_output(prod_inspector):
    inspector = prod_inspector

    result = inspector.analyse_label('ąlaptop', truncate_graphemes=0)
    all_chars = [c for grapheme in result['graphemes'] for c in grapheme['chars']]
    assert len(all_chars) == 0
    assert len(result['any_types']) >= 1

    result = inspector.analyse_label('ąlaptop', truncate_graphemes=None)
    all_chars = [c for grapheme in result['graphemes'] for c in grapheme['chars']]
    assert len(all_chars) == 7

    result = inspector.analyse_label('ąlaptop', truncate_graphemes=3)
    all_chars = [c for grapheme in result['graphemes'] for c in grapheme['chars']]
    assert len(all_chars) == 3


@pytest.mark.skip('disabled option disable_char_analysis')
@pytest.mark.execution_timeout(10)
def test_inspector_disable_char_analysis(prod_inspector):
    inspector = prod_inspector

    result = inspector.analyse_label('ąlaptop', disable_char_analysis=True)
    assert result['graphemes'] is None
    assert 'any_types' not in result

    result = inspector.analyse_label('ąlaptop', disable_char_analysis=False)
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
        ('abc🩷.', None),  # Unknown
    ]
)
def test_inspector_all_script(prod_inspector, label, script):
    result = prod_inspector.analyse_label(label)
    assert result['all_script'] == script


def test_inspector_aggregation_works_before_truncation(prod_inspector):
    label = 'abc123'
    result = prod_inspector.analyse_label(label, truncate_graphemes=3)
    assert [c['value'] for g in result['graphemes'] for c in g['chars']] == ['a', 'b', 'c']
    assert result['all_type'] == None
    assert sorted(result['any_types']) == sorted(['simple_letter', 'simple_number'])
    assert result['all_script'] == 'Latin'
    assert sorted(result['any_scripts']) == sorted(['Latin', 'Common'])


# probably not possible to test since all unknown chars are disallowed
@pytest.mark.skip('label is unnormalized')
def test_inspector_label_of_unknown_char(prod_inspector):
    label = '🩷'
    result = prod_inspector.analyse_label(label)
    assert result['graphemes'][0]['chars'][0]['label'] == 'Unknown character in Unknown script'


def test_inspector_grapheme_script(prod_inspector):
    label = '١-\u0610'
    result = prod_inspector.analyse_label(label)
    assert result['graphemes'][0]['script'] == 'Arabic'
    assert result['graphemes'][1]['script'] == 'Arabic'
    # TODO grapheme with multiple scripts?


def test_inspector_grapheme_class(prod_inspector):
    label = 'ع-\u0610👩🏻‍🤝‍👩🏼'
    result = prod_inspector.analyse_label(label)
    assert result['graphemes'][0]['type'] == 'other_letter'
    assert result['graphemes'][1]['type'] == 'special'
    assert result['graphemes'][2]['type'] == 'emoji'


def test_inspector_grapheme_label(prod_inspector):
    label = '١-\u0610👩🏻‍🤝‍👩🏼'
    result = prod_inspector.analyse_label(label)
    assert result['graphemes'][0]['name'] == 'ARABIC-INDIC DIGIT ONE'
    assert result['graphemes'][1]['name'] == 'Combined Character'
    assert result['graphemes'][2]['name'] == 'WOMEN HOLDING HANDS: LIGHT SKIN TONE, MEDIUM-LIGHT SKIN TONE'


@pytest.mark.parametrize(
    'input_label, normalized_input, expected_canonical_label, expected_beautiful_canonical_label',
    [
        ('pure-words', True, None, None),  # no confusables
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
def test_canonical_label(prod_inspector,
                         input_label: str,
                         normalized_input: bool,
                         expected_canonical_label: str,
                         expected_beautiful_canonical_label: str):
    result = prod_inspector.analyse_label(input_label)
    if normalized_input:
        assert result['canonical_confusable_label'] == expected_canonical_label
        assert result['beautiful_canonical_confusable_label'] == expected_beautiful_canonical_label
    else:
        assert result['canonical_confusable_label'] is None
        assert result['beautiful_canonical_confusable_label'] is None


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
    ('のtakb\u0327', None),
])
def test_inspector_all_script(prod_inspector, label, script):
    result = prod_inspector.analyse_label(label)
    assert result['all_script'] == script


def test_inspector_suggested_replacement(prod_inspector):
    result = prod_inspector.analyse_label('bs\u0327a')
    assert result['suggested_replacement'][0]['value'] == 'ş'

    result = prod_inspector.analyse_label('a\u200db')
    assert len(result['suggested_replacement']) == 0


@pytest.mark.parametrize('label,all_type', [
    ('-', 'hyphen'),
    ('_', 'underscore'),
    ('$', 'dollarsign'),
])
def test_inspector_named_character_types(prod_inspector, label, all_type):
    resp = prod_inspector.analyse_label(label)
    assert resp['all_type'] == all_type


def test_inspector_multi_char_grapheme_type(prod_inspector):
    resp = prod_inspector.analyse_label('ᄅᄅᄅ')
    assert resp['graphemes'][0]['type'] == 'other_letter'


def test_problem1_beautiful_flag(prod_inspector):
    label = '🇬🇧'
    resp = prod_inspector.analyse_label(label)
    assert resp['beautiful_label'] == label


@pytest.mark.parametrize('label', [
    '🧑‍🤝‍🧑🏿', '🤼🏾‍♂', '👩‍❤‍👩🏿', '🧙‍♂🏼🏼🏼🏼'
])
def test_problem2_unnormalized(prod_inspector, label):
    resp = prod_inspector.analyse_label(label)
    assert resp['status'] == 'unnormalized'


@pytest.mark.parametrize('label,g_link,c_links', [
    ('a', 'https://unicodeplus.com/U+0061', ['https://unicodeplus.com/U+0061']),
    ('-\u0610', 'https://unicode.link/inspect/utf8:2d.d8.90', ['https://unicodeplus.com/U+002D', 'https://unicodeplus.com/U+0610']),
    ('🧌', 'http://📙.la/🧌', ['http://📙.la/🧌']),
    ('👩🏿‍🦲', 'http://📙.la/👩🏿‍🦲', ["http://📙.la/👩", "http://📙.la/🏿", "http://📙.la/‍", "http://📙.la/🦲"]),
])
def test_inspector_char_links(prod_inspector, label, g_link, c_links):
    resp = prod_inspector.analyse_label(label)
    assert resp['graphemes'][0]['link'] == g_link
    assert [c['link'] for c in resp['graphemes'][0]['chars']] == c_links


def test_inspector_punycode(prod_inspector):
    resp = prod_inspector.analyse_label('xn--😵💫😵💫😵💫')
    assert resp['dns_hostname_support'] == False
    assert resp['punycode_compatibility'] == 'COMPATIBLE'
    assert resp['punycode_encoding'] == 'xn--xn---8v63caa362abab'

    resp = prod_inspector.analyse_label('x' * 64)
    assert resp['dns_hostname_support'] == False
    assert resp['punycode_compatibility'] == 'LABEL_TOO_LONG'
    assert resp['punycode_encoding'] == None


def test_inspector_font_support(prod_inspector):
    resp = prod_inspector.analyse_label('a✊🏾')
    assert resp['font_support_all_os'] == True
    assert resp['graphemes'][0]['font_support_all_os'] == True
    assert resp['graphemes'][1]['font_support_all_os'] == True

    resp = prod_inspector.analyse_label('✊🏾' + chr(5922) + '👊🏿')
    assert resp['font_support_all_os'] == False
    assert resp['graphemes'][0]['font_support_all_os'] == True
    assert resp['graphemes'][1]['font_support_all_os'] == False
    assert resp['graphemes'][2]['font_support_all_os'] == False
