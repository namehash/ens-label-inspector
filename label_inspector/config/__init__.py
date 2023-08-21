from typing import Literal
from contextlib import contextmanager
from hydra import initialize_config_module, compose


@contextmanager
def initialize_inspector_config(config_name: Literal["prod_config", "test_config"]):
    with initialize_config_module(version_base=None, config_module="label_inspector.config"):
        config = compose(config_name=config_name)
        yield config
