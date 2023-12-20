import logging
from typing import List
from fastapi import FastAPI

from label_inspector.config import initialize_inspector_config
from label_inspector.inspector import Inspector
from label_inspector.models import InspectorSingleRequest, InspectorBatchRequest, InspectorResult, InspectorBatchResult


logger = logging.getLogger('label_inspector')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(stream_handler)

app = FastAPI()


def init_inspector():
    with initialize_inspector_config('prod_config') as config:
        logger.setLevel(config.app.logging_level)
        for handler in logger.handlers:
            handler.setLevel(config.app.logging_level)
        return Inspector(config)


inspector = init_inspector()


def analyse_label(label: str, request_body: InspectorSingleRequest) -> InspectorResult:
    result = inspector.analyse_label(
        label,
        truncate_confusables=request_body.truncate_confusables,
        truncate_graphemes=request_body.truncate_graphemes,
        truncate_chars=request_body.truncate_chars,
        simple_confusables=request_body.simple_confusables,
    )
    return result


@app.post("/")
async def single_endpoint(request_body: InspectorSingleRequest) -> InspectorResult:
    return analyse_label(request_body.label, request_body)


@app.post("/batch")
async def batch_endpoint(request_body: InspectorBatchRequest) -> InspectorBatchResult:
    results = [analyse_label(label, request_body) for label in request_body.labels]
    return InspectorBatchResult(results=results)
