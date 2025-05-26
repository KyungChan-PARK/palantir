import pytest
from palantir.core.llm_manager import LLMManager

def test_llm_manager_invalid_mode():
    with pytest.raises(ValueError):
        LLMManager().generate_code("prompt", mode="not_supported") 