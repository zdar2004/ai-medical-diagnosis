"""
Laboratory Reference Range Interpreter Module.

This module provides the ReferenceRangeInterpreter class for interpreting
laboratory values against standard reference ranges.
"""

from typing import Dict, Any, Optional, Tuple, List
from decimal import Decimal
from app.risk_assessment.utils.logging_utils import get_logger

logger = get_logger(__name__)


class ReferenceRangeInterpreter:
    """
    Interpret laboratory values against reference ranges.

    This class compares extracted laboratory values against standard reference
    ranges to determine if values are normal, high, low, or unknown.
    It maintains an internal reference database of common laboratory parameters.

    Attributes:
        _reference_ranges (Dict[str, Dict[str, Any]]): Reference range database
            containing min, max values and units for each parameter.
    """

    def __init__(self) -> None:
        """Initialize the ReferenceRangeInterpreter with reference ranges."""
        self._reference_ranges = self._load_reference_ranges()

    def interpret(self, laboratory_values: Dict[str, Any]) -> Dict[str, Any]:
        """
        Interpret laboratory values against reference ranges.

        Args:
            laboratory_values (Dict[str, Any]): Dictionary of laboratory values
                with value and unit for each parameter.

        Returns:
            Dict[str, Any]: Dictionary with interpretation results including
                value, unit, status, and reference_range for each parameter.

        Example:
            >>> interpreter = ReferenceRangeInterpreter()
            >>> values = {"Glucose": {"value": 145, "unit": "mg/dL"}}
            >>> result = interpreter.interpret(values)
            >>> print(result)
            {
                "Glucose": {
                    "value": 145,
                    "unit": "mg/dL",
                    "status": "High",
                    "reference_range": "70-99"
                }
            }
        """
        if not laboratory_values:
            logger.warning("Empty laboratory values provided for interpretation")
            return {}

        logger.info("Starting reference range interpretation")
        results: Dict[str, Any] = {}
        total_params = len(laboratory_values)
        unknown_params = 0
        missing_values = 0

        for param_name, value_data in laboratory_values.items():
            if not value_data or "value" not in value_data:
                missing_values += 1
                logger.debug(f"Missing value for parameter: {param_name}")
                continue

            result = self._interpret_parameter(param_name, value_data)
            results[param_name] = result

            if result.get("status") == "Unknown":
                unknown_params += 1
                logger.debug(f"Unknown parameter: {param_name}")
            else:
                logger.debug(f"Interpreted {param_name}: {result['status']}")

        logger.info(f"Interpretation completed. Total parameters: {total_params}")
        logger.debug(f"Unknown parameters: {unknown_params}")
        logger.debug(f"Missing values: {missing_values}")

        return results

    def _load_reference_ranges(self) -> Dict[str, Dict[str, Any]]:
        """
        Load reference ranges for all laboratory parameters.

        Returns:
            Dict[str, Dict[str, Any]]: Reference range database.
        """
        return {
            # CBC Parameters
            "Hemoglobin": {
                "unit": "g/dL",
                "min": 13.5,
                "max": 17.5,
                "reference_range": "13.5-17.5",
                "gender_specific": True,
                "male_min": 13.5,
                "male_max": 17.5,
                "female_min": 12.0,
                "female_max": 16.0
            },
            "RBC": {
                "unit": "x10^6/uL",
                "min": 4.5,
                "max": 5.9,
                "reference_range": "4.5-5.9",
                "gender_specific": True,
                "male_min": 4.7,
                "male_max": 6.1,
                "female_min": 4.2,
                "female_max": 5.4
            },
            "WBC": {
                "unit": "x10^3/uL",
                "min": 4.5,
                "max": 11.0,
                "reference_range": "4.5-11.0"
            },
            "Platelets": {
                "unit": "x10^3/uL",
                "min": 150,
                "max": 400,
                "reference_range": "150-400"
            },
            "Hematocrit": {
                "unit": "%",
                "min": 38.3,
                "max": 48.6,
                "reference_range": "38.3-48.6",
                "gender_specific": True,
                "male_min": 40.7,
                "male_max": 50.3,
                "female_min": 36.1,
                "female_max": 44.3
            },
            "MCV": {
                "unit": "fL",
                "min": 80,
                "max": 100,
                "reference_range": "80-100"
            },
            "MCH": {
                "unit": "pg",
                "min": 27,
                "max": 33,
                "reference_range": "27-33"
            },
            "MCHC": {
                "unit": "g/dL",
                "min": 32,
                "max": 36,
                "reference_range": "32-36"
            },
            # Diabetes Parameters
            "Glucose": {
                "unit": "mg/dL",
                "min": 70,
                "max": 99,
                "reference_range": "70-99"
            },
            "HbA1c": {
                "unit": "%",
                "min": 4.0,
                "max": 5.6,
                "reference_range": "4.0-5.6"
            },
            # Kidney Parameters
            "Creatinine": {
                "unit": "mg/dL",
                "min": 0.7,
                "max": 1.3,
                "reference_range": "0.7-1.3",
                "gender_specific": True,
                "male_min": 0.8,
                "male_max": 1.4,
                "female_min": 0.6,
                "female_max": 1.2
            },
            "Urea": {
                "unit": "mg/dL",
                "min": 7,
                "max": 20,
                "reference_range": "7-20"
            },
            "BUN": {
                "unit": "mg/dL",
                "min": 7,
                "max": 20,
                "reference_range": "7-20"
            },
            "eGFR": {
                "unit": "mL/min/1.73m²",
                "min": 60,
                "max": 120,
                "reference_range": ">60"
            },
            # Liver Parameters
            "ALT": {
                "unit": "U/L",
                "min": 7,
                "max": 56,
                "reference_range": "7-56",
                "gender_specific": True,
                "male_min": 10,
                "male_max": 40,
                "female_min": 7,
                "female_max": 35
            },
            "AST": {
                "unit": "U/L",
                "min": 8,
                "max": 40,
                "reference_range": "8-40",
                "gender_specific": True,
                "male_min": 10,
                "male_max": 40,
                "female_min": 8,
                "female_max": 30
            },
            "Bilirubin": {
                "unit": "mg/dL",
                "min": 0.1,
                "max": 1.2,
                "reference_range": "0.1-1.2"
            },
            "Albumin": {
                "unit": "g/dL",
                "min": 3.4,
                "max": 5.4,
                "reference_range": "3.4-5.4"
            },
            "ALP": {
                "unit": "U/L",
                "min": 44,
                "max": 147,
                "reference_range": "44-147"
            },
            # Lipid Parameters
            "Total Cholesterol": {
                "unit": "mg/dL",
                "min": 125,
                "max": 200,
                "reference_range": "125-200"
            },
            "LDL": {
                "unit": "mg/dL",
                "min": 0,
                "max": 99,
                "reference_range": "<100"
            },
            "HDL": {
                "unit": "mg/dL",
                "min": 40,
                "max": 60,
                "reference_range": "40-60",
                "gender_specific": True,
                "male_min": 40,
                "male_max": 60,
                "female_min": 45,
                "female_max": 65
            },
            "Triglycerides": {
                "unit": "mg/dL",
                "min": 0,
                "max": 150,
                "reference_range": "<150"
            },
            # Electrolytes
            "Sodium": {
                "unit": "mEq/L",
                "min": 136,
                "max": 145,
                "reference_range": "136-145"
            },
            "Potassium": {
                "unit": "mEq/L",
                "min": 3.5,
                "max": 5.1,
                "reference_range": "3.5-5.1"
            },
            "Chloride": {
                "unit": "mEq/L",
                "min": 98,
                "max": 106,
                "reference_range": "98-106"
            },
            # Thyroid Parameters
            "TSH": {
                "unit": "mU/L",
                "min": 0.4,
                "max": 4.0,
                "reference_range": "0.4-4.0"
            },
            "T3": {
                "unit": "ng/dL",
                "min": 80,
                "max": 200,
                "reference_range": "80-200"
            },
            "T4": {
                "unit": "ug/dL",
                "min": 5.0,
                "max": 12.0,
                "reference_range": "5.0-12.0"
            },
            # Vitamin Parameters
            "Vitamin D": {
                "unit": "ng/mL",
                "min": 30,
                "max": 100,
                "reference_range": "30-100"
            },
            "Vitamin B12": {
                "unit": "pg/mL",
                "min": 200,
                "max": 900,
                "reference_range": "200-900"
            }
        }

    def _get_reference(self, param_name: str, value_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Get reference range for a parameter, considering gender if available.

        Args:
            param_name (str): Name of the laboratory parameter.
            value_data (Dict[str, Any]): Value data containing unit and optionally gender.

        Returns:
            Optional[Dict[str, Any]]: Reference range data or None if not found.
        """
        ref = self._reference_ranges.get(param_name)
        if not ref:
            return None

        # Check if gender-specific ranges are needed
        if ref.get("gender_specific", False):
            gender = value_data.get("gender", "").lower()
            if gender in ["male", "m"]:
                return {
                    "unit": ref["unit"],
                    "min": ref.get("male_min", ref["min"]),
                    "max": ref.get("male_max", ref["max"]),
                    "reference_range": ref["reference_range"]
                }
            elif gender in ["female", "f"]:
                return {
                    "unit": ref["unit"],
                    "min": ref.get("female_min", ref["min"]),
                    "max": ref.get("female_max", ref["max"]),
                    "reference_range": ref["reference_range"]
                }

        # Return default ranges
        return {
            "unit": ref["unit"],
            "min": ref["min"],
            "max": ref["max"],
            "reference_range": ref["reference_range"]
        }
    
    def _normalize_value_for_comparison(
        self,
        parameter_name: str,
        value: float,
        unit: str,
    ) -> float:
        """
        Normalize laboratory values to standard units for comparison with reference ranges.

        This method converts values reported in different units to the standard
        units used in the reference range database.

        Args:
            parameter_name (str): Name of the laboratory parameter.
            value (float): Raw laboratory value.
            unit (str): Unit of the laboratory value.

        Returns:
            float: Normalized value suitable for comparison with reference ranges.

        Examples:
            >>> interpreter = ReferenceRangeInterpreter()
            >>> interpreter._normalize_value_for_comparison("WBC", 8500, "cells/uL")
            8.5
            >>> interpreter._normalize_value_for_comparison("WBC", 8.5, "x10^3/uL")
            8.5
            >>> interpreter._normalize_value_for_comparison("Platelets", 250000, "/uL")
            250.0
            >>> interpreter._normalize_value_for_comparison("Platelets", 250, "x10^3/uL")
            250.0
        """
        # WBC normalization: cells/uL to x10^3/uL
        if parameter_name == "WBC":
            # If value > 100, assume it's in cells/uL and convert to x10^3/uL
            if value > 100:
                return value / 1000.0
            # Otherwise assume already in x10^3/uL
            return value

        # Platelets normalization: cells/uL to x10^3/uL
        if parameter_name == "Platelets":
            # If value > 1000, assume it's in cells/uL and convert to x10^3/uL
            if value > 1000:
                return value / 1000.0
            # Otherwise assume already in x10^3/uL
            return value

        # RBC normalization: cells/uL to x10^6/uL
        if parameter_name == "RBC":
            # If value > 1000, assume it's in cells/uL and convert to x10^6/uL
            if value > 1000:
                return value / 1_000_000.0
            # Otherwise assume already in x10^6/uL
            return value

        # All other parameters: no normalization
        return value

    def _interpret_parameter(self, param_name: str, value_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Interpret a single parameter.

        Args:
            param_name (str): Name of the parameter.
            value_data (Dict[str, Any]): Value data with value and optional unit.

        Returns:
            Dict[str, Any]: Interpretation result.
        """
        try:
            value = float(value_data["value"])
            unit = value_data.get("unit", "")

            ref = self._get_reference(param_name, value_data)
            if not ref:
                logger.debug(f"No reference range found for {param_name}")
                return self._build_result(value, unit, "Unknown", None)

            # Pass param_name and unit to _compare_value for normalization
            status = self._compare_value(value, ref, param_name, unit)
            return self._build_result(value, unit, status, ref["reference_range"])

        except (ValueError, TypeError, KeyError) as e:
            logger.error(f"Error interpreting {param_name}: {str(e)}")
            return {
                "value": value_data.get("value"),
                "unit": value_data.get("unit", ""),
                "status": "Unknown",
                "reference_range": None
            }
    def _compare_value(self, value: float, ref: Dict[str, Any], 
                       param_name: str = "", unit: str = "") -> str:
        """
        Compare value against reference range with appropriate normalization.

        Args:
            value (float): Laboratory value to compare.
            ref (Dict[str, Any]): Reference range data.
            param_name (str): Name of the parameter for normalization.
            unit (str): Unit of the value for normalization.

        Returns:
            str: Status - "Normal", "High", "Low", or "Unknown".
        """
        min_val = ref.get("min")
        max_val = ref.get("max")

        if min_val is None or max_val is None:
            return "Unknown"

        # Normalize the value before comparison
        normalized_value = self._normalize_value_for_comparison(param_name, value, unit)

        if self._is_normal(normalized_value, min_val, max_val):
            return "Normal"
        elif self._is_high(normalized_value, max_val):
            return "High"
        elif self._is_low(normalized_value, min_val):
            return "Low"
        else:
            return "Unknown"

    def _is_normal(self, value: float, min_val: float, max_val: float) -> bool:
        """
        Check if value is within normal range.

        Args:
            value (float): Value to check.
            min_val (float): Minimum normal value.
            max_val (float): Maximum normal value.

        Returns:
            bool: True if value is within normal range.
        """
        return min_val <= value <= max_val

    def _is_high(self, value: float, max_val: float) -> bool:
        """
        Check if value is above normal range.

        Args:
            value (float): Value to check.
            max_val (float): Maximum normal value.

        Returns:
            bool: True if value is above normal range.
        """
        return value > max_val

    def _is_low(self, value: float, min_val: float) -> bool:
        """
        Check if value is below normal range.

        Args:
            value (float): Value to check.
            min_val (float): Minimum normal value.

        Returns:
            bool: True if value is below normal range.
        """
        return value < min_val

    def _build_result(self, value: float, unit: str, status: str,
                     reference_range: Optional[str]) -> Dict[str, Any]:
        """
        Build the result dictionary for a parameter.

        Args:
            value (float): Laboratory value.
            unit (str): Unit of measurement.
            status (str): Interpretation status.
            reference_range (Optional[str]): Reference range string.

        Returns:
            Dict[str, Any]: Formatted result dictionary.
        """
        result = {
            "value": value,
            "unit": unit,
            "status": status
        }

        if reference_range:
            result["reference_range"] = reference_range

        return result