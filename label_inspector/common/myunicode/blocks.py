from bisect import bisect_right
from .data import MY_UNICODE_DATA


RANGES = MY_UNICODE_DATA['blocks']
STARTS, NAMES = RANGES['starts'], RANGES['names']


def bisect_block(chr: str) -> str:
    return NAMES[bisect_right(STARTS, ord(chr)) - 1]
