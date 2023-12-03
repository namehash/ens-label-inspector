from typing import Iterable
import os


DATA_JSON_PATH = os.path.join(os.path.dirname(__file__), "myunicode.json")


def get_data_lines(lines: Iterable[str]) -> Iterable[str]:
    """
    Remove leading/trailing whitespace,
    ignore empty and commented-out lines (#).
    """
    lines = map(str.strip, lines)
    return (line for line in lines if len(line) > 0 and not line.startswith("#"))
