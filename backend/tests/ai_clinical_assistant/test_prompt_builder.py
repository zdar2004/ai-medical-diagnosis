import pytest

from app.ai_clinical_assistant.prompt_builder import (
    MAX_CONVERSATION_MESSAGES,
    NOT_AVAILABLE,
    PromptBuilder,
)


@pytest.fixture
def builder():
    return PromptBuilder()


@pytest.fixture
def sample_context():
    return {
        "patient": {
            "patient_id": "P001",
            "age": 35,
            "gender": "Male",
        },
        "medical_history": [
            "Diabetes",
            "Hypertension",
        ],
        "medications": [
            "Metformin",
        ],
        "allergies": [
            "Penicillin",
        ],
        "risk_assessment": {
            "risk": "High",
            "score": 0.87,
        },
        "laboratory_results": {
            "HbA1c": 8.2,
            "Glucose": 190,
        },
        "clinical_summary": "Patient has uncontrolled diabetes.",
        "conversation_history": [
            {
                "role": "user",
                "content": "Hello",
            },
            {
                "role": "assistant",
                "content": "Hi, how can I help?",
            },
        ],
    }


def test_build_system_prompt(builder):
    prompt = builder.build_system_prompt()

    assert "AI Clinical Assistant" in prompt
    assert "never diagnose disease" in prompt
    assert "never prescribe medication" in prompt


def test_build_user_prompt(builder, sample_context):
    prompt = builder.build_user_prompt(
        "What is the patient's condition?",
        sample_context,
    )

    assert "PATIENT INFORMATION" in prompt
    assert "MEDICAL HISTORY" in prompt
    assert "CURRENT MEDICATIONS" in prompt
    assert "ALLERGIES" in prompt
    assert "RISK ASSESSMENT" in prompt
    assert "LABORATORY RESULTS" in prompt
    assert "CLINICAL SUMMARY" in prompt
    assert "PREVIOUS CONVERSATION" in prompt
    assert "USER QUESTION" in prompt


def test_complete_prompt(builder, sample_context):
    prompt = builder.build_complete_prompt(
        "Explain the report.",
        sample_context,
    )

    assert "AI Clinical Assistant" in prompt
    assert "USER QUESTION" in prompt
    assert "Explain the report." in prompt


def test_empty_context(builder):
    prompt = builder.build_user_prompt(
        "Hello",
        {},
    )

    assert NOT_AVAILABLE in prompt


def test_patient_format(builder, sample_context):
    result = builder._format_patient(sample_context)

    assert "patient id: P001" in result
    assert "age: 35" in result
    assert "gender: Male" in result


def test_history_format(builder, sample_context):
    result = builder._format_history(sample_context)

    assert "- Diabetes" in result
    assert "- Hypertension" in result


def test_medication_format(builder, sample_context):
    result = builder._format_medications(sample_context)

    assert "- Metformin" in result


def test_allergy_format(builder, sample_context):
    result = builder._format_allergies(sample_context)

    assert "- Penicillin" in result


def test_risk_format(builder, sample_context):
    result = builder._format_risk(sample_context)

    assert "risk: High" in result
    assert "score: 0.87" in result


def test_laboratory_format(builder, sample_context):
    result = builder._format_laboratory(sample_context)

    assert "HbA1c: 8.2" in result
    assert "Glucose: 190" in result
    
def test_summary_format(builder, sample_context):
    result = builder._format_summary(sample_context)

    assert result == "Patient has uncontrolled diabetes."


def test_conversation_format(builder, sample_context):
    result = builder._format_conversation(sample_context)

    assert "User:" in result
    assert "Assistant:" in result
    assert "Hello" in result
    assert "Hi, how can I help?" in result


def test_conversation_not_available(builder):
    result = builder._format_conversation({})

    assert result == NOT_AVAILABLE


def test_user_question_empty(builder):
    prompt = builder.build_user_prompt("", {})

    assert "USER QUESTION" in prompt
    assert NOT_AVAILABLE in prompt


def test_dictionary_rendering(builder):
    data = {"risk": "High", "score": 95}

    result = builder._format_risk({"risk_assessment": data})

    assert "risk: High" in result
    assert "score: 95" in result


def test_list_rendering(builder):
    result = builder._format_history(
        {
            "medical_history": [
                "Asthma",
                "Diabetes",
            ]
        }
    )

    assert "- Asthma" in result
    assert "- Diabetes" in result


def test_conversation_limit(builder):
    history = []

    for i in range(MAX_CONVERSATION_MESSAGES + 5):
        history.append(
            {
                "role": "user",
                "content": f"Message {i}",
            }
        )

    result = builder._format_conversation(
        {
            "conversation_history": history,
        }
    )

    assert "Message 0" not in result
    assert f"Message {MAX_CONVERSATION_MESSAGES + 4}" in result


def test_prompt_order(builder, sample_context):
    prompt = builder.build_user_prompt("Test", sample_context)

    assert prompt.index("PATIENT INFORMATION") < prompt.index("MEDICAL HISTORY")
    assert prompt.index("MEDICAL HISTORY") < prompt.index("CURRENT MEDICATIONS")
    assert prompt.index("CURRENT MEDICATIONS") < prompt.index("ALLERGIES")
    assert prompt.index("ALLERGIES") < prompt.index("RISK ASSESSMENT")
    assert prompt.index("RISK ASSESSMENT") < prompt.index("LABORATORY RESULTS")
    assert prompt.index("LABORATORY RESULTS") < prompt.index("CLINICAL SUMMARY")
    assert prompt.index("CLINICAL SUMMARY") < prompt.index("PREVIOUS CONVERSATION")
    assert prompt.index("PREVIOUS CONVERSATION") < prompt.index("USER QUESTION")


def test_complete_prompt_contains_everything(builder, sample_context):
    prompt = builder.build_complete_prompt(
        "Explain findings",
        sample_context,
    )

    assert "AI Clinical Assistant" in prompt
    assert "PATIENT INFORMATION" in prompt
    assert "MEDICAL HISTORY" in prompt
    assert "CURRENT MEDICATIONS" in prompt
    assert "ALLERGIES" in prompt
    assert "RISK ASSESSMENT" in prompt
    assert "LABORATORY RESULTS" in prompt
    assert "CLINICAL SUMMARY" in prompt
    assert "PREVIOUS CONVERSATION" in prompt
    assert "USER QUESTION" in prompt


def test_original_context_not_modified(builder, sample_context):
    original = sample_context["medical_history"][:]

    builder.build_user_prompt(
        "Hello",
        sample_context,
    )

    assert sample_context["medical_history"] == original