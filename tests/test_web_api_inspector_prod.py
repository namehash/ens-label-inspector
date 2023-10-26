import os
import random
from time import time as get_time

import pytest
from fastapi.testclient import TestClient

import label_inspector.web_api as web_api_inspector

from helpers import check_inspector_response, generate_example_names


@pytest.fixture(scope="module")
def prod_test_client():
    os.environ['CONFIG_NAME'] = 'prod_config'
    client = TestClient(web_api_inspector.app)
    return client


@pytest.mark.execution_timeout(10)
def test_prod_inspector_long_post(prod_test_client):
    client = prod_test_client
    response = client.post("/",
                           json={'label': "miinibaashkiminasiganibiitoosijiganibadagwiingweshiganibakwezhigan"})
    assert response.status_code == 200
    json = response.json()
    assert 'label' in json


@pytest.mark.execution_timeout(20)
def test_prod_inspector_long2_post(prod_test_client):
    client = prod_test_client
    response = client.post("/", json={'label': 'a' * 40000})
    assert response.status_code == 200
    json = response.json()
    assert 'label' in json


def test_inspector_basic(prod_test_client):
    label = 'cat'
    response = prod_test_client.post('/', json={'label': label})
    assert response.status_code == 200
    json = response.json()

    check_inspector_response(label, json)

    assert json['all_type'] == 'simple_letter'
    assert json['all_script'] == 'Latin'
    assert json['any_scripts'] == ['Latin']
    assert json['any_types'] == ['simple_letter']
    assert len(json['graphemes']) == 3

    # order of the returned characters must match input label
    all_chars = [c for grapheme in json['graphemes'] for c in grapheme['chars']]
    for char, name_char in zip(all_chars, label):
        assert char['script'] == 'Latin'
        assert char['name'] == f'LATIN SMALL LETTER {name_char.upper()}'
        assert char['type'] == 'simple_letter'

    for grapheme in json['graphemes']:
        assert grapheme['confusables_other'] == []


def test_inspector_special(prod_test_client):
    label = 'żóć'
    response = prod_test_client.post('/', json={'label': label})
    assert response.status_code == 200
    json = response.json()

    check_inspector_response(label, json)

    assert json['all_type'] == 'other_letter'
    assert json['all_script'] == 'Latin'
    assert json['any_scripts'] == ['Latin']
    assert json['any_types'] == ['other_letter']
    assert len(json['graphemes']) == 3

    # order of the returned characters must match input label
    all_chars = [c for grapheme in json['graphemes'] for c in grapheme['chars']]
    for char, canonical_char in zip(all_chars, 'zoc'):
        assert char['script'] == 'Latin'
        assert char['name'].startswith(f'LATIN SMALL LETTER {canonical_char.upper()}')
        assert char['type'] == 'other_letter'

    for grapheme, canonical_char in zip(json['graphemes'], 'zoc'):
        found_canonical_in_confusables = False
        for conf in grapheme['confusables_other']:
            for char in conf['chars']:
                found_canonical_in_confusables |= char['value'] == canonical_char
        assert found_canonical_in_confusables


@pytest.mark.parametrize(
    'label',
    [
        'dbque.eth\n',
        '🇪🇹is🦇🔊💲.eth',
        'iwant\U0001faf5.eth',
        'iwant\\U0001faf5.eth',
        'iwant\\\\U0001faf5.eth',
        'iwant🫵.eth',
        'ЁЯй╖ЁЯй╖ЁЯй╖.eth',
        'ЁЯлиЁЯлиЁЯли.eth',
        'ЁЯй╡ЁЯй╡ЁЯй╡ЁЯй╡ЁЯй╡.eth',
        'ЁЯй╢ЁЯй╢ЁЯй╢ЁЯй╢ЁЯй╢.eth',
        'ЁЯй╖ЁЯй╖ЁЯй╖ЁЯй╖ЁЯй╖.eth',
        'ЁЯй╡ЁЯй╡ЁЯй╡.eth',
        'ЁЯй╢ЁЯй╢ЁЯй╢.eth',
    ]
)
def test_inspector_special_cases(prod_test_client, label):
    response = prod_test_client.post('/', json={'label': label})
    assert response.status_code == 200
    check_inspector_response(label, response.json())



