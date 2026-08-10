import pytest

from app.ai_clinical_assistant.context_builder import ContextBuilder
from app.ai_clinical_assistant.conversation_memory import ConversationMemory
from app.ai_clinical_assistant.exceptions import ContextBuilderError
from app.ai_clinical_assistant.schemas import ConversationContext


@pytest.fixture
def memory():
    return ConversationMemory()


@pytest.fixture
def builder(memory):
    return ContextBuilder(memory)


@pytest.fixture
def sample_context():
    return ConversationContext(
        patient_id="P001",
        patient_age=35,
        patient_gender="Male",
        medical_history=["Diabetes", "Hypertension"],
        current_medications=["Metformin"],
        allergies=["Penicillin"],
        risk_assessment={
            "risk": "High",
            "score": 0.87,
        },
        laboratory_results={
            "HbA1c": 8.2,
            "Glucose": 190,
        },
        clinical_summary="Patient has uncontrolled diabetes.",
        report_analysis={
            "abnormal": True,
            "findings": "Elevated HbA1c",
        },
    )


def test_build_empty_context(builder):
    result = builder.build_context(None, None)

    assert result == {}


def test_invalid_context_type(builder):
    with pytest.raises(ContextBuilderError):
        builder.build_context(None, {"invalid": "context"})


def test_patient_section(builder, sample_context):
    result = builder.build_context(None, sample_context)

    assert "patient" in result
    assert result["patient"]["patient_id"] == "P001"
    assert result["patient"]["age"] == 35
    assert result["patient"]["gender"] == "Male"


def test_medical_history_section(builder, sample_context):
    result = builder.build_context(None, sample_context)

    assert result["medical_history"] == [
        "Diabetes",
        "Hypertension",
    ]


def test_medications_section(builder, sample_context):
    result = builder.build_context(None, sample_context)

    assert result["medications"] == [
        "Metformin",
    ]


def test_allergies_section(builder, sample_context):
    result = builder.build_context(None, sample_context)

    assert result["allergies"] == [
        "Penicillin",
    ]


def test_risk_assessment_section(builder, sample_context):
    result = builder.build_context(None, sample_context)

    assert result["risk_assessment"]["risk"] == "High"
    assert result["risk_assessment"]["score"] == 0.87


def test_laboratory_section(builder, sample_context):
    result = builder.build_context(None, sample_context)

    assert result["laboratory_results"]["HbA1c"] == 8.2
    assert result["laboratory_results"]["Glucose"] == 190


def test_clinical_summary_section(builder, sample_context):
    result = builder.build_context(None, sample_context)

    assert (
        result["clinical_summary"]
        == "Patient has uncontrolled diabetes."
    )


def test_report_analysis_section(builder, sample_context):
    result = builder.build_context(None, sample_context)

    assert result["report_analysis"]["abnormal"] is True
    assert result["report_analysis"]["findings"] == "Elevated HbA1c"
    
def test_conversation_history_loaded(builder, memory):
    conversation_id = memory.create_conversation()

    memory.add_user_message(conversation_id, "Hello")
    memory.add_assistant_message(conversation_id, "Hi")

    result = builder.build_context(conversation_id, None)

    assert "conversation_history" in result
    assert len(result["conversation_history"]) == 2
    assert result["conversation_history"][0]["role"] == "user"
    assert result["conversation_history"][1]["role"] == "assistant"


def test_conversation_history_empty(builder, memory):
    conversation_id = memory.create_conversation()

    result = builder.build_context(conversation_id, None)

    assert result == {}


def test_invalid_conversation_id(builder):
    result = builder.build_context("invalid-id", None)

    assert result == {}


def test_merge_all_sections(builder, memory, sample_context):
    conversation_id = memory.create_conversation()

    memory.add_user_message(conversation_id, "Question")
    memory.add_assistant_message(conversation_id, "Answer")

    result = builder.build_context(conversation_id, sample_context)

    assert "patient" in result
    assert "medical_history" in result
    assert "medications" in result
    assert "allergies" in result
    assert "risk_assessment" in result
    assert "laboratory_results" in result
    assert "clinical_summary" in result
    assert "report_analysis" in result
    assert "conversation_history" in result


def test_empty_lists_removed(builder):
    context = ConversationContext()

    result = builder.build_context(None, context)

    assert result == {}


def test_partial_context(builder):
    context = ConversationContext(
        patient_id="P100",
        patient_age=40,
    )

    result = builder.build_context(None, context)

    assert result == {
        "patient": {
            "patient_id": "P100",
            "age": 40,
        }
    }


def test_original_context_not_modified(builder, sample_context):
    builder.build_context(None, sample_context)

    assert sample_context.patient_id == "P001"
    assert sample_context.medical_history == [
        "Diabetes",
        "Hypertension",
    ]
    assert sample_context.current_medications == [
        "Metformin",
    ]


def test_history_is_copy(builder, memory):
    conversation_id = memory.create_conversation()

    memory.add_user_message(conversation_id, "Hello")

    result = builder.build_context(conversation_id, None)

    result["conversation_history"].append(
        {
            "role": "user",
            "content": "Fake",
        }
    )

    history = memory.get_recent_messages(conversation_id)

    assert len(history) == 1


def test_conversation_order_preserved(builder, memory):
    conversation_id = memory.create_conversation()

    memory.add_user_message(conversation_id, "One")
    memory.add_assistant_message(conversation_id, "Two")
    memory.add_user_message(conversation_id, "Three")

    result = builder.build_context(conversation_id, None)

    history = result["conversation_history"]

    assert history[0]["content"] == "One"
    assert history[1]["content"] == "Two"
    assert history[2]["content"] == "Three"


def test_recent_messages_limit(builder, memory):
    conversation_id = memory.create_conversation()

    for i in range(20):
        memory.add_user_message(conversation_id, f"Message {i}")

    result = builder.build_context(conversation_id, None)

    history = result["conversation_history"]

    assert len(history) == 10
    assert history[0]["content"] == "Message 10"
    assert history[-1]["content"] == "Message 19"