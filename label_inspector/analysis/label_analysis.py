from __future__ import annotations
from typing import List, Dict, Optional, Iterable, TYPE_CHECKING

from ens_normalize import ens_normalize, ens_beautify, ens_cure, ens_process, ENSProcessResult, DisallowedSequence, CurableSequence

from .analysis_framework import AnalysisBase, analysis_object, field, agg_all, agg_any
from .grapheme_analysis import GraphemeAnalysis
from .grapheme_with_confusables_analysis import GraphemeWithConfusablesAnalysis
from .char_analysis import CharAnalysis

from label_inspector.common.punycode import puny_analysis, PunycodeAnalysisResult
from label_inspector.common import myunicode
from label_inspector.components.font_support import aggregate_font_support

if TYPE_CHECKING:
    from label_inspector.inspector import Inspector


def count_words(tokenizeds: List[Dict]) -> int:
    count = [len(tokenized['tokens']) for tokenized in tokenizeds if '' not in tokenized['tokens']]
    if not count:
        return 0
    else:
        return min(count)


class LabelAnalysisConfig:
    def __init__(self,
                 label: str,
                 truncate_confusables: int = None,
                 truncate_graphemes: int = None,
                 truncate_chars: int = None,
                 simple_confusables: bool = False,
                 long_label: int = 30,
                 omit_cure: bool = False,
                 ):
        self.label = label
        self.truncate_confusables = truncate_confusables
        self.truncate_graphemes = truncate_graphemes
        self.truncate_chars = truncate_chars
        self.simple_confusables = simple_confusables
        self.long_label = long_label
        self.omit_cure = omit_cure


