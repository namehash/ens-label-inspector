from typing import List, Optional, Set
import regex
from label_inspector.common.myunicode import emoji_zwj_sequence_name, emoji_sequence_name, block_of, is_emoji
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

INVISIBLE_CHARACTER_JOINERS = invisible_joiners = {
        '\U0000034F': 'COMBINING GRAPHEME JOINER',
        '\U0000061C': 'ARABIC LETTER MARK',
        '\U000017B4': 'KHMER VOWEL INHERENT AQ',
        '\U000017B5': 'KHMER VOWEL INHERENT AA',
        '\U0000200C': 'ZERO WIDTH NON-JOINER',
        '\U0000200D': 'ZERO WIDTH JOINER',
        '\U0000200E': 'LEFT-TO-RIGHT MARK',
        '\U0000200F': 'RIGHT-TO-LEFT MARK',
        '\U0000206F': 'NOMINAL DIGIT SHAPES',
        '\U0000FE00': '',
        '\U0000FE01': '',
        '\U0000FE02': '',
        '\U0000FE03': '',
        '\U0000FE04': '',
        '\U0000FE05': '',
        '\U0000FE06': '',
        '\U0000FE07': '',
        '\U0000FE08': '',
        '\U0000FE09': '',
        '\U0000FE0A': '',
        '\U0000FE0B': '',
        '\U0000FE0C': '',
        '\U0000FE0D': '',
        '\U0000FE0E': '',
        '\U0000FE0F': '',
        '\U0000FEFF': 'ZERO WIDTH NO-BREAK SPACE',
        '\U0001D159': 'MUSICAL SYMBOL NULL NOTEHEAD',
        '\U0001D173': 'MUSICAL SYMBOL BEGIN BEAM',
        '\U0001D174': 'MUSICAL SYMBOL END BEAM',
        '\U0001D175': 'MUSICAL SYMBOL BEGIN TIE',
        '\U0001D176': 'MUSICAL SYMBOL END TIE',
        '\U0001D177': 'MUSICAL SYMBOL BEGIN SLUR',
        '\U0001D178': 'MUSICAL SYMBOL END SLUR',
        '\U0001D179': 'MUSICAL SYMBOL BEGIN PHRASE',
        '\U0001D17A': 'MUSICAL SYMBOL END PHRASE',
    }


def split(text: str, split_invisible: bool = True) -> List[str]:
    '''
    Returns a list of graphemes in text.
    Every Hangul Jamo character forces a break.
    For Hangul graphemes to work correctly, the text must be normalized to NFC.
    The assumption is that every Hangul character which cannot be expressed
    as a single codepoint (after NFC) will render as multiple graphemes on most platforms.
    If `split_invisible` is true then INVISIBLE_CHARACTER_JOINERS are treated as graphemes if they are not part of an emoji sequence.
    '''
    graphemes = _GRAPHEME_REGEX.findall(text)

    if split_invisible:
        out = []
        for g in graphemes:
            i = len(g) - 1
            while i >= 0:
                if g[i] in INVISIBLE_CHARACTER_JOINERS:
                    i -= 1
                else:
                    break
            i += 1
            base = g[:i]

            if i == len(g):  # no fe0fs
                out.append(base)
            else:
                if g[i] == '\ufe0f' and is_emoji(base):  # if base is emoji, then we want to keep the fe0f
                    i += 1
                if i > 0:
                    out.append(g[:i])
                for j in range(i, len(g)):
                    out.append(g[j])
        graphemes = out

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
