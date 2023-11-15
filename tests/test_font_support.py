from label_inspector.config import initialize_inspector_config
from label_inspector.components.font_support import aggregate_font_support
from label_inspector.components.font_support import FontSupport


def test_agg():
    assert aggregate_font_support([True, True, True]) is True
    assert aggregate_font_support([True, True, False]) is False
    assert aggregate_font_support([True, True, None]) is None
    assert aggregate_font_support([True, False, None]) is False
    assert aggregate_font_support([False, False, None]) is False


def test_fe0f():
    with initialize_inspector_config("prod_config") as config:
        fs = FontSupport(config)
        assert fs.check_support("🤹‍♀") is True
        assert fs.check_support("🤹‍♀️") is True
        assert fs.check_support("\uFE0F") is True