@analysis_object
class LabelAnalysis(AnalysisBase):
    def __init__(self, inspector: Inspector, config: LabelAnalysisConfig):
        self.root = self
        self.i = inspector
        self.config = config

    # / HELPERS

    def is_response_model_normalized(self) -> bool:
        return self.is_normalized

    def is_response_model_unnormalized(self) -> bool:
        return not self.is_normalized

    # no need for cached @field, because it just returns a generator
    @property
    def _chars_untruncated(self) -> Iterable[CharAnalysis]:
        """
        Untruncated char analysis.
        """
        return (char for grapheme in self._graphemes_untruncated
                     for char in grapheme._chars_untruncated)

    @field
    def _raw_graphemes(self) -> List[str]:
        """
        The label split into graphemes.
        """
        return myunicode.grapheme.split(self.config.label)

    @field
    def _punycode_analysis(self) -> PunycodeAnalysisResult:
        return puny_analysis(self.config.label)

    @field
    def _ens_process_result(self) -> ENSProcessResult:
        """
        Result of myunicode.ens_process.
        """
        return ens_process(
            self.config.label,
            do_normalize=True,
            do_beautify=True,
            do_normalizations=True,
        )

    @property
    def _ens_process_any_error(self):
        return self._ens_process_result.error or (self._ens_process_result.normalizations[0] if self._ens_process_result.normalizations else None)

    @property
    def _ens_error_is_curable(self):
        return isinstance(self._ens_process_any_error, CurableSequence)

    @property
    def is_normalized(self) -> bool:
        return self._ens_process_any_error is None

    # \ HELPERS

    # / COMMON

    @field
    def label(self) -> str:
        return self.config.label

    @field
    def status(self) -> str:
        if self.is_normalized:
            return 'normalized'
        else:
            return 'unnormalized'

    @field
    def char_length(self) -> Optional[int]:
        return len(self.config.label)

    @field
    def grapheme_length(self) -> Optional[int]:
        return len(self._raw_graphemes)

    @field
    def _graphemes_untruncated(self) -> List[GraphemeWithConfusablesAnalysis]:
        """
        Untruncated grapheme analysis.
        """
        return [GraphemeWithConfusablesAnalysis(g, self)
                for g in self._raw_graphemes]

    @field
    def graphemes(self) -> Optional[List[GraphemeWithConfusablesAnalysis]]:
        """
        Truncated grapheme analysis.
        """
        return self._graphemes_untruncated[:self.config.truncate_graphemes]

    # Aggregates (using untruncated grapheme analysis)

    @field
    def all_type(self) -> Optional[str]:
        return agg_all([g.type for g in self._graphemes_untruncated])

    @field
    def any_types(self) -> Optional[List[str]]:
        return agg_any([g.type for g in self._graphemes_untruncated])

    @field
    def all_script(self) -> Optional[str]:
        scripts = self.any_scripts
        had_inherited = False
        had_common = False
        strong_script = None
        for script in scripts:
            if script in ('Unknown', 'Combined'):
                # handles case 1
                return None
            elif script == 'Inherited':
                had_inherited = True
            elif script == 'Common':
                had_common = True
            elif strong_script is None:
                strong_script = script
            elif strong_script != script:
                # handles case 4
                return None
        # handles cases 2 and 3
        return strong_script or ('Common' if had_common else None) or ('Inherited' if had_inherited else None)

    @field
    def any_scripts(self) -> Optional[List[str]]:
        return agg_any([g.script for g in self._graphemes_untruncated])

    @field
    def confusable_count(self) -> int:
        return sum([1 for g in self._graphemes_untruncated if g._is_confusable])

    @field
    def dns_hostname_support(self) -> Optional[bool]:
        return self._punycode_analysis.dns_support

    @field
    def punycode_compatibility(self) -> Optional[str]:
        return self._punycode_analysis.compatibility.name

    @field
    def punycode_encoding(self) -> Optional[str]:
        return self._punycode_analysis.encoded

    @field
    def canonical_label(self) -> Optional[str]:
        canonicals = []
        for grapheme in self._graphemes_untruncated:
            if not grapheme._is_confusable:
                canonicals.append(grapheme.value)
            elif grapheme.confusables_canonical is None:
                return None
            else:
                canonicals.append(grapheme.confusables_canonical.value)
        return ''.join(canonicals)

    @field
    def normalized_canonical_label(self) -> Optional[str]:
        """
        Input label where all confusables are replaced
        with their canonicals and run through ENSIP normalization.
        Is `null` if:
        * input label is not confusable
        * at least one confusable does not have a canonical
        * result cannot be normalized
        """
        canonical_label = self.canonical_label
        if canonical_label is None:
            return None
        try:
            return ens_normalize(canonical_label)
        except DisallowedSequence:
            return None

    @field
    def beautiful_canonical_label(self) -> Optional[str]:
        """
        ENSIP beautified `canonical_confusable_label`.
        Is `null` if `canonical_confusable_label` is `null`.
        """
        canonical_label = self.canonical_label
        if canonical_label is None:
            return None
        try:
            return ens_beautify(canonical_label)
        except DisallowedSequence:
            return None

    @field
    def font_support_all_os(self) -> Optional[bool]:
        return aggregate_font_support([g.font_support_all_os for g in self._graphemes_untruncated])

    # \ COMMON

    # / NORMALIZED

    @field
    def beautiful_label(self) -> Optional[str]:
        """
        ENSIP beautified label.
        """
        if self.is_response_model_normalized():
            return self._ens_process_result.beautified

    # \ NORMALIZED

    # / UNNORMALIZED

    @field
    def normalized_label(self) -> Optional[str]:
        if self.is_response_model_unnormalized():
            return self._ens_process_result.normalized

    @field
    def cured_label(self) -> Optional[str]:
        if self.is_response_model_unnormalized() and not self.config.omit_cure:
            try:
                return ens_cure(self.label)
            except DisallowedSequence:
                return None

    @field
    def normalization_error_message(self) -> Optional[str]:
        if self.is_response_model_unnormalized():
            return self._ens_process_any_error.general_info

    @field
    def normalization_error_details(self) -> Optional[str]:
        if self.is_response_model_unnormalized() and self._ens_error_is_curable:
            return self._ens_process_any_error.sequence_info

    @field
    def normalization_error_code(self) -> Optional[str]:
        if self.is_response_model_unnormalized():
            return self._ens_process_any_error.code

    @field
    def disallowed_sequence_start(self) -> Optional[int]:
        if self.is_response_model_unnormalized() and self._ens_error_is_curable:
            return self._ens_process_any_error.index

    @field
    def disallowed_sequence(self) -> Optional[List[CharAnalysis]]:
        if self.is_response_model_unnormalized() and self._ens_error_is_curable:
            # need graphemes for char_class to work
            graphemes = myunicode.grapheme.split(self._ens_process_any_error.sequence)
            return [c for g in graphemes for c in GraphemeAnalysis(g, self)._chars_untruncated]

    @field
    def suggested_replacement(self) -> Optional[List[CharAnalysis]]:
        if self.is_response_model_unnormalized() and self._ens_error_is_curable:
            graphemes = myunicode.grapheme.split(self._ens_process_any_error.suggested)
            return [c for g in graphemes for c in GraphemeAnalysis(g, self)._chars_untruncated]

    # \ UNNORMALIZED
