# NameHash Label Inspector

The Label Inspector is a critical component of the NameHash software stack that is used to protect users from malicious domain names.

* ENS-tailored domain name label inspection
  * Character and grapheme information, scripts, codepoints, ...
  * Confusable grapheme detection
  * Rendering checks for different fonts
  * ENSIP-15 verification with detailed explanations and auto-suggestions
  * Punycode and DNS hostname compatibility checks
* Supports many use cases
  * Standalone Python library ([PyPI](https://pypi.org/project/ens-label-inspector/))
  * ASGI web server
  * [Amazon AWS Lambda](https://aws.amazon.com/lambda/) handler

## Getting Started

### Installing the library

The Label Inspector is available as a Python library on [PyPI](https://pypi.org/project/ens-label-inspector/). You can install it with `pip`:

```bash
pip install ens-label-inspector
```

### Starting the web server

A FastAPI application is included in the `label_inspector.web_api` module. The default installation from PyPI does not include an ASGI server, so you will need to install one separately. For example, to install [uvicorn](https://www.uvicorn.org):

```bash
pip install 'uvicorn[standard]'
```

You can start the web server with:

```bash
uvicorn label_inspector.web_api:app
```

Make an example request:

```bash
curl -d '{"label":"nick"}' -H "Content-Type: application/json" -X POST http://localhos
t:8000
# {"label":"nick","status":"normalized", ...
```

### Using the AWS Lambda handler

The Label Inspector includes a handler for [Amazon AWS Lambda](https://aws.amazon.com/lambda/). It is available in the `label_inspector.lambda` module. You can use it to create a Lambda function that will respond to HTTP requests. It uses the [mangum](https://mangum.io) library.

See the included [Dockerfile](/Dockerfile) for an example of how to build a Lambda deployment package.

## License

Licensed under the MIT License, Copyright © 2023-present [NameHash Labs](https://namehashlabs.org).

See [LICENSE](./LICENSE) for more information.
