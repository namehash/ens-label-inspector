from typing import Optional, List, Union

from label_inspector.common import myunicode

from .analysis_framework import analysis_object, field
from .grapheme_analysis import GraphemeAnalysis
from .confusable_grapheme_analysis import ConfusableGraphemeAnalysis
from .confusable_multi_grapheme_analysis import ConfusableMultiGraphemeAnalysis


ConfusableAnalysis = Union[ConfusableGraphemeAnalysis, ConfusableMultiGraphemeAnalysis]


def make_conf_analysis(confusable: str, parent) -> ConfusableAnalysis:
    graphemes = myunicode.grapheme.split(confusable)
    if len(graphemes) == 1:
        return ConfusableGraphemeAnalysis(confusable, parent)
    else:
        return ConfusableMultiGraphemeAnalysis(confusable, parent)


@analysis_object
class GraphemeWithConfusablesAnalysis(GraphemeAnalysis):
    '''
    Grapheme analysis with added confusables.
    '''

    def __init__(self, grapheme: str, parent):
        super().__init__(grapheme, parent)

    @field
    def _is_confusable(self) -> bool:
        """
        Is the grapheme confusable?
        Uses the first character.
        """
        return self.root.i.f.is_confusable(self.grapheme, simple=self.root.config.simple_confusables)

    @field
    def _confusables_other_untruncated(self) -> List[ConfusableAnalysis]:
        """
        Untruncated confusables for the grapheme.
        Uses the first character.
        """
        # optimize for non-confusable characters
        return [] if not self._is_confusable \
            else [make_conf_analysis(conf_text, self)
                  for conf_text
                  in self.root.i.f.get_confusables(self.grapheme, simple=self.root.config.simple_confusables)]

    @field
    def confusables_other(self) -> List[ConfusableAnalysis]:
        """
        Truncated confusables for the grapheme.
        Uses the first character.
        """
        return self._confusables_other_untruncated[:self.root.config.truncate_confusables]

    @field
    def confusables_canonical(self) -> Optional[ConfusableAnalysis]:
        """
        Canonical form of the confusable grapheme or None if not found.
        Uses the first character.
        """
        # optimize for non-confusable characters
        if not self._is_confusable:
            return None

        canonical = self.root.i.f.get_canonical(self.grapheme, simple=self.root.config.simple_confusables)
        if canonical is None:
            return None
        return make_conf_analysis(canonical, self)
