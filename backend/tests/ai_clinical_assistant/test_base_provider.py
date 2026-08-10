import pytest

from app.ai_clinical_assistant.exceptions import InvalidUserInputError
from app.report_analysis.providers.base_provider import BaseProvider


class DummyProvider(BaseProvider):
    def generate(self, prompt: str) -> str:
        self.validate_prompt(prompt)
        return "dummy response"

    def provider_name(self) -> str:
        return "dummy"

    def is_available(self) -> bool:
        return True


@pytest.fixture
def provider():
    return DummyProvider()


def test_provider_name(provider):
    assert provider.provider_name() == "dummy"


def test_provider_available(provider):
    assert provider.is_available() is True


def test_generate(provider):
    result = provider.generate("Hello")

    assert result == "dummy response"


def test_validate_prompt_valid(provider):
    provider.validate_prompt("Valid prompt")


def test_validate_prompt_empty(provider):
    with pytest.raises(InvalidUserInputError):
        provider.validate_prompt("")


def test_validate_prompt_whitespace(provider):
    with pytest.raises(InvalidUserInputError):
        provider.validate_prompt("      ")


def test_validate_prompt_none(provider):
    with pytest.raises(InvalidUserInputError):
        provider.validate_prompt(None)