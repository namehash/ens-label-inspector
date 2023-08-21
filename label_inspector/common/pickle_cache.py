from typing import TypeVar, Callable
from functools import wraps, cached_property
import os
import pickle
import hashlib


R = TypeVar('R')

CACHE_DIR = os.path.join(os.path.dirname(__file__), 'cache')
REGISTERED_FUNCTIONS = set()


def _get_config_val(config, key: str) -> str:
    for k in key.split('.'):
        config = config[k]
    return config


def _hash_deps(config, dep_keys: list[str]) -> str:
    hash = hashlib.md5()
    for key in dep_keys:
        hash.update(pickle.dumps(key))
        hash.update(pickle.dumps(_get_config_val(config, key)))
    return hash.hexdigest()


def pickled_property(*dependencies: str):
    '''
    Works like functools.cached_property, but uses pickle to store the value.
    Expects the class to have a config property (unless there are no dependencies).
    Dependencies: keys in self.config this property depends on.
    Value is recomputed when any of the dependency values change.
    The pickle path is {CACHE_DIR}/{module}.{class}.{func}-{hash}.pickle
    '''
    def decorator(func: Callable[..., R]) -> cached_property[R]:
        pickle_name = f'{func.__module__}.{func.__qualname__}'

        @cached_property
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if len(dependencies) > 0:
                hash = _hash_deps(self.config, dependencies)
            else:
                hash = '0'

            cache_file = os.path.join(CACHE_DIR, f'{pickle_name}-{hash}.pickle')

            try:
                with open(cache_file, 'rb') as f:
                    val: R = pickle.load(f)
                    return val
            except FileNotFoundError:
                result = func(self, *args, **kwargs)
                os.makedirs(os.path.dirname(cache_file), exist_ok=True)
                with open(cache_file, 'wb') as f:
                    pickle.dump(result, f)
                return result

        # register function for automatic cache generation
        module = func.__module__
        class_name, func_name = func.__qualname__.split('.')
        REGISTERED_FUNCTIONS.add((module, class_name, func_name))

        return wrapper
    return decorator
