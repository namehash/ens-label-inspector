from typing import Optional, List, Union
from pydantic import BaseModel, Field
from ens_normalize import DisallowedSequenceType, CurableSequenceType, NormalizableSequenceType


class BaseInspectorLabel(BaseModel):
    truncate_confusables: Optional[int] = Field(
        default=None, ge=0,
        title='truncate `confusables_other` fields output (`confusables_canonical` field is not affected); the goal is to reduce output size',
        description="* if `null` (default value) then no truncation is applied (there is no limit)\n"
                    "* if `0` then `confusables_other` field is an empty list, but `confusable_count` field is calculated before truncation\n"
                    "* if other number then maximum length of `confusables_other` is that number (`confusables_canonical` field is not counted), "
                    "e.g. by setting it to `2`, the canonical will be returned in `confusables_canonical` field and 2 elements in `confusables_other` list")
    truncate_graphemes: Optional[int] = Field(
        default=None, ge=0,
        title='truncate list of graphemes in output, but other fields (e.g. `grapheme_length`, `char_length`) are calculated before truncation; the goal is to reduce output size',
        description="* if `null` (default value) then no truncation is applied (there is no limit)\n"
                    "* if `0` then `graphemes` field is an empty list, but aggregation fields are calculated before truncation\n"
                    "* the truncation has been applied if length of `graphemes` is different than `grapheme_length`")
    truncate_chars: Optional[int] = Field(
        default=None, ge=0,
        title='truncate character list in each grapheme, but aggregated info is calculated before truncation; the goal is to reduce output size',
        description="* if `null` (default value) then no truncation is applied (there is no limit)\n"
                    "* if `0` then `chars` field in each element of `graphemes` list is an empty list, but aggregation fields are calculated before truncation"
                    "* the truncation has been applied if sum of lengths of `chars` in graphemes (count of chars in all graphemes) is different than `char_length`")


class InspectorLabel(BaseInspectorLabel):
    label: str = Field(title='input label')


class BatchInspectorLabel(BaseInspectorLabel):
    labels: List[str] = Field(title='batch input labels')


class InspectorCharResult(BaseModel):
    value: str = Field(title="character being inspected")
    script: str = Field(title="script name (writing system) of the character",
                        description="* is `Unknown` if script is not assigned for a character\n"
                                    "* special scripts are `Common` (e.g. punctuations, emojis) and `Inherited` (e.g. combining marks)")
    name: str = Field(title="name assigned to the character",
                      description="* for unknown characters it is `Unknown character in <script> script`")
    codepoint: str = Field(title="codepoint of the character as hex with 0x prefix")
    link: str = Field(title="link to external page with information about the character")
    type: str = \
        Field(title="type of the character",
              description=
              '* `simple_letter` - `[a-z]`\n'
              '* `simple_number` - `[0-9]`\n'
              '* `other_letter` - a letter in any script that is not simple; `LC` class http://www.unicode.org/reports/tr44/#GC_Values_Table \n'
              '* `other_number` - a digit in any script that is not simple; `N` class http://www.unicode.org/reports/tr44/#GC_Values_Table \n'  # TODO: check
              '* `hyphen` - a hyphen\n'
              '* `dollarsign` - a dollar sign\n'
              '* `underscore` - an underscore\n'
              '* `emoji` - a character inside correct emoji\n'
              '* `invisible` - zero width joiner or non-joiner (which is not part of correct emoji)\n'
              '* `special` - for any character that does not match one of the other classifications'
              )


