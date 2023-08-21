from typing import Iterable
import os


DATA_JSON_PATH = os.path.join(os.path.dirname(__file__), 'myunicode.json')


def get_data_lines(lines: Iterable[str]) -> Iterable[str]:
    """
    Remove leading/trailing whitespace,
    ignore empty and commented-out lines (#).
    """
    lines = map(str.strip, lines)
    return (l for l in lines if len(l) > 0 and not l.startswith('#'))
