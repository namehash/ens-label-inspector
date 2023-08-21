from typing import Dict
from functools import cache
import regex


class OnDemandRegex:
    def __init__(self, patterns: Dict[str, str], lazy: bool = True):
        self.patterns = patterns
        if not lazy:
            for name in patterns:
                self[name]
    
    @cache
    def __getitem__(self, key: str):
        return regex.compile(self.patterns[key])
