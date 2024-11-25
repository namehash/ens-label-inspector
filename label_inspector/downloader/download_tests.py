import requests
import os
from pathlib import Path


UNICODE_VERSION = '16.0.0'

TESTS_DATA_PATH = Path(__file__).resolve().parent.parent / 'data' / 'tests'


def download_numerics():
    r = requests.get(f'https://www.unicode.org/Public/{UNICODE_VERSION}/ucd/UnicodeData.txt')
    
    with open(TESTS_DATA_PATH / 'unicode_numerics.txt', 'w') as f:
        for line in r.text.splitlines():
            line = line.strip()
            if len(line) == 0 or line.startswith('#'):
                continue

            fields = line.split(';')
            code = fields[0].strip()
            category = fields[2].strip()

            is_numeric = category[0] == 'N'
            
            if is_numeric:
                f.write(f'{code}\n')


def download():
    os.makedirs(TESTS_DATA_PATH, exist_ok=True)
    download_numerics()


if __name__ == "__main__":
    print('Downloading test files...')
    download()
    print('Done')
