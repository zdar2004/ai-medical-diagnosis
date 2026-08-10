import pytest

from app.ai_clinical_assistant.exceptions import ResponseValidationError
from app.ai_clinical_assistant.response_validator import (
    DEFAULT_MAX_LENGTH,
    MEDICAL_DISCLAIMER,
    ResponseValidator,
    TRUNCATION_SUFFIX,
)


@pytest.fixture
def validator():
    return ResponseValidator()


def test_validate_not_empty_success(validator):
    validator.validate_not_empty("Hello")


def test_validate_not_empty_empty_string(validator):
    with pytest.raises(ResponseValidationError):
        validator.validate_not_empty("")


def test_validate_not_empty_whitespace(validator):
    with pytest.raises(ResponseValidationError):
        validator.validate_not_empty("      ")


def test_validate_not_empty_none(validator):
    with pytest.raises(ResponseValidationError):
        validator.validate_not_empty(None)


def test_remove_extra_whitespace(validator):
    text = "  Hello   \n\n\nWorld   \n"

    result = validator.remove_extra_whitespace(text)

    assert result == "Hello\n\nWorld"


def test_contains_medical_disclaimer_false(validator):
    assert validator.contains_medical_disclaimer(
        "Patient is stable."
    ) is False


def test_contains_medical_disclaimer_true(validator):
    text = (
        "Please consult a qualified healthcare professional "
        "before making decisions."
    )

    assert validator.contains_medical_disclaimer(text) is True


def test_append_disclaimer_when_missing(validator):
    result = validator.append_disclaimer("Clinical response.")

    assert "Clinical response." in result
    assert MEDICAL_DISCLAIMER in result


def test_append_disclaimer_not_duplicated(validator):
    text = f"Clinical response.\n\n{MEDICAL_DISCLAIMER}"

    result = validator.append_disclaimer(text)

    assert result.count(MEDICAL_DISCLAIMER) == 1


def test_append_disclaimer_empty_response(validator):
    result = validator.append_disclaimer("")

    assert result == MEDICAL_DISCLAIMER
    
def test_remove_prohibited_claims(validator):
    text = "You definitely have diabetes."

    result = validator.remove_prohibited_claims(text)

    assert "The findings may suggest" in result
    assert "definitely have" not in result.lower()


def test_remove_prohibited_claims_case_insensitive(validator):
    text = "YOU DEFINITELY HAVE pneumonia."

    result = validator.remove_prohibited_claims(text)

    assert "The findings may suggest" in result


def test_remove_prohibited_claims_no_change(validator):
    text = "Your laboratory values should be reviewed by a physician."

    result = validator.remove_prohibited_claims(text)

    assert result == text


def test_enforce_length_limit_not_needed(validator):
    text = "Short response."

    result = validator.enforce_length_limit(text)

    assert result == text


def test_enforce_length_limit_truncates():
    validator = ResponseValidator(max_length=50)

    text = (
        "This is a very long response that should be truncated safely "
        "without breaking words in the middle."
    )

    result = validator.enforce_length_limit(text, max_length=50)

    assert len(result) <= 50
    assert result.endswith(TRUNCATION_SUFFIX)


def test_validate_pipeline():
    validator = ResponseValidator(max_length=300)

    response = (
        "   You definitely have diabetes.   "
    )

    result = validator.validate(response)

    assert "The findings may suggest" in result
    assert MEDICAL_DISCLAIMER in result


def test_validate_pipeline_preserves_safe_text():
    validator = ResponseValidator()

    response = (
        "Laboratory findings should be interpreted together with "
        "clinical history."
    )

    result = validator.validate(response)

    assert "Laboratory findings" in result
    assert MEDICAL_DISCLAIMER in result


def test_replace_case_insensitive_helper(validator):
    result = validator._replace_case_insensitive(
        "HELLO world HELLO",
        "hello",
        "Hi",
    )

    assert result == "Hi world Hi"


def test_multiple_prohibited_replacements(validator):
    text = (
        "You definitely have pneumonia. "
        "This confirms infection."
    )

    result = validator.remove_prohibited_claims(text)

    assert "The findings may suggest" in result
    assert "The available information may indicate" in result


def test_validate_returns_string(validator):
    result = validator.validate("Normal clinical response.")

    assert isinstance(result, str)