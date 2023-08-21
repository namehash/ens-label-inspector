import pytest
import regex

from label_inspector.config import initialize_inspector_config
from label_inspector.components.confusables import Confusables


def test_confusable():
    with initialize_inspector_config("prod_config") as config:
        test_confusables = Confusables(config)
        chars = [
            ('ą', True, 'a'),
            ('ś', True, 's'),
            ('ó', True, 'o'),
            ('ź', True, 'z'),
            ('ł', True, 'l'),
            ('ώ', True, 'ω'),
            ('ῴ', True, 'ω'),
            ('𝕤', True, 's'),
            ('ą', True, 'ą'),
            ('s', False, None),
            ('1', False, None),
            ('l', False, None),
            ('⒀', True, '(13)'),
            ('-', False, None),
            ('_', False, None),
        ]
        for char, expected_is_confusable, expected_confusables in chars:
            is_confusable = test_confusables.is_confusable(char)
            confusables = test_confusables.get_confusables(char)
            canonical = test_confusables.get_canonical(char)

            assert is_confusable == expected_is_confusable
            if is_confusable:
                assert expected_confusables in ([canonical] + confusables)


def test_confusable_simple():
    with initialize_inspector_config("prod_config") as config:
        confusables = Confusables(config)

        for k, v in confusables.confusable_graphemes.items():
            if regex.match(r'[a-z0-9-]', k, regex.ASCII):
                print([k, v], len(k), len(v))


@pytest.mark.parametrize(
    'grapheme, is_confusable, canonical',
    [
        ('👩🏿‍🦰', True, '🧑'),
        ('👩🏿', True, '🧑'),
        ('👩‍🦰', True, '🧑'),
        ('👩', True, '🧑'),
        ('🏃‍♂', True, '🏃'),
        ('🏃‍♂️', False, None),  # FEOF at the end
        ('👩🏿‍🚒', True, '🧑‍🚒'),
        ('🫱🏻‍🫲🏿', True, None),
        ('🤜🏿', True, '🤜'),
        ('*⃣', True, None),
        ('🇺🇦', False, None),
        ('🏴󠁧󠁢󠁷󠁬󠁳󠁿', False, None),
        ('⛹🏽', True, '⛹'),
        ('🎅🏿', True, '🎅'),
        ('🧝🏼', True, '🧝'),
    ]
)
def test_grapheme_confusable(grapheme: str, is_confusable: bool, canonical: str):
    with initialize_inspector_config("prod_config") as config:
        confusables = Confusables(config)

        assert confusables.is_confusable_grapheme(grapheme) == is_confusable

        if is_confusable:
            assert confusables.get_canonical_grapheme(grapheme) == canonical


@pytest.mark.parametrize(
    'string, is_confusable, canonical',
    [
        ('ą', True, 'a'),
        ('s', False, None),
        ('👩‍🦰', True, '🧑'),
        ('👩', True, '🧑'),
        ('a', False, None),
        ('b\u0328', True, 'b'),
        ('b\u0329', True, 'b'),
        ('f̡̨̢̝̭͓̖͉͐͐́̎̇ͪ̚', True, 'f'),
        ('🫱🏻‍🫲🏿', True, None),
        ('🤜🏿', True, '🤜'),
        ('*⃣', True, None),
        ('🇺🇦', False, None),
    ]
)
def test_confusables(string: str, is_confusable: bool, canonical: str):
    with initialize_inspector_config("prod_config") as config:
        confusables = Confusables(config)

        assert confusables.is_confusable(string) == is_confusable

        if is_confusable:
            assert confusables.get_canonical(string) == canonical
