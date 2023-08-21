from typing import List, Optional, Set
import regex
from label_inspector.common.myunicode import emoji_zwj_sequence_name, emoji_sequence_name, block_of
from label_inspector.common.pickle_cache import pickled_property


class AllHanguls:
    @pickled_property()
    def hangul_jamo(self) -> Set[str]:
        chars = set()
        for c in map(chr, range(0x10FFFF + 1)):
            block = block_of(c) or ''
            # only jamo, not syllables
            if block.find('Hangul') != -1 and block.find('Jamo') != -1:
                chars.add(c)
        return chars


_ALL_HANGULS = AllHanguls()
_GRAPHEME_REGEX = regex.compile(r'\X')


def split(text: str) -> List[str]:
    '''
    Returns a list of graphemes in text.
    Every Hangul Jamo character forces a break.
    For Hangul graphemes to work correctly, the text must be normalized to NFC.
    The assumption is that every Hangul character which cannot be expressed
    as a single codepoint (after NFC) will render as multiple graphemes on most platforms.
    '''
    graphemes = _GRAPHEME_REGEX.findall(text)

    if not _ALL_HANGULS.hangul_jamo.intersection(text):
        return graphemes

    out = []
    for g in graphemes:
        i = 0
        j = 1
        while j < len(g):
            # split on hangul
            if g[j] in _ALL_HANGULS.hangul_jamo:
                out.append(g[i:j])
                i = j
            j += 1
        out.append(g[i:j])
    return out


def name(grapheme: str) -> Optional[str]:
    '''
    Returns the name of the grapheme or None if it has no name.
    Currently, only emoji ZWJ sequences and other emoji sequences are supported.
    '''
    return emoji_sequence_name(grapheme) or emoji_zwj_sequence_name(grapheme)
