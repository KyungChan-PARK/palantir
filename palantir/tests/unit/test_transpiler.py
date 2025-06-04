from palantir.core import transpiler


def test_transpile_yaml_to_dag_online():
    d = {"name": "n", "tasks": [1,2]}
    out = transpiler.transpile_yaml_to_dag(d)
    assert out["dag_name"] == "n" and out["tasks"] == [1,2]

def test_transpile_yaml_to_dag_offline(monkeypatch):
    class DummySettings:
        OFFLINE_MODE = True
        LLM_PROVIDER = "openai"
    orig_settings = transpiler.settings
    transpiler.settings = DummySettings()
    d = {"name": "n", "tasks": [1,2]}
    out = transpiler.transpile_yaml_to_dag(d)
    assert "비활성화" in out
    transpiler.settings = orig_settings 