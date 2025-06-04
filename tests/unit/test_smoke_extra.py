import pytest

from palantir.core.llm_manager import LLMManager
from palantir.core.policy_guard import rate_limit_for_tier
from palantir.core.visualization import generate_plotly_html


def test_llmmanager_invalid_mode():
    llm = LLMManager(offline=True)
    with pytest.raises(ValueError):
        llm.generate_code("test", mode="invalid")


def test_rate_limit_for_tier_default():
    assert rate_limit_for_tier("unknown") == "5/minute"


def test_generate_plotly_html_else():
    html = generate_plotly_html({"type": "unknown", "data": "test"})
    assert html.startswith("<pre>")
