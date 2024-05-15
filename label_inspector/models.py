from typing import Optional, List, Union
from pydantic import BaseModel, Field
from ens_normalize import DisallowedSequenceType, CurableSequenceType, NormalizableSequenceType


class InspectorRequestBase(BaseModel):
    truncate_confusables: Optional[int] = Field(
        default=None,
        ge=0,
        description="Truncate `confusables_other` fields output. `confusables_canonical` field is not affected.\n"
                    "* if `null` (default value) then no truncation is applied\n"
                    "* if `0` then `confusables_other` field is an empty list, but `confusable_count` field is calculated before truncation\n"
                    "* if other number then maximum length of `confusables_other` is that number (`confusables_canonical` field is not counted), "
                    "e.g. by setting it to `2`, the canonical will be returned in `confusables_canonical` field and 2 elements in `confusables_other` list")
    truncate_graphemes: Optional[int] = Field(
        default=None,
        ge=0,
        description="Truncate list of graphemes in output. Other fields (e.g. `grapheme_length`, `char_length`) are calculated before truncation.\n"
                    "* if `null` (default value) then no truncation is applied\n"
                    "* if `0` then `graphemes` field is an empty list, but aggregation fields are calculated before truncation\n"
                    "* the truncation has been applied if length of `graphemes` is different than `grapheme_length`")
    truncate_chars: Optional[int] = Field(
        default=None,
        ge=0,
        description="Truncate character list in each grapheme. Aggregated info is calculated before truncation.\n"
                    "* if `null` (default value) then no truncation is applied\n"
                    "* if `0` then `chars` field in each element of `graphemes` list is an empty list\n"
                    "* the truncation has been applied if sum of lengths of `chars` in graphemes (count of chars in all graphemes) is different than `char_length`")
    simple_confusables: bool = Field(
        default=False,
        description="Limit `confusables_other` and `confusables_canonical` fields output to confusables that are single-grapheme and ENSIP-15 normalized.\n"
                    "* this option affects the earliest stage of confusable generation and impacts all confusable-related fields"
    )


class InspectorSingleRequest(InspectorRequestBase):
    label: str = Field(description='Input label.')


class InspectorBatchRequest(InspectorRequestBase):
    labels: List[str] = Field(description='Batch of input labels.')


class InspectorCharResult(BaseModel):
    value: str = Field(description="Character being inspected.")
    script: str = Field(description="Script name (writing system) of the character.\n"
                                    "* is `Unknown` if script is not assigned for a character\n"
                                    "* special scripts are `Common` (e.g. punctuations, emojis) and `Inherited` (e.g. combining marks)")
    name: str = Field(description="Name assigned to the character.\n"
                                  "* for unknown characters it is `Unknown character in <script> script`")
    codepoint: str = Field(description="Codepoint of the character as hex integer with 0x prefix.")
    link: str = Field(description="Link to an external page with information about the character.")
    type: str = \
        Field(description="Type of the character.\n"
            '* `simple_letter` - `[a-z]`\n'
            '* `simple_number` - `[0-9]`\n'
            '* `other_letter` - a letter in any script that is not simple; `LC` class http://www.unicode.org/reports/tr44/#GC_Values_Table \n'
            '* `other_number` - a digit in any script that is not simple; `N` class http://www.unicode.org/reports/tr44/#GC_Values_Table \n'
            '* `hyphen` - a hyphen\n'
            '* `dollarsign` - a dollar sign\n'
            '* `underscore` - an underscore\n'
            '* `emoji` - a character inside correct emoji\n'
            '* `invisible` - zero width joiner or non-joiner (which is not part of correct emoji)\n'
            '* `special` - for any character that does not match one of the other classifications'
        )
    unicode_version: Optional[str] = Field(description="Unicode Version of the character.\n"
                                                        "* `null` if the character is not assigned to any version")


