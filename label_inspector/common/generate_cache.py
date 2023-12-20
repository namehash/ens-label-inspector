'''
Executes all functions registered with pickled_property, generating cache.
For each function, creates an instance of the function's class
trying a default constructor first, then using the production config.
'''

import shutil

import label_inspector.inspector
# if there are modules not imported by inspector, import them here

from label_inspector.common import pickle_cache
from label_inspector.config import initialize_inspector_config


def main():
    with initialize_inspector_config('prod_config') as config:
        print('Removing old cache')
        shutil.rmtree(pickle_cache.CACHE_DIR, ignore_errors=True)

        for module, class_name, func_name in pickle_cache.REGISTERED_FUNCTIONS:
            print(f'Generating {module} {class_name}.{func_name}')
            exec(f'import {module}')
            try:
                # try default constructor
                exec(f'{module}.{class_name}().{func_name}')
            except TypeError:
                # pass config
                exec(f'{module}.{class_name}(config).{func_name}')


if __name__ == '__main__':
    main()
