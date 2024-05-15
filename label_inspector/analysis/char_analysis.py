from __future__ import annotations
from typing import TYPE_CHECKING, Optional

from label_inspector.common import myunicode

from .analysis_framework import AnalysisBase, analysis_object, field

if TYPE_CHECKING:
    from .grapheme_analysis import GraphemeAnalysis


@analysis_object
class CharAnalysis(AnalysisBase):
    def __init__(self, char: str, parent_grapheme: GraphemeAnalysis):
        self._char = char
        self.parent_grapheme = parent_grapheme
        self.root = parent_grapheme.root

    @field
    def value(self) -> str:
        return self._char

    @field
    def script(self) -> str:
        # will never return None, because it's a single character
        return myunicode.script_of(self._char)

    @field
    def name(self) -> str:
        return myunicode.name(self._char, f'Unknown character in {self.script} script')

    @field
    def codepoint(self) -> str:
        return self.root.i.f.codepoint_hex(self._char)

    @field
    def link(self) -> str:
        if self.type == 'emoji':
            return self.root.i.f.emoji_link(self._char)
        else:
            return self.root.i.f.char_link(self._char)

    @field
    def type(self) -> str:
        # Refers to this char's parent grapheme to detect ZWJs in emoji sequences.
        if ((self._char == '\u200d' and myunicode.is_emoji(self.parent_grapheme.value))
                or myunicode.is_emoji_char(self._char)):
            return 'emoji'
        else:
            return self.root.i.f.type(self._char)

    @field
    def unicode_version(self) -> Optional[str]:
        return myunicode.unicode_min_version(self._char)