@pytest.mark.parametrize(
    'label',
    [
        '🩶🩶🩶🩶🩶.eth',
        '🫨🫨🫨.eth',
        '🩷🩷🩷.eth',
        '🩶🩶🩶🩶🩶.eth',
        'i🩷u.eth',
    ]
)
def test_inspector_invalid_script(prod_test_client, label):
    response = prod_test_client.post('/', json={'label': label})
    assert response.status_code == 200
    check_inspector_response(label, response.json())


def test_inspector_stress(prod_test_client):
    client = prod_test_client
    max_duration = 3
    start1 = get_time()
    for label in generate_example_names(400):
        start = get_time()
        response = client.post('/', json={'label': label})
        duration = get_time() - start
        assert response.status_code == 200, f'{label} failed with {response.status_code}'
        assert duration < max_duration, f'Time exceeded on {label}'
        check_inspector_response(label, response.json())
    duration = get_time() - start1
    print(f'Processed names in {duration:.2f}s')


def test_inspector_stress2(prod_test_client):
    client = prod_test_client
    max_duration = 3
    start1 = get_time()
    for label in generate_example_names(5000):
        start = get_time()
        response = client.post('/',
                               json={'label': label, 'truncate_chars': 0, 'truncate_graphemes': 0,
                                     'truncate_confusables': 0})
        duration = get_time() - start
        assert response.status_code == 200, f'{label} failed with {response.status_code}'
        assert duration < max_duration, f'Time exceeded on {label}'
        check_inspector_response(label, response.json(), truncate_chars=0, truncate_graphemes=0,
                                 truncate_confusables=0)
    duration = get_time() - start1
    print(f'Processed names in {duration:.2f}s')


def test_inspector_limit_confusables(prod_test_client):
    label = 'ącat'
    response = prod_test_client.post('/', json={'label': label, 'truncate_confusables': 1})
    assert response.status_code == 200
    json = response.json()
    print(json)
    check_inspector_response(label, json, truncate_confusables=1)

    assert json['all_type'] is None
    assert json['all_script'] == 'Latin'
    assert json['any_scripts'] == ['Latin']
    assert sorted(json['any_types']) == ['other_letter', 'simple_letter']
    assert len(json['graphemes']) == 4

    assert len(json['graphemes'][0]['confusables_other']) == 1


def test_inspector_disable_chars_output(prod_test_client):
    label = 'cat'
    response = prod_test_client.post('/', json={'label': label, 'truncate_graphemes': 0})
    assert response.status_code == 200
    json = response.json()
    print(json)
    check_inspector_response(label, json, truncate_graphemes=0)

    assert json['all_type'] == 'simple_letter'
    assert json['all_script'] == 'Latin'
    assert json['any_scripts'] == ['Latin']
    assert json['any_types'] == ['simple_letter']
    assert len(json['graphemes']) == 0

    all_chars = [c for grapheme in json['graphemes'] for c in grapheme['chars']]
    assert len(all_chars) == 0


@pytest.mark.execution_timeout(10)
def test_prod_inspector_confusable(prod_test_client):
    client = prod_test_client
    response = client.post("/",
                           json={'label': "tést"})

    assert response.status_code == 200

    json = response.json()
    assert len(json['graphemes']) == 4
    assert 'label' in json
    assert json['confusable_count']


@pytest.mark.parametrize(
    'label, graphemes',
    [
        ('🇪🇹', 1),
        ('👨‍👩‍👧', 1),
        ('-\u0610', 1),
    ]
)
def test_inspector_graphemes(prod_test_client, label, graphemes):
    response = prod_test_client.post('/', json={'label': label})
    assert response.status_code == 200
    json = response.json()
    check_inspector_response(label, json)
    assert len(json['graphemes']) < len(label)
    assert len(json['graphemes']) == graphemes


def test_inspector_truncate_graphemes(prod_test_client):
    label = '-\u0610-\u0610'
    response = prod_test_client.post('/', json={'label': label, 'truncate_graphemes': 1})
    assert response.status_code == 200
    json = response.json()
    check_inspector_response(label, json, truncate_graphemes=1)
    assert [len(g['chars']) for g in json['graphemes']] == [2]


