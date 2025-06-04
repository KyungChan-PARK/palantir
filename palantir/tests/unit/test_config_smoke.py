from palantir.core import config


def test_config_import():
    assert hasattr(config.Settings, "Config")
