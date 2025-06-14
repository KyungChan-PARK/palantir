import pytest

from palantir.core.llm_manager import LLMManager


def test_llm_manager_invalid_mode():
    llm = LLMManager(offline=True)
    with pytest.raises(ValueError):
        llm.generate_code("prompt", mode="not_supported")


def test_llm_manager_offline_sql():
    llm = LLMManager(offline=True)
    code = llm.generate_code("test_query", mode="sql")
    assert code.startswith("SELECT")


def test_llm_manager_offline_pyspark():
    llm = LLMManager(offline=True)
    code = llm.generate_code("test_query", mode="pyspark")
    assert code.startswith("df.filter")


def test_llm_manager_provider_local():
    class DummySettings:
        OFFLINE_MODE = False
        LLM_PROVIDER = "local"

    # settings를 임시로 대체
    orig_settings = LLMManager.__init__.__globals__["settings"]
    LLMManager.__init__.__globals__["settings"] = DummySettings()
    llm = LLMManager()
    code = llm.generate_code("test_query", mode="sql")
    assert code.startswith("SELECT")
    LLMManager.__init__.__globals__["settings"] = orig_settings


def test_llm_manager_provider_unsupported():
    class DummySettings:
        OFFLINE_MODE = False
        LLM_PROVIDER = "unsupported"

    orig_settings = LLMManager.__init__.__globals__["settings"]
    LLMManager.__init__.__globals__["settings"] = DummySettings()
    llm = LLMManager()
    code = llm.generate_code("test_query", mode="sql")
    assert code.startswith("SELECT")
    LLMManager.__init__.__globals__["settings"] = orig_settings


def test_llm_manager_openai_exception(monkeypatch):
    class DummyClient:
        class Chat:
            class Completions:
                @staticmethod
                def create(**kwargs):
                    raise Exception("fail")

    class DummySettings:
        OFFLINE_MODE = False
        LLM_PROVIDER = "openai"

    orig_settings = LLMManager.__init__.__globals__["settings"]
    LLMManager.__init__.__globals__["settings"] = DummySettings()
    llm = LLMManager()
    llm.client = DummyClient()
    code = llm.generate_code("test_query", mode="sql")
    assert code.startswith("SELECT")
    LLMManager.__init__.__globals__["settings"] = orig_settings


def test_llm_manager_azure_exception(monkeypatch):
    class DummyClient:
        class Chat:
            class Completions:
                @staticmethod
                def create(**kwargs):
                    raise Exception("fail")

    class DummySettings:
        OFFLINE_MODE = False
        LLM_PROVIDER = "azure"

    orig_settings = LLMManager.__init__.__globals__["settings"]
    LLMManager.__init__.__globals__["settings"] = DummySettings()
    llm = LLMManager()
    llm.client = DummyClient()
    code = llm.generate_code("test_query", mode="sql")
    assert code.startswith("SELECT")
    LLMManager.__init__.__globals__["settings"] = orig_settings
