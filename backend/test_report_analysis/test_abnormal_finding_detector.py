import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.report_analysis.abnormal_finding_detector import (
    AbnormalFindingDetector,
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
    "WBC": {
        "value": 8500,
        "unit": "cells/uL",
        "status": "Normal",
        "reference_range": "4.5-11.0",
    },
    "Creatinine": {
        "value": 1.0,
        "unit": "mg/dL",
        "status": "Normal",
        "reference_range": "0.7-1.3",
    },
    "Vitamin D": {
        "value": 26,
        "unit": "ng/mL",
        "status": "Low",
        "reference_range": "30-100",
    },
}

detector = AbnormalFindingDetector()

result = detector.detect(interpreted_results)

print("=" * 80)
print("ABNORMAL FINDINGS")
print("=" * 80)

for finding in result["abnormal_findings"]:
    print(finding)
    print("-" * 60)

print("=" * 80)
print("TOTAL ABNORMAL :", result["total_abnormal"])
print("HAS ABNORMALITY:", result["has_abnormality"])
print("=" * 80)