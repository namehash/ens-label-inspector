import os
from typing import Optional
import json
from label_inspector.data import get_resource_path


def aggregate_font_support(support_levels: list[Optional[bool]]) -> Optional[bool]:
    '''
    Aggregate font support levels.
    Returns `True` if all supported, `False` if at least one unsupported, `None` otherwise.
    '''
    unknown = False
    for level in support_levels:
        if level is None:
            unknown = True
        elif not level:
            return False
    return None if unknown else True


class FontSupport:
    def __init__(self, config):
        self.config = config

        self.supported: set[str] = set()
        self.unsupported: set[str] = set()

        root = os.path.join(get_resource_path(self.config.inspector.fonts), 'combine_all')
        supported_chars_path = os.path.join(root, 'supported_chars.json')
        supported_emoji_path = os.path.join(root, 'supported_emoji.json')
        unsupported_chars_path = os.path.join(root, 'unsupported_chars.json')
        unsupported_emoji_path = os.path.join(root, 'unsupported_emoji.json')

        # add all supported
        self.supported.update(self._load_chars(supported_chars_path))
        self.supported.update(self._load_emoji(supported_emoji_path))

        # remove all unsupported
        self.supported.difference_update(self._load_chars(unsupported_chars_path))
        self.supported.difference_update(self._load_emoji(unsupported_emoji_path))

        # add all unsupported
        self.unsupported.update(self._load_chars(unsupported_chars_path))
        self.unsupported.update(self._load_emoji(unsupported_emoji_path))

        # remove all supported
        self.unsupported.difference_update(self._load_chars(supported_chars_path))
        self.unsupported.difference_update(self._load_emoji(supported_emoji_path))

    def check_support(self, char: str) -> Optional[bool]:
        '''
        Check if a character is supported.
        Returns `True` if supported, `False` if unsupported, `None` if unknown.
        '''
        if char in self.supported:
            return True
        elif char in self.unsupported:
            return False
        else:
            return None

    def _load_chars(self, path):
        # list of codepoints
        with open(path, 'r', encoding='utf-8') as f:
            return set(chr(cp) for cp in json.load(f))

    def _load_emoji(self, path):
        # list of list of codepoints
        with open(path, 'r', encoding='utf-8') as f:
            return set(''.join(chr(cp) for cp in cps) for cps in json.load(f))
