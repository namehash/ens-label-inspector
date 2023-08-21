from __future__ import annotations
from typing import TYPE_CHECKING, List

from .analysis_framework import AnalysisBase, analysis_object, field
from .char_analysis import CharAnalysis


if TYPE_CHECKING:
    from .label_analysis import LabelAnalysis


@analysis_object
class ConfusableMultiGraphemeAnalysis(AnalysisBase):
    def __init__(self, confusable: str, parent):
        # not actually a single grapheme
        self.grapheme = confusable
        self.root: LabelAnalysis = parent.root

    @field
    def value(self) -> str:
        return self.grapheme

    @field
    def chars(self) -> List[CharAnalysis]:
        return [CharAnalysis(char, self)
                for char in self.grapheme]