class InspectorGraphemeResult(BaseModel):
    value: str = Field(description="The grapheme string.")
    chars: List[InspectorCharResult] = Field(description="List of characters. May be shorter than `value` (grapheme string) if `truncate_chars` applies")
    name: str = Field(description="Name of the grapheme.\n"
                                  "* is `Combined Character` for multi-character graphemes without a unique name")
    codepoint: Optional[str] = Field(description="Codepoint of the single-character grapheme as hex with 0x prefix.\n"
                                                 "* `null` for multi-character graphemes")
    link: Optional[str] = Field(description="Link to an external page with information about the single-character grapheme.\n"
                                            "* `null` for multi-character graphemes")
    script: str = Field(description="Script name of the grapheme computed from the script names of its characters.")

    type: str = \
        Field(
            description='Type of the grapheme. If all characters in the grapheme have the same type, that type is returned. Otherwise, `special` is returned.\n'
            '* `simple_letter` - `[a-z]`\n'
            '* `simple_number` - `[0-9]`\n'
            '* `other_letter` - a letter (single-char grapheme) in any script that is not simple; `LC` class http://www.unicode.org/reports/tr44/#GC_Values_Table \n'
            '* `other_number` - a digit (single-char grapheme) in any script that is not simple; `N` class http://www.unicode.org/reports/tr44/#GC_Values_Table \n'
            '* `hyphen` - a hyphen\n'
            '* `dollarsign` - a dollar sign\n'
            '* `underscore` - an underscore\n'
            '* `emoji` - an emoji or emoji ZWJ sequence\n'
            '* `invisible` - zero width joiner or non-joiner\n'
            '* `special` - for any grapheme that doesn\'t match one of the other classifications or if characters have different types'
        )

    font_support_all_os: Optional[bool] = Field(
        description="Whether the grapheme is supported by the default sets of fonts on common operating systems.\n"
                    "* `true` - the grapheme is known to be supported\n"
                    "* `false` - the grapheme is known not to be supported\n"
                    "* `null` - it is unknown whether the grapheme is supported or not"
    )

    description: str = Field(description="Description of the grapheme type.")

    unicode_version: Optional[str] = Field(description="Unicode Version of the grapheme.\n"
                                                       "* `null` if the grapheme is not assigned to any version")


class InspectorConfusableGraphemeResult(InspectorGraphemeResult):
    pass


class InspectorConfusableMultiGraphemeResult(BaseModel):
    value: str = Field(description="The confusable string.")
    chars: List[InspectorCharResult] = Field(description="List of characters in the confusable.")


InspectorConfusableResult = Union[InspectorConfusableGraphemeResult, InspectorConfusableMultiGraphemeResult]


class InspectorGraphemeWithConfusablesResult(InspectorGraphemeResult):
    confusables_canonical: Optional[InspectorConfusableResult] = \
        Field(description="Canonical form of confusable grapheme.\n"
                          "* may be `null` if canonical form is not known/does not exist\n"
                          "* may be null when `simple_confusables` is enabled and the canonical is not single-grapheme or not normalized")
    confusables_other: List[InspectorConfusableResult] = \
        Field(description="List of confusable forms without the canonical.\n"
                          "* if the grapheme is not confusable then empty list is returned\n"
                          "* if `simple_confusables` is enabled then only single-grapheme normalized confusables are returned")


