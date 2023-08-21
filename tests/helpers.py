import regex
from typing import List, Tuple
import os
from label_inspector.common import myunicode
from label_inspector import data as inspector_data
from ens_normalize import ens_normalize, ens_beautify, ens_cure, ens_process, is_ens_normalized, DisallowedSequence, CurableSequence

NoneType = type(None)

TESTS_DATA_PATH = os.path.join(os.path.dirname(inspector_data.__file__), 'tests')

VERSION_REGEX = regex.compile(r'^[0-9]+\.[0-9]+\.[0-9]+$')
SPECIAL_CHAR_REGEX = regex.compile(r'[^a-zA-Z0-9.-]')
NAMEHASH_REGEX = regex.compile(r'^\[[0-9a-f]{64}\]$')


def is_type(obj, *types):
    # not using isinstance() because it allows subclasses
    t = type(obj)
    return any(t is u for u in types)


def check_inspector_normalized_response(label,
                                        resp,
                                        truncate_confusables=None,
                                        truncate_graphemes=None,
                                        truncate_chars=None):
    assert sorted(resp.keys()) == sorted([
        'label',
        'status',
        'version',
        'char_length',
        'grapheme_length',
        'all_type',
        'any_types',
        'all_script',
        'any_scripts',
        'confusable_count',
        'graphemes',
        'beautiful_label',
        'canonical_confusable_label',
        'beautiful_canonical_confusable_label',
        'dns_hostname_support',
        'punycode_compatibility',
        'punycode_encoding',
        'font_support_all_os',
    ])

    assert resp['label'] == label
    assert resp['status'] == 'normalized'
    assert resp['label'] == ens_normalize(label)
    assert VERSION_REGEX.match(resp['version'])
    assert resp['char_length'] == len(label)
    assert resp['grapheme_length'] == len(myunicode.grapheme.split(label))

    try:
        beautiful_label = ens_beautify(label)
    except DisallowedSequence:
        beautiful_label = None
    assert resp['beautiful_label'] == beautiful_label

    assert is_type(resp['all_type'], str, NoneType)
    assert is_type(resp['any_types'], list, NoneType)
    assert is_type(resp['all_script'], str, NoneType)
    assert is_type(resp['any_scripts'], list)
    assert is_type(resp['confusable_count'], int)

    # check returned characters
    # the order of the characters must match the input label
    if truncate_graphemes is not None:
        assert len(resp['graphemes']) <= truncate_graphemes

    for grapheme in resp['graphemes']:
        assert sorted(grapheme.keys()) == sorted([
            'value',
            'chars',
            'name',
            'codepoint',
            'link',
            'script',
            'type',
            'font_support_all_os',
            'confusables_other',
            'confusables_canonical',
        ])
        assert type(grapheme['value']) == str
        assert type(grapheme['chars']) == list
        assert type(grapheme['name']) == str
        assert type(grapheme['script']) == str
        assert grapheme['confusables_canonical'] is None or type(grapheme['confusables_canonical']) == dict
        if grapheme['confusables_canonical'] is not None:
            if len(myunicode.grapheme.split(grapheme['confusables_canonical']['value'])) != 1:
                assert sorted(grapheme['confusables_canonical'].keys()) == sorted([
                    'value',
                    'chars',
                ])
            else:
                sorted(grapheme['confusables_canonical'].keys()) == sorted([
                    'value',
                    'chars',
                    'name',
                    'codepoint',
                    'link',
                    'script',
                    'type',
                ])

        if truncate_confusables is not None:
            assert len(grapheme['confusables_other']) <= truncate_confusables

        for conf in grapheme['confusables_other']:
            if len(myunicode.grapheme.split(conf['value'])) != 1:
                assert sorted(conf.keys()) == sorted([
                    'value',
                    'chars',
                ])
            else:
                sorted(conf.keys()) == sorted([
                    'value',
                    'chars',
                    'name',
                    'codepoint',
                    'link',
                    'script',
                    'type',
                ])

        if truncate_chars is not None:
            assert len(grapheme['chars']) <= truncate_chars
        else:
            assert len(grapheme['chars']) > 0

    all_chars = [c for grapheme in resp['graphemes'] for c in grapheme['chars']]
    assert len(resp['graphemes']) <= len(all_chars)
    # apply chars in grapheme truncation to original name
    name_chars = label if truncate_chars is None else \
        (c for g in myunicode.grapheme.split(label) for c in g[:truncate_chars])
    for char, name_char in zip(all_chars, name_chars):
        assert sorted(char.keys()) == sorted([
            'value',
            'script',
            'name',
            'codepoint',
            'link',
            'type',
            # 'duplicated_combining_mark'
        ])

        assert char['value'] == name_char
        assert type(char['script']) == str
        assert type(char['name']) == str
        assert char['codepoint'].startswith('0x')
        if char['type'] == 'emoji':
            assert char['link'] == f'http://📙.la/{char["value"]}'
        else:
            assert char['link'] == f'https://unicodeplus.com/U+{ord(char["value"]):04X}'
        assert type(char['type']) == str


