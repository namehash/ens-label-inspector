import os
import math
from time import time as get_time
from tqdm import tqdm
import argparse
from pathlib import Path

from fastapi.testclient import TestClient

import label_inspector.web_api as web_api_inspector
from helpers import check_inspector_response, SPECIAL_CHAR_REGEX


def prod_test_client():
    os.environ['CONFIG_NAME'] = 'prod_config'

    client = TestClient(web_api_inspector.app)
    return client


def request_inspector(label):
    return client.post('/', json={'label': label})


def verify_inspector(label, json):
    check_inspector_response(label, json)


def stress_test(fn, filename):
    with open(filename, 'r', encoding='utf-8') as f:
        num_lines = sum(1 for _ in f)
        f.seek(0)

        for i, line in tqdm(enumerate(f), total=num_lines):
            try:
                label = line[:-1]
                fn(label)
            except Exception as e:
                print(f'\n[{i + 1}] {label} failed: {e}')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--no-simple', action='store_true', help=f'Skip simple labels {SPECIAL_CHAR_REGEX.pattern}')
    parser.add_argument('-t', '--timeout', type=float, default=0, help='Timeout [s] for each request')
    parser.add_argument('-l', '--long-length', type=int, default=500,
                        help='Names above this length will not be skipped')
    parser.add_argument('data_file', type=Path, help='File with labels to use')
    args = parser.parse_args()

    module = 'inspector'
    filename = args.data_file
    timeout = math.inf if args.timeout == 0 else args.timeout
    enable_filter = args.no_simple
    long_length = args.long_length

    print('Creating client...')
    client = prod_test_client()

    request_fn = request_inspector
    verify_fn = verify_inspector


    def test_label(label):
        if len(label) < long_length and enable_filter and SPECIAL_CHAR_REGEX.search(label) is None:
            return

        start = get_time()
        resp = request_fn(label)
        duration = get_time() - start

        assert resp.status_code == 200
        assert duration < timeout, f'Time limit exceeded'

        verify_fn(label, resp.json())


    stress_test(test_label, filename)