class InspectorResultBase(BaseModel):
    label: str = Field(description="Input label.")

    status: str = Field(description="Status of the input label.\n"
                                    "* `normalized` - if the input label is normalized\n"
                                    "* `unnormalized` - if the input label is unnormalized")

    version: str = Field(default='0.2.0', description="Version of the label inspector.")

    char_length: int = Field(
        description="Number of Unicode UTF-32 codepoints in the input label. Might be larger than the number of graphemes.")

    grapheme_length: int = Field(description="Number of graphemes in the input label.")

    all_type: Optional[str] = Field(description="Type of all graphemes if all graphemes have the same type, otherwise `null`.")

    any_types: List[str] = Field(description="List of all unique grapheme types that are present in the input label.")

    all_script: Optional[str] = Field(
        description="Script of all graphemes if all graphemes have the same script.\n"
                    "If `any_scripts` contains `Unknown` or `Combined`:\n"
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

    any_scripts: List[str] = Field(description="List of unique script names of all graphemes.")

    confusable_count: int = Field(description='Number of graphemes that are confusable.')

    graphemes: List[InspectorGraphemeWithConfusablesResult] = Field(
        description="List of graphemes in the input label. May be shorter than `grapheme_length` if `truncate_graphemes` is enabled.")

    canonical_label: Optional[str] = Field(
        description='Input label where all confusables are replaced with their canonicals.\n'
                    'Is `null` if:\n'
                    '* at least one confusable does not have a canonical')

    normalized_canonical_label: Optional[str] = Field(
        description='Input label where all confusables are replaced with their canonicals and run through ENSIP-15 normalization.\n'
                    'Is `null` if:\n'
                    '* at least one confusable does not have a canonical\n'
                    '* result contains disallowed characters and cannot be normalized')

    beautiful_canonical_label: Optional[str] = Field(
        description='Beautified version of `canonical_confusable_label`. Is `null` if `canonical_confusable_label` is null.')

    dns_hostname_support: bool = Field(
        description='Whether the input label is a valid DNS hostname according to RFC 1123.\n'
                    'Note: this label-level check does not enforce the full name limit of 253 characters, which can be checked externally.'
    )

    punycode_compatibility: str = Field(
        description='Whether the input label is compatible with Punycode (RFC 3492).\n'
                    '* `COMPATIBLE` - the label can be encoded in Punycode\n'
                    '* `UNSUPPORTED_ASCII` - the Punycode encoded label contains disallowed characters\n'
                    '* `PUNYCODE_LITERAL` - the input label is already Punycode encoded\n'
                    '* `INVALID_LABEL_EXTENSION` - the input label contains disallowed hyphens\n'
                    '* `LABEL_TOO_LONG` - the Punycode encoded label exceeds 63 characters\n'
                    'Note: this label-level check does not enforce the full name limit of 253 characters, which can be checked externally'
    )

    punycode_encoding: Optional[str] = Field(
        description='Punycode (RFC 3492) encoded version of the input label.\n'
                    'Is `null` if the input label is not compatible with Punycode (see `punycode_compatibility`).'
    )

    font_support_all_os: Optional[bool] = Field(
        description="Whether all graphemes in the label are supported by the default sets of fonts on common operating systems.\n"
                    "* `true` - all graphemes are known to be supported\n"
                    "* `false` - at least one grapheme is known not to be supported\n"
                    "* `null` - at least one grapheme is unknown and zero graphemes are known not to be supported"
    )


class InspectorResultNormalized(InspectorResultBase):
    beautiful_label: str = Field(description="ENSIP-15 beautified version of the input label.")


class InspectorResultUnnormalized(InspectorResultBase):
    normalized_label: Optional[str] = Field(
        description='Input label run through ENSIP-15 normalization.\n'
                    'Is `null` if the input label contains disallowed characters and cannot be normalized.')

    cured_label: Optional[str] = Field(
        description='ENSIP-15 normalized input label where all disallowed characters are removed.\n'
                    'Is `null` if the label cannot be cured.')

    normalization_error_message: str = Field(description='Reason why the input label is not normalized.')

    normalization_error_details: Optional[str] = Field(description='Details of the normalization error.')

    normalization_error_code: str = Field(
        description='Error code of the normalization error.\n'
            '\n'.join(f'* `{e.code}` - {e.general_info}'
                      for e in DisallowedSequenceType) + '\n' +
            '\n'.join(f'* `{e.code}` - {e.general_info}'
                      for e in CurableSequenceType) + '\n' +
            '\n'.join(f'* `{e.code}` - {e.general_info}'
                      for e in NormalizableSequenceType)
    )

    disallowed_sequence_start: Optional[int] = Field(
        description='0-based index of the first disallowed character in the label.\n'
                    '* for some errors the disallowed sequence cannot be reported and this field becomes `null`, see `normalization_error_code`')

    disallowed_sequence: Optional[List[InspectorCharResult]] = Field(
        description='A part of the label that is not normalized.\n'
                    '* for some errors the disallowed sequence cannot be reported and this field becomes `null`, see `normalization_error_code`')

    suggested_replacement: Optional[List[InspectorCharResult]] = Field(
        description='A suggested replacement for the disallowed sequence.\n'
                    '* an empty list means that the disallowed sequence should be removed completely\n'
                    '* for some errors the disallowed sequence cannot be reported and this field becomes `null`, see `normalization_error_code`')


InspectorResult = Union[InspectorResultNormalized, InspectorResultUnnormalized]


class InspectorBatchResult(BaseModel):
    results: List[InspectorResult] = Field(description="List of results for each input label.")