def check_inspector_unnormalized_response(label,
                                          resp,
                                          truncate_confusables=None,
                                          truncate_graphemes=None,
                                          truncate_chars=None):
    assert sorted(resp.keys()) == sorted([
        'label',
        'status',
        'version',
        'cured_label',
        'canonical_confusable_label',
        'beautiful_canonical_confusable_label',
        'normalization_error_message',
        'normalization_error_details',
        'normalization_error_code',
        'disallowed_sequence_start',
        'disallowed_sequence',
        'suggested_replacement',
    ])

    assert resp['label'] == label
    try:
        cured = ens_cure(label)
    except DisallowedSequence:
        cured = None
    assert resp['cured_label'] == cured
    assert resp['status'] == 'unnormalized'
    assert VERSION_REGEX.match(resp['version'])
    try:
        normalized = ens_normalize(label)
    except DisallowedSequence:
        normalized = None
    assert resp['canonical_confusable_label'] == normalized
    res = ens_process(label, do_normalizations=True)
    error = res.error or (res.normalizations[0] if res.normalizations else None)
    assert resp['normalization_error_message'] == error.general_info
    if isinstance(error, CurableSequence):
        assert resp['normalization_error_details'] == error.sequence_info
        assert resp['label'][resp['disallowed_sequence_start'] : resp['disallowed_sequence_start'] + len(error.sequence)] == error.sequence
        assert ''.join(c['value'] for c in resp['disallowed_sequence']) == error.sequence
        assert ''.join(c['value'] for c in resp['suggested_replacement']) == error.suggested
    else:
        assert resp['normalization_error_details'] is None
        assert resp['disallowed_sequence_start'] is None
        assert resp['disallowed_sequence'] is None
        assert resp['suggested_replacement'] is None
    assert resp['normalization_error_code'] == error.code


def check_inspector_response(label,
                             resp,
                             truncate_confusables=None,
                             truncate_graphemes=None,
                             truncate_chars=None):
    """
    Checks that the response from the inspector is valid.
    Verifies only field names and types without exact values.
    """
    if is_ens_normalized(label):
        check_inspector_normalized_response(label,
                                            resp,
                                            truncate_confusables=truncate_confusables,
                                            truncate_graphemes=truncate_graphemes,
                                            truncate_chars=truncate_chars,)
    else:
        check_inspector_unnormalized_response(label,
                                              resp,
                                              truncate_confusables=truncate_confusables,
                                              truncate_graphemes=truncate_graphemes,
                                              truncate_chars=truncate_chars)


def generate_example_names(count, input_filename=os.path.join(TESTS_DATA_PATH, 'primary.csv')):
    with open(input_filename, 'r', encoding='utf-8') as f:
        num_lines = sum(1 for _ in f)
        f.seek(0)

        # ensure uniform sampling of lines
        # from the input file
        stride = max(1, num_lines // count)

        i = 0
        for line in f:
            # strip \n
            name = line[:-1]

            # skip simple names
            if SPECIAL_CHAR_REGEX.search(name) is None:
                continue

            if i % stride == 0:
                yield name

            i += 1


def load_new_unicode_chars(unicode_version: str) -> List[Tuple[str, str]]:
    """
    Returns a list of characters (with names) added in unicode_version.
    """
    with open(os.path.join(TESTS_DATA_PATH, f'unicode{unicode_version}.txt'), encoding='utf-8') as f:
        chars = []
        for line in f:
            line = line.strip()
            if len(line) == 0 or line.startswith('#'):
                continue

            code, name = line.split(';')
            chars.append((chr(int(code, 16)), name))

        return chars