def test_inspector_truncate_chars_in_graphemes(prod_test_client):
    label = '-\u0610-\u0610'
    response = prod_test_client.post('/', json={'label': label, 'truncate_chars': 1})
    assert response.status_code == 200
    json = response.json()
    check_inspector_response(label, json, truncate_chars=1)
    assert [len(g['chars']) for g in json['graphemes']] == [1, 1]


def test_inspector_truncate_chars_in_graphemes2(prod_test_client):
    label = '00000000000000000000000000000000000000ᴅᴇᴀᴅ'
    response = prod_test_client.post('/', json={'label': label, 'truncate_chars': 0})
    assert response.status_code == 200
    json = response.json()
    check_inspector_response(label, json, truncate_chars=0)
    assert [len(g['chars']) for g in json['graphemes']] == [0] * len(label)


def test_inspector_truncate_graphemes_and_chars(prod_test_client):
    label = '-\u0610-\u0610'
    response = prod_test_client.post('/', json={'label': label, 'truncate_graphemes': 1, 'truncate_chars': 1})
    assert response.status_code == 200
    json = response.json()
    check_inspector_response(label, json, truncate_graphemes=1, truncate_chars=1)
    assert [len(g['chars']) for g in json['graphemes']] == [1]


def test_inspector_zwj_emoji_sequence(prod_test_client):
    label = '👩🏻‍🤝‍👩🏼'
    response = prod_test_client.post('/', json={'label': label})
    assert response.status_code == 200
    json = response.json()
    check_inspector_response(label, json)
    assert 'invisible' not in json['any_types']


def test_inspector_empty_label(prod_test_client):
    response = prod_test_client.post('/', json={'label': ''})
    assert response.status_code == 200
    json = response.json()
    check_inspector_response('', json)


@pytest.mark.parametrize(
    'label,expected',
    [
        ('bąrdżó-lądńą-ńąźwą', True),
        ('disallowed space', False),
        ('aąaąaą', False),
        ('2᷑j᫄ꪳξ樂難ѕs羽', False),
    ]
)
def test_inspector_is_normalized(prod_test_client, label, expected):
    response = prod_test_client.post('/', json={'label': label})
    assert response.status_code == 200
    json = response.json()
    check_inspector_response(label, json)
    assert (json['status'] == 'normalized') == expected


@pytest.mark.parametrize('label,is_normalized', [
    ('goodname', True),
    ('unnorma\u0328', False),
    ('bad_name', False)
])
def test_inspector_response_model(prod_test_client, label, is_normalized):
    response = prod_test_client.post('/', json={'label': label})
    assert response.status_code == 200
    json = response.json()
    assert (json['status'] == 'normalized') == is_normalized
    check_inspector_response(label, json)


def test_inspector_emoji_confusables(prod_test_client):
    label = '🧟‍♂'
    response = prod_test_client.post('/', json={'label': label})
    assert response.status_code == 200
    json = response.json()

    check_inspector_response(label, json)

    assert json['all_type'] == 'emoji'
    assert json['all_script'] == 'Common'
    assert json['any_scripts'] == ['Common']
    assert json['any_types'] == ['emoji']
    assert len(json['graphemes']) == 1
    assert json['confusable_count'] == 1

    grapheme = json['graphemes'][0]

    assert grapheme['value'] == '🧟‍♂'
    assert grapheme['name'] == 'MAN ZOMBIE'
    assert grapheme['script'] == 'Common'
    assert grapheme['type'] == 'emoji'
    assert grapheme['confusables_canonical'] is not None
    assert grapheme['confusables_canonical']['value'] == '🧟'
    assert len(grapheme['confusables_other']) == 1
    assert grapheme['confusables_other'][0]['value'] == '🧟‍♀'


def test_inspector_confusables(prod_test_client):
    label = 'ą'
    response = prod_test_client.post('/', json={'label': label})
    assert response.status_code == 200
    json = response.json()

    check_inspector_response(label, json)

    assert json['all_type'] == 'other_letter'
    assert json['all_script'] == 'Latin'
    assert json['any_scripts'] == ['Latin']
    assert json['any_types'] == ['other_letter']
    assert len(json['graphemes']) == 1
    assert json['confusable_count'] == 1

    grapheme = json['graphemes'][0]

    assert grapheme['value'] == 'ą'
    assert grapheme['name'] == 'LATIN SMALL LETTER A WITH OGONEK'
    assert grapheme['script'] == 'Latin'
    assert grapheme['type'] == 'other_letter'
    assert grapheme['confusables_canonical'] is not None
    assert grapheme['confusables_canonical']['value'] == 'a'
    assert len(grapheme['confusables_other']) >= 1


