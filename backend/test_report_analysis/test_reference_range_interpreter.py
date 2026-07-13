"""
Unit test for ReferenceRangeInterpreter.
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.report_analysis.reference_range_interpreter import (
    ReferenceRangeInterpreter,
)

laboratory_values = {
    "Glucose": {
        "value": 145.0,
        "unit": "mg/dL",
    },
    "Hemoglobin": {
        "value": 11.2,
        "unit": "g/dL",
    },
    "WBC": {
        "value": 8500,
        "unit": "cells/uL",
    },
    "Platelets": {
        "value": 250000,
        "unit": "/uL",
    },
    "Creatinine": {
        "value": 1.1,
        "unit": "mg/dL",
    },
    "Total Cholesterol": {
        "value": 220,
        "unit": "mg/dL",
    },
    "HDL": {
        "value": 45,
        "unit": "mg/dL",
    },
    "LDL": {
        "value": 140,
        "unit": "mg/dL",
    },
    "Triglycerides": {
        "value": 180,
        "unit": "mg/dL",
    },
    "Sodium": {
        "value": 138,
        "unit": "mmol/L",
    },
    "Potassium": {
        "value": 4.2,
        "unit": "mmol/L",
    },
    "TSH": {
        "value": 2.8,
        "unit": "mU/L",
    },
    "Vitamin D": {
        "value": 26,
        "unit": "ng/mL",
    },
}

interpreter = ReferenceRangeInterpreter()

result = interpreter.interpret(laboratory_values)

print("=" * 80)
print("REFERENCE RANGE INTERPRETATION")
print("=" * 80)

for parameter, interpretation in result.items():
    print(parameter)
    print(interpretation)
    print("-" * 80)

print("=" * 80)
print(f"TOTAL PARAMETERS : {len(result)}")
print("=" * 80)