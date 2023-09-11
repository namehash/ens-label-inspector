import os

import pytest
from fastapi.testclient import TestClient

import label_inspector.web_api as web_api_inspector

from helpers import check_inspector_response


@pytest.fixture(scope="module")
def test_test_client():
    os.environ['CONFIG_NAME'] = 'test_config'

    client = TestClient(web_api_inspector.app)
    return client


def test_inspector_fast(test_test_client):
    label = 'cat'
    response = test_test_client.post('/', json={'label': label})
    assert response.status_code == 200
    json = response.json()

    check_inspector_response(label, json)


def test_inspector_negative_score(test_test_client):
    label = 'fourscoreandsevenyearsagoourfathersbroughtforthonthiscontinentanewnationconceivedinlibertyanddedicatedtothepropositionthatallmenarecreatedequalnowweareengagedinagreatcivilwartestingwhetherthatnationoranynationsoconceivedandsodedicatedcanlongendurewearemetonagreatbattlefieldofthatwarwehavecometodedicateaportionofthatfieldasafinalrestingplaceforthosewhoheregavetheirlivesthatthatnationmightliveitisaltogetherfittingandproperthatweshoulddothisbutinalargersensewecannotdedicatewecannotconsecratewecannothallowthisgroundthebravemenlivinganddeadwhostruggledherehaveconsecrateditfaraboveourpoorpowertoaddordetracttheworldwilllittlenotenorlongrememberwhatwesayherebutitcanneverforgetwhattheydidhereitisforusthelivingrathertobededicatedheretotheunfinishedworkwhichtheywhofoughtherehavethusfarsonoblyadvanceditisratherforustobeherededicatedtothegreattaskremainingbeforeusthatfromthesehonoreddeadwetakeincreaseddevotiontothatcauseforwhichtheyheregavethelastfullmeasureofdevotionthatweherehighlyresolvethatthesedeadshallnothavediedinvainthatthisnationundergodshallhaveanewbirthoffreedomandthatgovernmentofthepeoplebythepeopleforthepeopleshallnotperishfromtheearth.eth'
    response = test_test_client.post('/', json={'label': label})
    assert response.status_code == 200
    check_inspector_response(label, response.json())


def test_inspector_cured_label(test_test_client):
    label = 'my name'
    response = test_test_client.post('/', json={'label': label})
    assert response.status_code == 200
    resp = response.json()
    check_inspector_response(label, resp)
    assert resp['cured_label'] == 'myname'

    label = ''
    response = test_test_client.post('/', json={'label': label})
    assert response.status_code == 200
    resp = response.json()
    check_inspector_response(label, resp)
    assert resp['status'] == 'normalized'

    label = '0х0'
    response = test_test_client.post('/', json={'label': label})
    assert response.status_code == 200
    resp = response.json()
    check_inspector_response(label, resp)
    assert resp['cured_label'] == None


def test_inspector_batch(test_test_client):
    labels = ['cat', 'dog', 'horse']
    response = test_test_client.post('/batch', json={'labels': labels})
    assert response.status_code == 200
    resp = response.json()
    assert len(resp['results']) == len(labels)
    for label, result in zip(labels, resp['results']):
        check_inspector_response(label, result)
