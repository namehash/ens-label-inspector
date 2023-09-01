FROM public.ecr.aws/lambda/python:3.11

WORKDIR /app

COPY pyproject.toml poetry.lock README.md LICENSE ./
COPY label_inspector ./label_inspector/
RUN pip install --no-cache-dir .[lambda]

CMD [ "label_inspector.lambda.handler" ]
