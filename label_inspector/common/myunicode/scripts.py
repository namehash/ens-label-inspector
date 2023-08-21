from bisect import bisect_right
from .data import MY_UNICODE_DATA


RANGES = MY_UNICODE_DATA['scripts']
STARTS, NAMES = RANGES['starts'], RANGES['names']
NEUTRAL_SCRIPTS = set(('Common', 'Inherited'))


def bisect_script(chr: str) -> str:
    script = NAMES[bisect_right(STARTS, ord(chr)) - 1]
    return script if script is not None else 'Unknown'
