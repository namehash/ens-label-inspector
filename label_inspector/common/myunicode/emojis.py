from typing import Iterator
from bisect import bisect_right

from more_itertools import chunked

from .data import MY_UNICODE_DATA


RANGES = MY_UNICODE_DATA['emojis']
STARTS, IS_EMOJI = RANGES['starts'], RANGES['is_emoji']


def bisect_emoji(chr: str) -> bool:
    return IS_EMOJI[bisect_right(STARTS, ord(chr)) - 1]


def emoji_char_iterator() -> Iterator[str]:
    start_idx = IS_EMOJI.index(True)
    for start, end in chunked(STARTS[start_idx:], 2, strict=True):
        for codepoint in range(start, end):
            yield chr(codepoint)
