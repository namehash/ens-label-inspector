from .data import MY_UNICODE_DATA
from .blocks import bisect_block
from .scripts import bisect_script, NEUTRAL_SCRIPTS
from .emojis import bisect_emoji, emoji_char_iterator
from .special import get_special_name, get_special_category, get_special_combining

from typing import Optional, Iterator
from itertools import chain
import unicodedata


def name(chr: str, default=None) -> str:
    """
    Returns the name of the unicode character.
    If the character does not have a name,
    returns default if given or throws an exception.
    """
    if len(chr) != 1:
        raise TypeError('name() argument 1 must be a unicode character, not str')
    try:
        return MY_UNICODE_DATA['name'][ord(chr)]
    except KeyError:
        try:
            return get_special_name(chr)
        except KeyError:
            # fallback
            if default is None:
                # do not pass default to make sure the function throws
                # (when passed default=None it does not throw)
                return unicodedata.name(chr)
            return unicodedata.name(chr, default)


def category(chr: str) -> str:
    """
    Returns the category of the unicode character.
    If the character does not have a category, returns 'Cn'.
    """
    if len(chr) != 1:
        raise TypeError('category() argument must be a unicode character, not str')
    try:
        return MY_UNICODE_DATA['category'][ord(chr)]
    except KeyError:
        try:
            return get_special_category(chr)
        except KeyError:
            # fallback
            return unicodedata.category(chr)


def combining(chr: str) -> int:
    """
    Returns the combining class of the unicode character.
    If the character does not have a combining class, returns 0.
    """
    if len(chr) != 1:
        raise TypeError('combining() argument must be a unicode character, not str')
    try:
        return MY_UNICODE_DATA['combining'][ord(chr)]
    except KeyError:
        try:
            return get_special_combining(chr)
        except KeyError:
            # fallback
            return unicodedata.combining(chr)


def block_of(chr: str) -> Optional[str]:
    """
    Returns the block of the character.
    If the character does not have a block, returns None.
    """
    if len(chr) != 1:
        raise TypeError('block_of() argument must be a unicode character, not str')
    return bisect_block(chr)


def script_of(text: str) -> Optional[str]:
    """
    Returns the script of text, or None if text has many non-neutral scripts.
    
    Common and Inherited scripts are considered neutral.

    Empty string returns None.

    Script priority:
    Non-neutral > Common > Inherited
    """
    script = None

    for c in text:
        s = bisect_script(c)

        if script is None:
            # first script
            script = s
        elif s != script:
            # differing scripts

            if script == 'Common':
                if s not in NEUTRAL_SCRIPTS:
                    # common overriden only by non-neutral
                    script = s
            elif script == 'Inherited':
                # inherited overridden by everything
                script = s
            elif s not in NEUTRAL_SCRIPTS:
                # non-neutral conflicts with non-neutral
                return None

    return script


def is_emoji_char(chr: str) -> bool:
    """
    Returns True if the character is an emoji.
    """
    if len(chr) != 1:
        raise TypeError('is_emoji() argument must be a unicode character, not str')
    return bisect_emoji(chr)


def is_emoji_sequence(text: str) -> bool:
    """
    Returns True if text is a valid emoji sequence.
    """
    return text in MY_UNICODE_DATA['emoji_sequences']


def emoji_sequence_name(text: str) -> Optional[str]:
    """
    Returns the name of the emoji ZWJ sequence or None if text is not an emoji sequence.
    """
    return MY_UNICODE_DATA['emoji_sequences'].get(text)


def is_emoji_zwj_sequence(text: str) -> bool:
    """
    Returns True if text is a valid emoji ZWJ sequence.
    """
    return text in MY_UNICODE_DATA['emoji_zwj_sequences']


def emoji_zwj_sequence_name(text: str) -> Optional[str]:
    """
    Returns the name of the emoji ZWJ sequence or None if text is not a ZWJ sequence.
    """
    return MY_UNICODE_DATA['emoji_zwj_sequences'].get(text)


def is_emoji(text: str) -> bool:
    """
    Returns True if grapheme is an emoji.
    """
    # all multi-character emoji graphemes should be present in emoji-sequences or emoji-zwj-sequences
    # if it is not there, then we assume that it can be emoji only if it has only one character
    return is_emoji_sequence(text) \
        or is_emoji_zwj_sequence(text) \
        or (len(text) == 1 and is_emoji_char(text[0]))


def emoji_iterator() -> Iterator[str]:
    return chain(emoji_char_iterator(),
                 MY_UNICODE_DATA['emoji_sequences'].keys(),
                 MY_UNICODE_DATA['emoji_zwj_sequences'].keys())


def emoji_name(text: str) -> Optional[str]:
    if not is_emoji(text):
        return None

    if is_emoji_sequence(text):
        return emoji_sequence_name(text)

    if is_emoji_zwj_sequence(text):
        return emoji_zwj_sequence_name(text)

    return name(text)


def is_numeric(chr: str) -> bool:
    """
    Returns True if the character is numeric (category N).
    """
    if len(chr) != 1:
        raise TypeError('is_numeric() argument must be a unicode character, not str')
    return category(chr).startswith('N')
