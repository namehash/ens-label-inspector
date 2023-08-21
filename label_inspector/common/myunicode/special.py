from bisect import bisect_right
from .data import MY_UNICODE_DATA


RANGES = MY_UNICODE_DATA['special']
STARTS, DATA = RANGES['starts'], RANGES['data']


def bisect_special(chr: str) -> str:
    return DATA[bisect_right(STARTS, ord(chr)) - 1]


def get_special_name(chr: str) -> str:
    data = bisect_special(chr)

    if data['name'].startswith('CJK Ideograph'):
        return f'CJK UNIFIED IDEOGRAPH-{ord(chr):04X}'
    # TODO add support for other special classes (Hangul, etc)
    else:
        raise KeyError


def get_special_category(chr: str) -> str:
    return bisect_special(chr)['category']


def get_special_combining(chr: str) -> str:
    return bisect_special(chr)['combining']
