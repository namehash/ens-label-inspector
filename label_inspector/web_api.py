import logging
from typing import Union, List
from fastapi import FastAPI

from label_inspector.config import initialize_inspector_config
from label_inspector.inspector import Inspector
from label_inspector.models import BatchInspectorLabel, InspectorLabel, InspectorResultNormalized, InspectorResultUnnormalized, InspectorResult


logger = logging.getLogger('label_inspector')
app = FastAPI()


def init_inspector():
    with initialize_inspector_config('prod_config') as config:
        logger.setLevel(config.app.logging_level)
        for handler in logger.handlers:
            handler.setLevel(config.app.logging_level)
        return Inspector(config)


inspector = init_inspector()


def analyse_label(label: str, request_body: InspectorLabel):
    result = inspector.analyse_label(label,
                                     truncate_confusables=request_body.truncate_confusables,
                                     truncate_graphemes=request_body.truncate_graphemes,
                                     truncate_chars=request_body.truncate_chars)

    if result['status'] == 'normalized':
        model = InspectorResultNormalized
    else:
        model = InspectorResultUnnormalized

    return model(**result)


@app.post("/")
async def default_endpoint(request_body: InspectorLabel) -> InspectorResult:
    return analyse_label(request_body.label, request_body)


@app.post("/batch")
async def batch_endpoint(request_body: BatchInspectorLabel) -> List[InspectorResult]:
    return [analyse_label(label, request_body) for label in request_body.labels]

