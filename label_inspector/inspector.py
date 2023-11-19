import unicodedata
from omegaconf import DictConfig

from label_inspector.config import initialize_config_module
from label_inspector.common import myunicode
from label_inspector.components.features import Features
from label_inspector.analysis.label_analysis import LabelAnalysis, LabelAnalysisConfig
from label_inspector.models import (
    InspectorResultNormalized,
    InspectorResultUnnormalized,
    InspectorResult,
)


def remove_accents(input_str: str) -> str:
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return u"".join([c for c in nfkd_form if not myunicode.combining(c)])


def strip_accents(s: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFD', s)
                   if myunicode.category(c) != 'Mn')


class Inspector:
    def __init__(self, config: DictConfig):
        self.config = config
        self.f = Features(config)

    def analyse_label(self, label: str,
                      truncate_confusables: int = None,
                      truncate_graphemes: int = None,
                      truncate_chars: int = None,
                      simple_confusables: bool = False,
                      omit_cure: bool = False,
                      ) -> InspectorResult:
        config = LabelAnalysisConfig(
            label,
            truncate_confusables=truncate_confusables,
            truncate_graphemes=truncate_graphemes,
            truncate_chars=truncate_chars,
            simple_confusables=simple_confusables,
            omit_cure=omit_cure,
        )

        label_analysis = LabelAnalysis(self, config)
        result = label_analysis.materialize()

        if result['status'] == 'normalized':
            return InspectorResultNormalized(**result)
        else:
            return InspectorResultUnnormalized(**result)


def main():
    with initialize_config_module('prod_config') as config:
        print('Unicode version', unicodedata.unidata_version)

        labels = ['🅜🅜🅜', 'ന്‌മ', 'a‌b.eth', '1a〆.eth', 'аррӏе.eth', 'as', '.', 'ASD', 'Bloß.de', 'xn--0.pt', 'u¨.com',
                  'a⒈com', 'a_a', 'a👍a', 'a‍a', 'łąść', 'ᴄeo', 'ǉeto', 'pаypаl', 'ѕсоре', 'laptop']

        inspector = Inspector(config)
        for label in labels:
            print(label)
            print(inspector.analyse_label(label))


if __name__ == "__main__":
    main()
