import pytest
from palantir.sdk.components.base import ComponentMeta

class DummyComponent(ComponentMeta):
    def execute(self, **kwargs):
        return "executed"

def test_componentmeta_cannot_instantiate_abstract():
    with pytest.raises(TypeError):
        ComponentMeta(id="1", name="Base", params={})

def test_componentmeta_execute():
    comp = DummyComponent(id="2", name="Dummy", params={"x": 1})
    assert comp.execute() == "executed" 