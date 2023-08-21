from typing import NamedTuple, Optional
from enum import Enum, auto
import string


class PunycodeCompatibility(Enum):
    COMPATIBLE = auto()
    UNSUPPORTED_ASCII = auto()
    PUNYCODE_LITERAL = auto()
    INVALID_LABEL_EXTENSION = auto()
    LABEL_TOO_LONG = auto()
    NAME_TOO_LONG = auto()


class PunycodeAnalysisResult(NamedTuple):
    dns_support: bool
    compatibility: PunycodeCompatibility
    encoded: Optional[str]


HYPHEN = ord('-')
MAX_LABEL = 63
MAX_NAME = 253
CHARS_LOWER_DIGITS_HYPHEN = frozenset(string.ascii_lowercase + string.digits + '-')
CHARS_LOWER_DIGITS_HYPHEN_DOT = frozenset(string.ascii_lowercase + string.digits + '-' + '.')


def puny_encoded_label(label: str) -> str:
    '''
    Encode a single label according to RFC 3492.
    '''
    if not label:
        return label
    encoded = label.encode('punycode')
    if encoded[-1] != HYPHEN:
        label = 'xn--' + encoded.decode('ascii')
    return label


def puny_encoded(name: str) -> str:
    '''
    Encode text according to RFC 3492.
    '''
    return '.'.join(puny_encoded_label(label) for label in name.split('.'))


def puny_analysis(name: str) -> PunycodeAnalysisResult:
    compat = PunycodeCompatibility.COMPATIBLE
    encoded = []
    for label in name.split('.'):
        encoded_label = puny_encoded_label(label).lower()
        if not all(c in CHARS_LOWER_DIGITS_HYPHEN for c in encoded_label):
            compat = PunycodeCompatibility.UNSUPPORTED_ASCII
            break
        if encoded_label == label:
            if label.startswith('xn--'):
                compat = PunycodeCompatibility.PUNYCODE_LITERAL
                break
            if label[2:4] == '--':
                compat = PunycodeCompatibility.INVALID_LABEL_EXTENSION
                break
        if len(encoded_label) > MAX_LABEL:
            compat = PunycodeCompatibility.LABEL_TOO_LONG
            break
        encoded.append(encoded_label)
    encoded_name = '.'.join(encoded)
    # make sure we do not override label-level errors
    if len(encoded_name) > MAX_NAME and compat is PunycodeCompatibility.COMPATIBLE:
        compat = PunycodeCompatibility.NAME_TOO_LONG
    return PunycodeAnalysisResult(
        dns_support=is_rfc1123(name),
        compatibility=compat,
        encoded=encoded_name
                if compat is PunycodeCompatibility.COMPATIBLE
                else None,
    )


'''
From https://adraffy.github.io/punycode.js/test/demo.html
function is_RFC1123(name) {
	let max = 253;
	if (name.length > max+1) return false; 
	if (!/^[a-zA-z0-9-.]+$/) return false;
	if (name.endsWith('.')) name = name.slice(0, -1);
	if (name.length > max) return false;
	return name.split('.').every(s => !s.startsWith('-') && !s.endsWith('-') && s.length < 64);
}
'''
def is_rfc1123(name: str) -> bool:
    if len(name) > MAX_NAME + 1:
        return False
    if not all(c in CHARS_LOWER_DIGITS_HYPHEN_DOT for c in name.lower()):
        return False
    if name.endswith('.'):
        name = name[:-1]
    if len(name) > MAX_NAME:
        return False
    return all(
        not label.startswith('-') and
        not label.endswith('-') and
        len(label) <= MAX_LABEL
        for label in name.split('.')
    )
