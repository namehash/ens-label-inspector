import pytest
from label_inspector.common.punycode import puny_analysis, puny_encoded


@pytest.mark.parametrize(
    "name, expected",
    [
        ("", ""),
        (".", "."),
        ("a", "a"),
        ("a.", "a."),
        ("a.b", "a.b"),
        (".a.b", ".a.b"),
        ("xn--😵💫😵💫😵💫", "xn--xn---8v63caa362abab"),
        ("🇺🇸", "xn--w77hd"),
        ("💩", "xn--ls8h"),
        ("💩︎", "xn--u86cy764b"),
        ("💩️", "xn--v86cw764b"),
        ("\ud83d\udca9", "xn--8c9by4f"),
        ("👩🏽‍⚕️", "xn--1ug39wgn9reu4hopa"),
        ("👩🏽⚕", "xn--t7h5689nija"),
        ("🚴‍♂️", "xn--1ug66vku9rt36h"),
        ("🚴♂", "xn--g5h7790o"),
        ("👩‍❤️‍💋‍👨", "xn--1ugaa826ezk4zh52kba0z"),
        ("😵‍💫😵‍💫😵‍💫", "xn--1ugaa67909bbab66ycac"),
        ("-", "-"),
        (".-.", ".-."),
        ("-.-", "-.-"),
    ],
)
def test_puny_encoded(name, expected):
    assert puny_analysis(name).encoded == expected
    assert puny_encoded(name) == expected


def test_puny_compatibility():
    assert puny_analysis("ąą").compatibility.name == "COMPATIBLE"
    assert puny_analysis("x" * 64).compatibility.name == "LABEL_TOO_LONG"
    assert (
        puny_analysis(".".join("x" * 63 for _ in range(4))).compatibility.name
        == "NAME_TOO_LONG"
    )
    assert puny_analysis("xn--abc").compatibility.name == "PUNYCODE_LITERAL"
    assert puny_analysis("ab--abc").compatibility.name == "INVALID_LABEL_EXTENSION"
    # TODO: UNSUPPORTED_ASCII


@pytest.mark.parametrize(
    "name, expected",
    [
        ("example.com", True),
        ("rfc-1123.org", True),
        ("xn--rfc-1123.org", True),
        ("-invalid-start.com", False),
        ("invalid-end-.org", False),
        ("example..com", True),  # TODO: does this actually meet RFC1123?
        ("a_label_with_underscores.com", False),
        ("xn--😵💫😵💫😵💫", False),
    ],
)
def test_dns_support(name, expected):
    assert puny_analysis(name).dns_support == expected


def test_punycode_error_prio():
    # not NAME_TOO_LONG
    assert puny_analysis("x" * 1024).compatibility.name == "LABEL_TOO_LONG"
