import os
import json
import tempfile
from palantir.sdk.registry import register, COMPONENTS_JSON, get_registered_components
from palantir.sdk.components.base import ComponentMeta

class TestComponent(ComponentMeta):
    name = "TestComponent"
    params = {"foo": "bar"}
    def execute(self, **kwargs):
        return "ok"

def test_register_and_json(tmp_path, monkeypatch):
    # components.json 임시 경로로 변경
    tmp_json = tmp_path / "components.json"
    monkeypatch.setattr("palantir.sdk.registry.COMPONENTS_JSON", str(tmp_json))
    # 레지스트리 초기화
    from palantir.sdk import registry
    registry._registry.clear()
    # 등록
    register(TestComponent)
    # 파일 생성 및 내용 확인
    assert os.path.exists(tmp_json)
    with open(tmp_json, encoding="utf-8") as f:
        data = json.load(f)
    assert any(c["id"] == "TestComponent" for c in data)
    # get_registered_components 동작 확인
    comps = get_registered_components()
    assert "TestComponent" in comps 