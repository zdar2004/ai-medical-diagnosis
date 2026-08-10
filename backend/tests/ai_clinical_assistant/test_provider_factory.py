import pytest

from app.ai_clinical_assistant.exceptions import ConfigurationError
from app.ai_clinical_assistant.provider_factory import ProviderFactory
from app.report_analysis.providers.dummy_provider import DummyProvider
from app.report_analysis.providers.gemini_provider import GeminiProvider
from app.report_analysis.providers.openai_provider import OpenAIProvider


def test_factory_initialization():
    factory = ProviderFactory()
    assert factory is not None


def test_get_dummy_provider():
    factory = ProviderFactory()

    provider = factory.get_provider("dummy")

    assert isinstance(provider, DummyProvider)


def test_get_gemini_provider(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")

    factory = ProviderFactory()

    provider = factory.get_provider("gemini")

    assert isinstance(provider, GeminiProvider)


def test_get_openai_provider(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "fake-key")

    factory = ProviderFactory()

    provider = factory.get_provider("openai")

    assert isinstance(provider, OpenAIProvider)


def test_invalid_provider():
    factory = ProviderFactory()

    with pytest.raises(ConfigurationError):
        factory.get_provider("invalid-provider")


def test_provider_names():
    factory = ProviderFactory()

    assert factory.get_provider("dummy").provider_name() == "dummy"


def test_factory_returns_new_instance():
    factory = ProviderFactory()

    provider1 = factory.get_provider("dummy")
    provider2 = factory.get_provider("dummy")

    assert provider1 is not provider2