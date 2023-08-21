'''
Executes all functions registered with pickled_property, generating cache.
For each function, creates an instance of the function's class
trying a default constructor first, then using the production config.
'''

import shutil
from hydra import compose, initialize_config_module

import label_inspector.inspector
# if there are modules not imported by inspector, import them here

from label_inspector.common import pickle_cache


def main():
    with initialize_config_module(version_base=None, config_module='inspector_conf'):
        config = compose(config_name='prod_config')

        print('Removing old cache')
        shutil.rmtree(pickle_cache.CACHE_DIR, ignore_errors=True)

        for module, class_name, func_name in pickle_cache.REGISTERED_FUNCTIONS:
            print(f'Generating {module}{class_name}.{func_name}')
            exec(f'import {module}')
            try:
                # try default constructor
                exec(f'{module}.{class_name}().{func_name}')
            except TypeError:
                # pass config
                exec(f'{module}.{class_name}(config).{func_name}')


if __name__ == '__main__':
    main()
