import pytest

from app.ai_clinical_assistant.exceptions import InvalidUserInputError
from app.report_analysis.providers.dummy_provider import (
    DUMMY_PROVIDER_NAME,
    DUMMY_RESPONSE_TEXT,
    DummyProvider,
)


@pytest.fixture
def provider():
    return DummyProvider()


def test_provider_initialization(provider):
    assert provider is not None


def test_provider_name(provider):
    assert provider.provider_name() == DUMMY_PROVIDER_NAME


def test_provider_available(provider):
    assert provider.is_available() is True


def test_generate_returns_fixed_response(provider):
    result = provider.generate("Hello")

    assert result == DUMMY_RESPONSE_TEXT


def test_generate_is_deterministic(provider):
    first = provider.generate("Question one")
    second = provider.generate("Question two")

    assert first == second == DUMMY_RESPONSE_TEXT


def test_generate_empty_prompt(provider):
    with pytest.raises(InvalidUserInputError):
        provider.generate("")


def test_generate_whitespace_prompt(provider):
    with pytest.raises(InvalidUserInputError):
        provider.generate("      ")


def test_generate_none_prompt(provider):
    with pytest.raises(InvalidUserInputError):
        provider.generate(None)