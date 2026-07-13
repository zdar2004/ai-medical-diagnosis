import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.report_analysis.clinical_summary_generator import (
    ClinicalSummaryGenerator,
)


# -------------------------------------------------------
# Mock Provider
# -------------------------------------------------------

class MockLLMProvider:
    def generate(self, prompt: str) -> str:
        return (
            "Laboratory analysis reveals elevated glucose and cholesterol "
            "levels with reduced hemoglobin. These findings should be "
            "reviewed by a qualified physician. This summary does not "
            "constitute a diagnosis."
        )


# -------------------------------------------------------
# Dummy Data
# -------------------------------------------------------

cleaned_text = """
Patient Name: Ali Khan

Glucose: 145 mg/dL
Hemoglobin: 11.2 g/dL
Total Cholesterol: 220 mg/dL
"""

laboratory_values = {
    "Glucose": {
        "value": 145,
        "unit": "mg/dL"
    },
    "Hemoglobin": {
        "value": 11.2,
        "unit": "g/dL"
    },
    "Total Cholesterol": {
        "value": 220,
        "unit": "mg/dL"
    }
}

interpreted_results = {
    "Glucose": {
        "status": "High",
        "reference_range": "70-99"
    },
    "Hemoglobin": {
        "status": "Low",
        "reference_range": "13.5-17.5"
    },
    "Total Cholesterol": {
        "status": "High",
        "reference_range": "125-200"
    }
}

abnormal_findings = [
    {
        "parameter": "Glucose",
        "value": 145,
        "unit": "mg/dL",
        "status": "High",
        "severity": "Moderate",
        "reference_range": "70-99"
    },
    {
        "parameter": "Hemoglobin",
        "value": 11.2,
        "unit": "g/dL",
        "status": "Low",
        "severity": "Moderate",
        "reference_range": "13.5-17.5"
    },
    {
        "parameter": "Total Cholesterol",
        "value": 220,
        "unit": "mg/dL",
        "status": "High",
        "severity": "Moderate",
        "reference_range": "125-200"
    }
]

# -------------------------------------------------------
# Run
# -------------------------------------------------------

provider = MockLLMProvider()

generator = ClinicalSummaryGenerator(provider)

result = generator.generate(
    cleaned_text=cleaned_text,
    laboratory_values=laboratory_values,
    interpreted_results=interpreted_results,
    abnormal_findings=abnormal_findings
)

print("=" * 80)
print("CLINICAL SUMMARY")
print("=" * 80)

print(result["clinical_summary"])

print("\n")

print("=" * 80)
print("MODEL")
print("=" * 80)

print(result["model"])

print("\n")

print("=" * 80)
print("GENERATED AT")
print("=" * 80)

print(result["generated_at"])

print("\n")

print("=" * 80)
print("WARNINGS")
print("=" * 80)

for warning in result["warnings"]:
    print("-", warning)