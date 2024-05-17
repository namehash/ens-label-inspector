from __future__ import annotations
from typing import Optional, List, TYPE_CHECKING

from label_inspector.common import myunicode
from label_inspector.components.font_support import aggregate_font_support

from .analysis_framework import AnalysisBase, analysis_object, field, agg_only, agg_all
from .char_analysis import CharAnalysis

if TYPE_CHECKING:
    from .label_analysis import LabelAnalysis


def v2num(version: str) -> int:
    return [int(x) for x in version.split('.')]


@analysis_object
class GraphemeAnalysis(AnalysisBase):
    '''
    Basic analysis of a grapheme (no confusables).
    '''

    def __init__(self, grapheme: str, parent):
        self.grapheme = grapheme
        self.root: LabelAnalysis = parent.root

    @field
    def value(self) -> str:
        return self.grapheme

    @field
    def _chars_untruncated(self) -> List[CharAnalysis]:
        """
        Untruncated char analysis.
        """
        return [CharAnalysis(char, self) for char in self.grapheme]

    @field
    def _single_char(self) -> Optional[CharAnalysis]:
        """
        If the grapheme is a single char, return that char's analysis.
        """
        return agg_only(self._chars_untruncated)

    @field
    def chars(self) -> List[CharAnalysis]:
        """
        Truncated char analysis.
        """
        return self._chars_untruncated[:self.root.config.truncate_chars]

    @field
    def name(self) -> str:
        """
        Name of the grapheme.
        Emoji sequence, single-character name or Combined Character.
        """
        return myunicode.emoji_zwj_sequence_name(self.grapheme) or \
            myunicode.emoji_sequence_name(self.grapheme) or \
            getattr(self._single_char, 'name', 'Combined Character')

    @field
    def codepoint(self) -> Optional[str]:
        return getattr(self._single_char, 'codepoint', None)

    @field
    def link(self) -> Optional[str]:
        if self.type == 'emoji':
            return self.root.i.f.emoji_link(self.grapheme)
        else:
            return getattr(self._single_char, 'link', None) or \
                   self.root.i.f.multi_char_link(self.grapheme)

    @field
    def script(self) -> str:
        scr = myunicode.script_of(self.grapheme)
        return scr if scr is not None else 'Combined'

    @field
    def type(self) -> str:
        if self.grapheme == '\ufe0f':  # because it is treated as emoji
            return 'invisible'
            
        if myunicode.is_emoji(self.grapheme):
            return 'emoji'

        cls = agg_all([c.type for c in self._chars_untruncated])

        return cls or 'special'

    @field
    def font_support_all_os(self) -> Optional[bool]:
        if self.type == 'emoji':
            return self.root.i.f.font_support.check_support(self.grapheme)
        else:
            return aggregate_font_support([self.root.i.f.font_support.check_support(c) for c in self.grapheme])

    @field
    def description(self) -> str:
        if self.type == 'simple_letter':
            return 'A-Z letter'
        elif self.type == 'simple_number':
            return '0-9 number'
        elif self.type == 'other_letter':
            return f'{self.script} letter'
        elif self.type == 'other_number':
            return f'{self.script} number'
        elif self.type == 'hyphen':
            return 'Hyphen'
        elif self.type == 'dollarsign':
            return 'Dollar sign'
        elif self.type == 'underscore':
            return 'Underscore'
        elif self.type == 'emoji':
            return 'Emoji'
        elif self.type == 'invisible':
            return 'Invisible character'
        elif self.type == 'special':
            return 'Special character'

    @field
    def unicode_version(self) -> Optional[str]:
        # try to get the version of the whole grapheme
        version = myunicode.unicode_min_version(self.grapheme)
        if version is not None:
            return version

        # fallback to the highest version of the chars
        highest_version = myunicode.unicode_min_version(self.grapheme[0])
        for char in self.grapheme[1:]:
            version = myunicode.unicode_min_version(char)
            if version is None:
                # it's best to avoid returning null (for the UI)
                # that's why we return the highest non-null version
                continue
            if highest_version is None or v2num(version) > v2num(highest_version):
                highest_version = version
        return highest_version
