import json
from typing import Dict, List, Tuple, Optional

import regex
from omegaconf import DictConfig

from label_inspector.common import myunicode
from label_inspector.data import get_resource_path
from label_inspector.common.pickle_cache import pickled_property

from ens_normalize import is_ens_normalized


def is_simple_confusable(conf: str) -> bool:
    return is_ens_normalized(conf) and len(myunicode.grapheme.split(conf)) == 1


class Confusables:
    """Stores confusable characters and graphemes."""

    def __init__(self, config: DictConfig):
        self.config = config
        if not config.inspector.lazy_loading:
            self.confusable_graphemes

    @pickled_property('inspector.confusables', 'inspector.grapheme_confusables')
    def _full_confusable_graphemes(self) -> Dict[str, Tuple[str, List[str]]]:
        with open(get_resource_path(self.config.inspector.confusables), 'r', encoding='utf-8') as f:
            old_confusables = json.load(f)

        with open(get_resource_path(self.config.inspector.grapheme_confusables), 'r', encoding='utf-8') as f:
            new_confusables = json.load(f)

        return old_confusables | new_confusables

    @pickled_property('inspector.confusables', 'inspector.grapheme_confusables')
    def _simple_confusable_graphemes(self) -> Dict[str, Tuple[str, List[str]]]:
        all_confusables = self._full_confusable_graphemes
        return {g: (canon if canon is not None and is_simple_confusable(canon) else None,
                    list(filter(is_simple_confusable, confs)))
                    for g, (canon, confs) in all_confusables.items()}

    @property
    def confusable_graphemes(self) -> Dict[str, Tuple[str, List[str]]]:
        return self._full_confusable_graphemes

    def is_confusable_grapheme_with_combining_marks(self, grapheme: str) -> bool:
        return len(grapheme) > 1 \
               and not myunicode.combining(grapheme[0]) \
               and all(myunicode.combining(char) for char in grapheme[1:])

    def is_confusable_grapheme_in_dictionary(self, grapheme: str) -> bool:
        return grapheme in self.confusable_graphemes

    def is_confusable_grapheme(self, grapheme: str) -> bool:
        if regex.fullmatch(r'[a-z0-9_$-]+', grapheme):
            return False

        return self.is_confusable_grapheme_in_dictionary(grapheme) \
               or self.is_confusable_grapheme_with_combining_marks(grapheme)

    def get_confusables_grapheme(self, grapheme: str) -> List[str]:
        if self.is_confusable_grapheme_with_combining_marks(grapheme):
            # if grapheme is a confusable with combining marks,
            # then we simply return the confusables for the first character
            if self.is_confusable_grapheme_in_dictionary(grapheme[0]):
                return self.confusable_graphemes[grapheme[0]][1]

        if self.is_confusable_grapheme_in_dictionary(grapheme):
            return self.confusable_graphemes[grapheme][1]

        return []

    def get_canonical_grapheme(self, grapheme: str) -> Optional[str]:
        # if the grapheme has combining marks, we simply return the first char as canonical
        if self.is_confusable_grapheme_with_combining_marks(grapheme):
            return grapheme[0]

        if self.is_confusable_grapheme_in_dictionary(grapheme):
            return self.confusable_graphemes[grapheme][0]

        return None

    def is_confusable(self, string: str) -> bool:
        return self.is_confusable_grapheme(string) or (len(string) > 1 and self.is_confusable(string[0]))

    def get_confusables(self, string: str) -> List[str]:
        confusables = self.get_confusables_grapheme(string)
        return confusables if confusables or len(string) == 1 else self.get_confusables(string[0])

    def get_canonical(self, string: str) -> Optional[str]:
        canonical = self.get_canonical_grapheme(string)
        return canonical if canonical or len(string) == 1 else self.get_canonical(string[0])


class SimpleConfusables(Confusables):
    @property
    def confusable_graphemes(self) -> Dict[str, Tuple[str, List[str]]]:
        return self._simple_confusable_graphemes
