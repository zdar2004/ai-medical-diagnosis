"""
Unit test for LaboratoryValueExtractor.
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.report_analysis.laboratory_value_extractor import (
    LaboratoryValueExtractor,
)

sample_text = """
MEDICAL LAB REPORT

Patient Name: Ali Khan
Age: 45

Glucose: 145 mg/dL
Hemoglobin: 11.2 g/dL
WBC: 8500 cells/uL
Platelets: 250000 /uL
Creatinine: 1.1 mg/dL
Total Cholesterol: 220 mg/dL
HDL: 45 mg/dL
LDL: 140 mg/dL
Triglycerides: 180 mg/dL
Sodium: 138 mmol/L
Potassium: 4.2 mmol/L
TSH: 2.8 mU/L
Vitamin D: 26 ng/mL
"""

extractor = LaboratoryValueExtractor()

result = extractor.extract(sample_text)

print("=" * 70)
print("EXTRACTED LAB VALUES")
print("=" * 70)

for key, value in result.items():
    print(f"{key:20} -> {value}")

print("=" * 70)
print(f"TOTAL PARAMETERS EXTRACTED : {len(result)}")
print("=" * 70)