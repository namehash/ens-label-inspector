import os
from typing import Optional
import json

from label_inspector.common.pickle_cache import pickled_property
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

        root = os.path.join(get_resource_path(self.config.inspector.fonts), 'combine_all')
        self.supported_chars_path = os.path.join(root, 'supported_chars.json')
        self.supported_emoji_path = os.path.join(root, 'supported_emoji.json')
        self.unsupported_chars_path = os.path.join(root, 'unsupported_chars.json')
        self.unsupported_emoji_path = os.path.join(root, 'unsupported_emoji.json')

        if not config.inspector.lazy_loading:
            self.supported
            self.unsupported



    def check_support(self, char: str) -> Optional[bool]:
        '''
        Check if a character is supported.
        Returns `True` if supported, `False` if unsupported, `None` if unknown.
        '''
        if char == '\uFE0F':
            return True
        char = char.replace('\uFE0F', '')
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
            return set(''.join(chr(cp) for cp in cps if cp != 0xFE0F) for cps in json.load(f))

    @pickled_property('inspector.fonts')
    def supported(self):
        supported: set[str] = set()
        # add all supported
        supported.update(self._load_chars(self.supported_chars_path))
        supported.update(self._load_emoji(self.supported_emoji_path))

        # remove all unsupported
        supported.difference_update(self._load_chars(self.unsupported_chars_path))
        supported.difference_update(self._load_emoji(self.unsupported_emoji_path))
        return supported

    @pickled_property('inspector.fonts')
    def unsupported(self):
        unsupported: set[str] = set()
        # add all unsupported
        unsupported.update(self._load_chars(self.unsupported_chars_path))
        unsupported.update(self._load_emoji(self.unsupported_emoji_path))

        # remove all supported
        unsupported.difference_update(self._load_chars(self.supported_chars_path))
        unsupported.difference_update(self._load_emoji(self.supported_emoji_path))
        return unsupported