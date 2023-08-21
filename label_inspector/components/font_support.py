import os
import json
from label_inspector.data import get_resource_path


class FontSupport:
    def __init__(self, config):
        self.config = config

        self.supported: list[str] = set()

        root = os.path.join(get_resource_path(self.config.inspector.fonts), 'combine_all')
        supported_chars_path = os.path.join(root, 'supported_chars.json')
        supported_emoji_path = os.path.join(root, 'supported_emoji.json')
        unsupported_chars_path = os.path.join(root, 'unsupported_chars.json')
        unsupported_emoji_path = os.path.join(root, 'unsupported_emoji.json')

        self.supported.update(self._load_chars(supported_chars_path))
        self.supported.update(self._load_emoji(supported_emoji_path))

        self.supported.difference_update(self._load_chars(unsupported_chars_path))
        self.supported.difference_update(self._load_emoji(unsupported_emoji_path))

    def all_os(self, char):
        return char in self.supported

    def _load_chars(self, path):
        # list of codepoints
        with open(path, 'r', encoding='utf-8') as f:
            return set(chr(cp) for cp in json.load(f))

    def _load_emoji(self, path):
        # list of list of codepoints
        with open(path, 'r', encoding='utf-8') as f:
            return set(''.join(chr(cp) for cp in cps) for cps in json.load(f))
