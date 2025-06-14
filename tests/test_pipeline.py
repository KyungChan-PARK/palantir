from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


VALID_YAML = """

name: test-pipeline

description: test

tasks:

  - id: t1

    type: python

    params:

      script: print('hi')

    depends_on: []

"""


INVALID_YAML = """

name: test-pipeline

description: test

tasks:

  - id: t1

    params: {}

"""


def test_pipeline_validate_success():

    res = client.post(
        "/pipeline/validate", files={"file": ("pipeline.yaml", VALID_YAML)}
    )

    assert res.status_code == 200

    assert res.json()["valid"] is True


def test_pipeline_validate_fail():

    res = client.post(
        "/pipeline/validate", files={"file": ("pipeline.yaml", INVALID_YAML)}
    )

    assert res.status_code == 200

    assert res.json()["valid"] is False