class InspectorGraphemeResult(BaseModel):
    value: str = Field(title="the grapheme string")
    chars: List[InspectorCharResult] = Field(title="list of characters",
                                             description="may be shorter than `value` (grapheme string) if `truncate_chars` applies")
    name: str = Field(title="name of the grapheme",
                      description="* if emoji ZWJ sequence then its name\n"
                                  "* if single-character grapheme then character name\n"
                                  "* else `Combined Character` for other graphemes")
    codepoint: Optional[str] = Field(title="codepoint of the single-character grapheme as hex with 0x prefix",
                                     description="* `null` for multi-character graphemes")
    link: Optional[str] = Field(title="link to external page with information about the single-character grapheme",
                                description="* `null` for multi-character graphemes")
    script: str = Field(
        title="script name of the grapheme computed on all its characters",
        description="when the value of scripts names is any of the following:\n"
                    "* [X, Common, Inherited]\n"
                    "* [X, Inherited]\n"
                    "* [X, Common]\n\n"
                    "we should record the value of the script field as just X.\n"
                    "* For [Common, Inherited] `Common` is returned.\n"
                    "* Might be `Unknown` for new characters introduced in new Unicode\n"
                    "* is `Combined` if there are characters with different non-neutral scripts in the grapheme")

    type: str = \
        Field(
            title='type of the grapheme',
            description=
            'If all characters in the grapheme have the same type, that type is returned. Otherwise, `special` is returned.\n'
            '* `simple_letter` - `[a-z]`\n'
            '* `simple_number` - `[0-9]`\n'
            '* `other_letter` - a letter (single-char grapheme) in any script that is not simple; `LC` class http://www.unicode.org/reports/tr44/#GC_Values_Table \n'
            '* `other_number` - a digit (single-char grapheme) in any script that is not simple; `N` class http://www.unicode.org/reports/tr44/#GC_Values_Table \n'  # TODO: check
            '* `hyphen` - a hyphen\n'
            '* `dollarsign` - a dollar sign\n'
            '* `underscore` - an underscore\n'
            '* `emoji` - an emoji or emoji ZWJ sequence\n'
            '* `invisible` - zero width joiner or non-joiner\n'
            '* `special` - for any grapheme that doesn\'t match one of the other classifications or if characters have different types'
        )

    font_support_all_os: bool = Field(
        title="whether the grapheme is supported by the default sets of fonts on all operating systems",
    )


class InspectorConfusableGraphemeResult(InspectorGraphemeResult):
    pass


class InspectorConfusableMultiGraphemeResult(BaseModel):
    value: str = Field(title="the confusable string")
    chars: List[InspectorCharResult] = Field(title="list of characters in the confusable")


InspectorConfusableResult = Union[InspectorConfusableGraphemeResult, InspectorConfusableMultiGraphemeResult]


class InspectorGraphemeWithConfusablesResult(InspectorGraphemeResult):
    confusables_canonical: Optional[InspectorConfusableResult] = \
        Field(title="canonical form of confusable grapheme",
              description='* may be `null` if canonical form is not known/does not exist')
    confusables_other: List[InspectorConfusableResult] = \
        Field(title="list of confusable forms without canonical",
              description='* if the grapheme is not confusable then empty list is returned.')


class InspectorResultBase(BaseModel):
    label: str = Field(title="input string")
    status: str = Field(title="status of the input label",
                        description="* `normalized` - if the input label is normalized\n"
                                    "* `unnormalized` - if the input label is unnormalized")
    version: str = Field(default='0.2.0', title="version of the label inspector",
                         description="* version can be used for updating cache")


