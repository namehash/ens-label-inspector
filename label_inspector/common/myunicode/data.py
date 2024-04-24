import json
from .utils import DATA_JSON_PATH
from label_inspector.common.pickle_cache import pickled_property


def make_int_dict(dict, key):
    dict[key] = {int(k, 16): v for k, v in dict[key].items()}


def remove_fe0f(dict, key):
    dict[key] = {emoji.replace('\ufe0f', ''): name for emoji, name in dict[key].items()}


class MyUnicodeData:
    @pickled_property()
    def _data(self):
        with open(DATA_JSON_PATH, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
            make_int_dict(json_data, 'name')
            make_int_dict(json_data, 'category')
            make_int_dict(json_data, 'combining')
            remove_fe0f(json_data, 'emoji_sequences')
            remove_fe0f(json_data, 'emoji_zwj_sequences')
            remove_fe0f(json_data['versions'], 'unicode')
            remove_fe0f(json_data['versions'], 'emoji')
            # replace None with {} to get KeyError if no special data found
            json_data['special']['data'] = [{} if d is None else d for d in json_data['special']['data']]
            return json_data
    
    def __getitem__(self, key: str):
        return self._data[key]


MY_UNICODE_DATA = MyUnicodeData()
