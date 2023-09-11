from label_inspector.components.font_support import aggregate_font_support


def test_agg():
    assert aggregate_font_support([True, True, True]) is True
    assert aggregate_font_support([True, True, False]) is False
    assert aggregate_font_support([True, True, None]) is None
    assert aggregate_font_support([True, False, None]) is False
    assert aggregate_font_support([False, False, None]) is False
