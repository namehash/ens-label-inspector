from typing import Dict, Callable, Union, List, Iterable, Optional
from functools import cached_property

import regex
import idna
from ens_normalize import ens_normalize, ens_beautify, ens_tokenize, is_ens_normalized, DisallowedSequence
import unicodedata

from label_inspector.common import myunicode
from label_inspector.common.on_demand_regex import OnDemandRegex
from label_inspector.components.confusables import Confusables, SimpleConfusables
from label_inspector.components.font_support import FontSupport


class Features:
    def __init__(self, config):
        self.config = config

        lazy_loading = config.inspector.lazy_loading

        self.full_confusables = Confusables(self.config)
        self.simple_confusables = SimpleConfusables(self.config)
        self.font_support = FontSupport(self.config)

        self.regexp_patterns = {
            'simple_letter': '^[a-z]+$',
            'numeric': '^[0-9]+$',
            'latin-alpha-numeric': '^[a-z0-9]+$',
            'simple': '^[a-z0-9-]+$',
            'is_letter': r'^(\p{Ll}|\p{Lu}|\p{Lt}|\p{Lo})+$',
            'is_number': r'^\p{N}+$',
            'is_namehash': r'^\[[0-9a-f]{64}\]$',
        }

        self.compiled_regexp_patterns = OnDemandRegex(self.regexp_patterns, lazy=lazy_loading)

        # self.classes_config: Dict[str, Callable] = {
        #     'other_letter': self.is_letter,
        #     'other_number': self.simple_number,
        #     'hyphen': self.is_hyphen,
        #     'invisible': self.invisible,
        #     'emoji': self.is_emoji,
        #     'simple': self.simple,
        #     'simple_letter': self.simple_letter,
        #     'simple_number': self.simple_number,
        #     # 'simple_letter_emoji': self.simple_letter_emoji,
        # }
        # self.token_classes_config: Dict[str, Callable] = {
        #     'other_letter': self.is_letter,
        #     'other_number': self.simple_number,
        #     'hyphen': self.is_hyphen,
        #     'invisible': self.invisible,
        #     'emoji': self.is_emoji,
        #     'simple': self.simple,
        #     'simple_letter': self.simple_letter,
        #     'simple_number': self.simple_number,
        # }

        self.types_config: Dict[str, Callable] = {
            'simple_letter': self.simple_letter,
            'simple_number': self.simple_number,
            'other_letter': self.is_letter,
            'other_number': self.is_number,
            'hyphen': self.is_hyphen,
            'dollarsign': self.is_dollarsign,
            'underscore': self.is_underscore,
            'invisible': self.invisible,
            # 'emoji': myunicode.is_emoji,
        }

        # if not lazy_loading:
        #     self.emoji_regexp

    # @cached_property
    # def emoji_regexp(self):
    #     from emoji import unicode_codes
    #     emojis = sorted(unicode_codes.EMOJI_DATA, key=len, reverse=True)
    #     emoji_pattern = u'(' + u'|'.join(regex.escape(u) for u in emojis) + u')'
    #     patterns = {
    #         'is_emoji': '^(' + emoji_pattern + ')+$',
    #         'simple-emoji': '^([a-z0-9-]|' + emoji_pattern + ')+$',
    #         'simple_letter-emoji': '^([a-z]|' + emoji_pattern + ')+$',
    #     }
    #     compiled = {name: regex.compile(pattern) for name, pattern in patterns.items()}
    #     return compiled

    def length(self, label) -> int:
        """Returns number of Unicode chars in the string."""
        return len(label)
    
    def grapheme_length(self, label) -> int:
        """Returns number of graphemes in the string."""
        return len(myunicode.grapheme.split(label))

    def emoji_count(self, label) -> int:
        """Returns number of emojis in the string."""
        from emoji.core import emoji_count
        return emoji_count(label)

    def simple_letter(self, label) -> bool:
        """Checks if whole string matches regular expression of lowercase Latin letters."""
        return self.compiled_regexp_patterns['simple_letter'].match(label) is not None

    # def simple_letter_emoji(self, label) -> bool:  # TODO: slow
    #     """Checks if whole string matches regular expression of lowercase Latin letters."""
    #     return self.emoji_regexp['simple_letter-emoji'].match(label) is not None

    def numeric(self, label) -> bool:
        """Checks if whole string matches regular expression of Latin digits."""
        return self.compiled_regexp_patterns['numeric'].match(label) is not None

    def latin_alpha_numeric(self, label) -> bool:
        """Checks if whole string matches regular expression of Latin lowercase letters or digits."""
        return self.compiled_regexp_patterns['latin-alpha-numeric'].match(label) is not None

    def simple(self, label) -> bool:
        """Checks if whole string matches regular expression of Latin lowercase letters or digits or hyphen."""
        return self.compiled_regexp_patterns['simple'].match(label) is not None

    # def is_emoji(self, label) -> bool:
    #     """Checks if whole string matches regular expression of emojis."""
    #     return self.emoji_regexp['is_emoji'].match(label) is not None

    # def simple_emoji(self, label) -> bool:
    #     """Checks if whole string matches regular expression of Latin lowercase letters or digits or hyphen or
    #     emojis. """
    #     return self.emoji_regexp['simple-emoji'].match(label) is not None

    def is_letter(self, label) -> bool:
        """Checks if string matches regular expression of lowercase letters."""
        return self.compiled_regexp_patterns['is_letter'].match(label) is not None

    def simple_number(self, label) -> bool:
        """Checks if string matches regular expression of lowercase letters."""
        return self.compiled_regexp_patterns['numeric'].match(label) is not None

    def is_number(self, label) -> bool:
        return self.compiled_regexp_patterns['is_number'].match(label) is not None

    def is_namehash(self, label) -> bool:
        return self.compiled_regexp_patterns['is_namehash'].match(label) is not None

    def script_name(self, label) -> Union[str, None]:
        """Returns name of script (writing system) of the string, None if different scripts are used in the string."""
        return myunicode.script_of(label)

    def is_hyphen(self, label) -> bool:
        """Detects hyphen"""
        return '-' == label

    def is_dollarsign(self, label) -> bool:
        """Detects dollar sign"""
        return '$' == label

    def is_underscore(self, label) -> bool:
        """Detects underscore"""
        return '_' == label

    def zwj(self, label) -> bool:
        """Detects zero width joiner"""
        return '\u200d' == label  # '‍'

    def zwnj(self, label) -> bool:
        """Detects zero width non-joiner"""
        return '\u200c' == label  # '‌'

    def invisible(self, label) -> bool:
        """Detects zero width joiner or non-joiner or fe0f or fe0e"""
        return label in ('\u200d', '\u200c', '\ufe0f', '\ufe0e')  # ('‍', '‌', )

    def ens_tokens(self, label) -> List[Dict]:
        """Performs ENSIP tokenization."""
        return ens_tokenize(label)

    def is_normalized(self, label) -> bool:
        """Checks if string is normalized according to ENSIP."""
        return is_ens_normalized(label)

    def normalized_label(self, label) -> Optional[str]:
        """
        Returns the ENSIP normalized label or None if:
        - label is disallowed
        - label is already normalized
        """
        try:
            norm = ens_normalize(label)
            return norm if norm != label else None
        except DisallowedSequence:
            return None

    def beautiful_label(self, label) -> Optional[str]:
        """
        Returns the ENSIP normalized and beautified label or None if:
        - label is disallowed
        - label is already beautified
        """
        try:
            beautiful = ens_beautify(label)
            return beautiful if beautiful != label else None
        except DisallowedSequence:
            return None

    def unicodedata_name(self, label) -> Union[str, None]:
        """Returns the name assigned to the character."""
        try:
            return myunicode.name(label)
        except ValueError:
            return None

    def unicodedata_category(self, label) -> str:
        """Returns the general category assigned to the character: http://www.unicode.org/reports/tr44/#GC_Values_Table"""
        return myunicode.category(label)

    def unicodedata_bidirectional(self, label) -> str:
        """Returns the bidirectional class assigned to the character or empty string."""
        return unicodedata.bidirectional(label)

    def unicodedata_combining(self, label) -> int:
        """Returns the canonical combining class assigned to the character. Returns 0 if no combining class is defined.."""
        return myunicode.combining(label)

    def unicodedata_mirrored(self, label) -> int:
        """Returns the mirrored property assigned to the character"""
        return unicodedata.mirrored(label)

    def unicodedata_decomposition(self, label) -> str:
        """Returns the character decomposition mapping assigned to the character"""
        return unicodedata.decomposition(label)

    def unicodeblock(self, label) -> Union[str, None]:
        """Return a name of Unicode block in which the character is or None"""
        return myunicode.block_of(label)

    def is_confusable(self, label, simple=False) -> bool:
        """Indicates if a character is confusable."""
        return self.simple_confusables.is_confusable(label) if simple else self.full_confusables.is_confusable(label)

    def get_confusables(self, label, simple=False) -> Iterable[str]:
        """Return set of confusable characters."""
        return self.simple_confusables.get_confusables(label) if simple else self.full_confusables.get_confusables(label)

    def get_canonical(self, label, simple=False):
        """Returns canonical character from confusable set."""
        return self.simple_confusables.get_canonical(label) if simple else self.full_confusables.get_canonical(label)

    def is_ascii(self, label) -> bool:
        """Detects if label is all ASCII."""
        try:
            label.encode('ascii')
            return True
        except UnicodeEncodeError:
            return False

    def codepoint(self, label) -> str:
        """Codepoint of Unicode char as hex with 0x prefix."""
        return f'{ord(label):x}'

    def codepoint_int(self, label) -> int:
        """Codepoint of Unicode char as integer."""
        return ord(label)

    def codepoint_hex(self, label) -> str:
        """Codepoint of Unicode char as hex."""
        return hex(ord(label))

    def char_link(self, label) -> str:
        """Link to external page with Unicode character information."""
        return f'https://unicodeplus.com/U+{ord(label):04X}'

    def multi_char_link(self, grapheme) -> str:
        """Link to external page with Unicode grapheme information."""
        encoded = grapheme.encode('utf-8')
        return f'https://unicode.link/inspect/utf8:{".".join(f"{b:02x}" for b in encoded)}'

    def emoji_link(self, label) -> str:
        """Link to external page with emoji information."""
        return f'http://📙.la/{label}'

    def name(self, label) -> str:
        return label

    def bytes(self, label) -> int:
        """Number of bytes in UTF8 encoding."""
        return len(label.encode('utf-8'))

    def NFKD_ascii(self, label) -> str:
        """Returns string after decomposition in compatible mode with removed non-ascii chars."""
        return unicodedata.normalize('NFKD', label).encode('ascii', 'ignore').decode('utf-8')

    def NFD_ascii(self, label) -> str:
        """Returns string after decomposition with removed non-ascii chars."""
        return unicodedata.normalize('NFD', label).encode('ascii', 'ignore').decode('utf-8')

    def NFKD(self, label) -> str:
        """Returns string after decomposition in compatible mode."""
        return unicodedata.normalize('NFKD', label)

    def NFD(self, label) -> str:
        """Returns string after decomposition."""
        return unicodedata.normalize('NFD', label)

    # def classes(self, label) -> List[str]:
    #     """Return classes of string: letter,number,hyphen,emoji,simple,invisible"""
    #     result = []
    #     for c, func in self.classes_config.items():
    #         if func(label):
    #             result.append(c)
    #     return result

    # def token_classes(self, label) -> List[str]:
    #     """Return classes of string: letter,number,hyphen,emoji,simple,invisible"""
    #     result = []
    #     for c, func in self.token_classes_config.items():
    #         if func(label):
    #             result.append(c)
    #     return result

    def type(self, label) -> str:
        """Return classes of char: simple_letter,simple_number,other_letter,other_number,hyphen,emoji,invisible,special"""
        for c, func in self.types_config.items():
            if func(label):
                return c
        return 'special'

    def uts46_remap(self, name) -> Union[str, None]:
        try:
            uts46_remap = idna.uts46_remap(name, std3_rules=True, transitional=False)
        except idna.core.InvalidCodepoint:
            uts46_remap = None
        return uts46_remap

    def idna_encode(self, name) -> Union[str, None]:
        try:
            encode = idna.encode(name, uts46=True, std3_rules=True, transitional=False)
        except idna.core.InvalidCodepoint:
            encode = None
        except idna.core.IDNAError as e:
            encode = None
        return encode