def test_inspector_confusables_ascii(prod_test_client):
    label = 'a'
    response = prod_test_client.post('/', json={'label': label})
    assert response.status_code == 200
    json = response.json()

    check_inspector_response(label, json)

    assert json['all_type'] == 'simple_letter'
    assert json['all_script'] == 'Latin'
    assert json['any_scripts'] == ['Latin']
    assert json['any_types'] == ['simple_letter']
    assert len(json['graphemes']) == 1
    assert json['confusable_count'] == 0

    grapheme = json['graphemes'][0]

    assert grapheme['value'] == 'a'
    assert grapheme['name'] == 'LATIN SMALL LETTER A'
    assert grapheme['script'] == 'Latin'
    assert grapheme['type'] == 'simple_letter'
    assert grapheme['confusables_canonical'] is None

    assert len(grapheme['confusables_other']) == 0


def test_inspector_confusable_ascii_combining(prod_test_client):
    label = '-\u0610'
    response = prod_test_client.post('/', json={'label': label})
    assert response.status_code == 200
    json = response.json()

    check_inspector_response(label, json)

    assert json['all_type'] == 'special'
    assert json['all_script'] == 'Arabic'
    assert json['any_scripts'] == ['Arabic']
    assert json['any_types'] == ['special']
    assert len(json['graphemes']) == 1
    assert json['confusable_count'] == 1

    grapheme = json['graphemes'][0]

    assert grapheme['value'] == '-\u0610'
    assert grapheme['name'] == 'Combined Character'
    assert grapheme['script'] == 'Arabic'
    assert grapheme['type'] == 'special'
    assert grapheme['confusables_canonical'] is not None
    assert grapheme['confusables_canonical']['value'] == '-'
    assert len(grapheme['confusables_other']) >= 1


def test_inspector_emoji_with_ascii(prod_test_client):
    label = '*⃣'
    response = prod_test_client.post('/', json={'label': label})
    assert response.status_code == 200
    json = response.json()

    check_inspector_response(label, json)

    assert json['all_type'] == 'emoji'
    assert json['all_script'] == 'Common'
    assert json['any_scripts'] == ['Common']
    assert json['any_types'] == ['emoji']
    assert len(json['graphemes']) == 1
    assert json['confusable_count'] == 1

    grapheme = json['graphemes'][0]

    assert grapheme['value'] == '*⃣'
    assert grapheme['name'] == 'KEYCAP: *'
    assert grapheme['script'] == 'Common'
    assert grapheme['type'] == 'emoji'
    assert grapheme['confusables_canonical']['value'] == '*⃣'
    assert len(grapheme['confusables_other']) == 11
    confusables = [value['value'] for value in grapheme['confusables_other']]
    assert '8⃣' in confusables


@pytest.mark.parametrize('label,status', [
    ('goodlabel', 'normalized'),
    ('UnNoRmAlIzEd', 'unnormalized'),
    ('[' + '0' * 64 + ']', 'unnormalized'),
])
def test_inspector_label_status(prod_test_client, label, status):
    response = prod_test_client.post('/', json={'label': label})
    assert response.status_code == 200
    json = response.json()
    assert json['status'] == status
    check_inspector_response(label, json)


@pytest.mark.execution_timeout(20)
@pytest.mark.parametrize('length,limit', [
    (30, 1),
    (100, 2),
    (38894, 10),
])
def test_inspector_longest_speed_limit(prod_test_client, length, limit):
    truncate_graphemes = 100
    truncate_confusables = 20

    confs = 'śąęćżźńó'
    random.seed(42)
    labels = [''.join(random.choice(confs) for _ in range(length)) for _ in range(3)]

    times = []
    for l in labels:
        start = get_time()
        response = prod_test_client.post('/', json={
            'label': l,
            'truncate_graphemes': truncate_graphemes,
            'truncate_confusables': truncate_confusables,
        })
        times.append(get_time() - start)
        assert response.status_code == 200

    t = min(times)

    assert t < limit, f'Time limit exceeded: {t} s'
