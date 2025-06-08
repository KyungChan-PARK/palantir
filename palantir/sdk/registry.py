import json
import os
from typing import Type, Dict, Any
from palantir.sdk.components.base import ComponentMeta

COMPONENTS_JSON = os.path.join(os.path.dirname(__file__), "components.json")

_registry = {}

def register(component_cls: Type[ComponentMeta]):
    """컴포넌트 클래스를 레지스트리에 등록하고, components.json을 갱신한다."""
    meta = {
        "id": component_cls.__name__,
        "name": getattr(component_cls, "name", component_cls.__name__),
        "params": getattr(component_cls, "params", {}),
        "doc": component_cls.__doc__ or ""
    }
    _registry[meta["id"]] = meta
    _save_registry()
    return component_cls

def _save_registry():
    with open(COMPONENTS_JSON, "w", encoding="utf-8") as f:
        json.dump(list(_registry.values()), f, ensure_ascii=False, indent=2)

def get_registered_components() -> Dict[str, Any]:
    return _registry.copy()

def ensure_components_json():
    if not os.path.exists(COMPONENTS_JSON):
        with open(COMPONENTS_JSON, "w", encoding="utf-8") as f:
            json.dump([], f)

# 모듈 import 시 자동으로 components.json 파일이 없으면 생성
ensure_components_json()

# 사용 예시
# from palantir.sdk.components.base import ComponentMeta
# @register
# class MyComponent(ComponentMeta):
#     ... 