class InspectorResultNormalized(InspectorResultBase):
    char_length: int = Field(
        title="number of Unicode characters in the input label (sum of Unicode characters across all graphemes)")
    grapheme_length: int = Field(title="number of graphemes")
    all_type: Optional[str] = \
        Field(title="type of all graphemes if all graphemes have the same type, otherwise `null`")
    any_types: List[str] = Field(
        title='a list of all grapheme types (unique) that are present in the input label')
    all_script: Optional[str] = Field(
        title="script of all graphemes if all graphemes have the same script",
        description="If `any_scripts` contains `Unknown` or `Combined`:\n"
                    "* `all_script` is `null`\n"
                    "Else if `any_scripts` is `[Common, Inherited]`:\n"
                    "* `all_script` is `Common`\n"
                    "Else if `any_scripts` is any of the following:\n"
                    "* `[X]`\n"
                    "* `[X, Common, Inherited]`\n"
                    "* `[X, Inherited]`\n"
                    "* `[X, Common]`\n"
                    "then `all_script` is `X`.\n"
                    "Otherwise, the label has many scripts and `all_script` is `null`.")
    any_scripts: List[str] = Field(title="list of unique script names of all graphemes")
    confusable_count: int = Field(title='number of confusable graphemes')
    graphemes: List[InspectorGraphemeWithConfusablesResult]
    beautiful_label: str = Field(title='ENSIP beautified version of the input label')
    canonical_confusable_label: Optional[str] = Field(
        title='input label where all confusables are replaced with their canonicals and run through ENSIP normalization',
        description='is `null` if:\n'
                    '* input label is not confusable\n'
                    '* at least one confusable does not have a canonical\n'
                    '* result contains disallowed characters and cannot be normalized')
    beautiful_canonical_confusable_label: Optional[str] = Field(
        title='beautified version of `canonical_confusable_label`',
        description='is `null` if the `canonical_confusable_label` is null')
    dns_hostname_support: bool = Field(
        title='whether the input label is a valid DNS hostname according to RFC 1123',
        description='note: this label-level check does not enforce the full name limit of 253 characters, which can be checked externally'
    )
    punycode_compatibility: str = Field(
        title='whether the input label is compatible with Punycode (RFC 3492)',
        description='Possible values:\n'
                    '* `COMPATIBLE` - the label can be encoded in Punycode\n'
                    '* `UNSUPPORTED_ASCII` - the Punycode encoded label contains disallowed characters\n'
                    '* `PUNYCODE_LITERAL` - the input label is already Punycode encoded\n'
                    '* `INVALID_LABEL_EXTENSION` - the input label contains disallowed hyphens\n'
                    '* `LABEL_TOO_LONG` - the Punycode encoded label exceeds 63 characters\n'
                    'note: this label-level check does not enforce the full name limit of 253 characters, which can be checked externally'
    )
    punycode_encoding: Optional[str] = Field(
        title='Punycode (RFC 3492) encoded version of the input label',
        description='is `null` if the input label is not compatible with Punycode (see `punycode_compatibility`)'
    )
    font_support_all_os: bool = Field(
        title="whether all graphemes in the label are supported by the default sets of fonts on all operating systems",
    )


class InspectorResultUnnormalized(InspectorResultBase):
    cured_label: Optional[str] = Field(
        title='input label where all disallowed characters are removed',
        description='is `null` if the label cannot be cured')
    canonical_confusable_label: Optional[str] = Field(
        title='properly ENSIP normalized version of the input label',
        description='is `null` if the input label cannot be normalized (e.g. contains disallowed characters)')
    beautiful_canonical_confusable_label: Optional[str] = Field(
        title='beautified version of `canonical_confusable_label`',
        description='is `null` if the `canonical_confusable_label` is null')
    normalization_error_message: str = Field(title='reason why the input label is not normalized')
    normalization_error_details: Optional[str] = Field(title='details of the normalization error')
    normalization_error_code: str = Field(
        title='error code of the normalization error',
        description=(
            '\n'.join(f'* `{e.code}` - {e.general_info}'
                      for e in DisallowedSequenceType) + '\n' +
            '\n'.join(f'* `{e.code}` - {e.general_info}'
                      for e in CurableSequenceType) + '\n' +
            '\n'.join(f'* `{e.code}` - {e.general_info}'
                      for e in NormalizableSequenceType)
        )
    )
    disallowed_sequence_start: Optional[int] = Field(
        title='0-based index of the first disallowed character in the label',
        description='* for some errors the disallowed sequence cannot be reported and this field becomes `null`, see `normalization_error_code`')
    disallowed_sequence: Optional[List[InspectorCharResult]] = Field(
        title='a part of the label that is not normalized',
        description='* for some errors the disallowed sequence cannot be reported and this field becomes `null`, see `normalization_error_code`')
    suggested_replacement: Optional[List[InspectorCharResult]] = Field(
        title='a suggested replacement for the disallowed sequence',
        description='* an empty list means that the disallowed sequence should be removed completely\n'
                    '* for some errors the disallowed sequence cannot be reported and this field becomes `null`, see `normalization_error_code`')


InspectorResult = Union[InspectorResultNormalized, InspectorResultUnnormalized]
