import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.report_analysis.clinical_insights_generator import (
    ClinicalInsightsGenerator,
)

interpreted_results = {
    "Glucose": {
        "value": 145,
        "unit": "mg/dL",
        "status": "High",
        "reference_range": "70-99",
    },
    "Hemoglobin": {
        "value": 11.2,
        "unit": "g/dL",
        "status": "Low",
        "reference_range": "13.5-17.5",
    },
    "Creatinine": {
        "value": 1.0,
        "unit": "mg/dL",
        "status": "Normal",
        "reference_range": "0.7-1.3",
    },
}

abnormal_findings = [
    {
        "parameter": "Glucose",
        "value": 145,
        "unit": "mg/dL",
        "status": "High",
        "severity": "Moderate",
        "reference_range": "70-99",
    },
    {
        "parameter": "Hemoglobin",
        "value": 11.2,
        "unit": "g/dL",
        "status": "Low",
        "severity": "Moderate",
        "reference_range": "13.5-17.5",
    },
]

clinical_summary = (
    "Laboratory analysis reveals elevated glucose levels "
    "and reduced hemoglobin. Physician review is recommended."
)

generator = ClinicalInsightsGenerator()

result = generator.generate(
    interpreted_results=interpreted_results,
    abnormal_findings=abnormal_findings,
    clinical_summary=clinical_summary,
)

print("=" * 80)
print("CLINICAL INSIGHTS")
print("=" * 80)

for idx, insight in enumerate(result["insights"], start=1):
    print(f"\nInsight {idx}")
    print("-" * 40)
    print("Title      :", insight["title"])
    print("Description:", insight["description"])
    print("Priority   :", insight["priority"])
    print("Parameter  :", insight["parameter"])
    print("Value      :", insight["value"], insight["unit"])
    print("Reference  :", insight["reference_range"])

print("\n" + "=" * 80)
print("REVIEW REQUIRED")
print("=" * 80)
print(result["review_required"])

print("\n" + "=" * 80)
print("GENERATED AT")
print("=" * 80)
print(result["generated_at"])