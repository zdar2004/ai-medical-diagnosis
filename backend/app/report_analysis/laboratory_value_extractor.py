"""
Laboratory Value Extraction Module.

This module provides the LaboratoryValueExtractor class for parsing and extracting
structured laboratory values from cleaned medical report text.
"""

import re
from typing import Dict, Any, Optional, List, Tuple, Pattern
from decimal import Decimal, InvalidOperation
from app.risk_assessment.utils.logging_utils import get_logger

logger = get_logger(__name__)


class LaboratoryValueExtractor:
    """
    Extract structured laboratory values from cleaned medical report text.

    This class parses medical report text to extract laboratory parameters,
    their values, and units. It supports multiple report formats and
    laboratory test types including CBC, Diabetes, Kidney, Liver, Lipid,
    Electrolytes, Thyroid, and Vitamin panels.

    Attributes:
        _parameter_patterns (Dict[str, List[Pattern]]): Compiled regex patterns
            for each laboratory parameter.
        _parameter_aliases (Dict[str, List[str]]): Aliases for parameter names.
        _unit_patterns (Dict[str, Pattern]): Patterns for detecting units.
        _numeric_pattern (Pattern): Pattern for detecting numeric values.
    """

    def __init__(self) -> None:
        """Initialize the LaboratoryValueExtractor with parameter patterns."""
        self._parameter_aliases = self._build_parameter_aliases()
        self._parameter_patterns = self._build_parameter_patterns()
        self._unit_patterns = self._build_unit_patterns()
        self._numeric_pattern = re.compile(
            r'[-+]?(?:\d{1,3}(?:,\d{3})*|\d+)(?:\.\d+)?(?:[eE][-+]?\d+)?'
        )

    def extract(self, text: str) -> Dict[str, Any]:
        """
        Extract structured laboratory values from cleaned medical report text.

        Args:
            text (str): Cleaned medical report text.

        Returns:
            Dict[str, Any]: Dictionary mapping parameter names to their extracted
                values and units.

        Example:
            >>> extractor = LaboratoryValueExtractor()
            >>> text = "Hemoglobin : 11.8 g/dL\\nGlucose : 145 mg/dL"
            >>> result = extractor.extract(text)
            >>> print(result)
            {
                "Hemoglobin": {"value": 11.8, "unit": "g/dL"},
                "Glucose": {"value": 145, "unit": "mg/dL"}
            }
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for extraction")
            return {}

        logger.info("Starting laboratory value extraction")
        results: Dict[str, Any] = {}
        lines = text.splitlines()
        total_params = 0
        ignored_params = 0
        parsing_failures = 0

        for line in lines:
            if not line.strip():
                continue

            extracted = self._process_line(line)
            if extracted:
                param_name = extracted.get("parameter", "")
                if param_name and "value" in extracted:
                    results[param_name] = {
                        "value": extracted["value"],
                        "unit": extracted.get("unit", "")
                    }
                    total_params += 1
                    logger.debug(f"Extracted: {param_name} = {extracted['value']} {extracted.get('unit', '')}")
                else:
                    ignored_params += 1
                    logger.debug(f"Ignored line: {line[:50]}...")
            else:
                parsing_failures += 1
                logger.debug(f"Failed to parse: {line[:50]}...")

        logger.info(f"Extraction completed. Total parameters: {total_params}")
        logger.debug(f"Ignored parameters: {ignored_params}")
        logger.debug(f"Parsing failures: {parsing_failures}")

        return results

    def _build_parameter_aliases(self) -> Dict[str, List[str]]:
        """
        Build parameter aliases mapping.

        Returns:
            Dict[str, List[str]]: Mapping of canonical parameter names to aliases.
        """
        return {
            # CBC
            "Hemoglobin": ["Hb", "HGB", "Hemoglobin", "haemoglobin"],
            "RBC": ["RBC", "Red Blood Cells", "Erythrocytes"],
            "WBC": ["WBC", "White Blood Cells", "Leukocytes"],
            "Platelets": ["PLT", "Platelet Count", "Thrombocytes"],
            "Hematocrit": ["HCT", "Hct", "Packed Cell Volume", "PCV"],
            "MCV": ["MCV", "Mean Corpuscular Volume"],
            "MCH": ["MCH", "Mean Corpuscular Hemoglobin"],
            "MCHC": ["MCHC", "Mean Corpuscular Hemoglobin Concentration"],
            # Diabetes
            "Glucose": ["Glucose", "Blood Sugar", "FBS", "RBS"],
            "HbA1c": ["HbA1c", "Glycated Hemoglobin", "A1C"],
            # Kidney
            "Creatinine": ["Creatinine", "Serum Creatinine"],
            "Urea": ["Urea", "Blood Urea"],
            "BUN": ["BUN", "Blood Urea Nitrogen"],
            "eGFR": ["eGFR", "Estimated GFR"],
            # Liver
            "ALT": ["ALT", "SGPT", "Alanine Aminotransferase"],
            "AST": ["AST", "SGOT", "Aspartate Aminotransferase"],
            "Bilirubin": ["Bilirubin", "Total Bilirubin"],
            "Albumin": ["Albumin", "Serum Albumin"],
            "ALP": ["ALP", "Alkaline Phosphatase"],
            # Lipid
            "Total Cholesterol": ["Total Cholesterol", "Cholesterol"],
            "LDL": ["LDL", "LDL Cholesterol"],
            "HDL": ["HDL", "HDL Cholesterol"],
            "Triglycerides": ["Triglycerides", "TG"],
            # Electrolytes
            "Sodium": ["Sodium", "Na"],
            "Potassium": ["Potassium", "K"],
            "Chloride": ["Chloride", "Cl"],
            # Thyroid
            "TSH": ["TSH", "Thyroid Stimulating Hormone"],
            "T3": ["T3", "Triiodothyronine"],
            "T4": ["T4", "Thyroxine"],
            # Vitamins
            "Vitamin D": ["Vitamin D", "25-OH Vitamin D"],
            "Vitamin B12": ["Vitamin B12", "Cobalamin"],
        }

    def _build_parameter_patterns(self) -> Dict[str, List[Pattern]]:
        """
        Compile regex patterns for parameter detection.

        Returns:
            Dict[str, List[Pattern]]: Compiled regex patterns for each parameter.
        """
        patterns: Dict[str, List[Pattern]] = {}
        
        for param, aliases in self._parameter_aliases.items():
            param_patterns = []
            for alias in aliases:
                # Create pattern that matches parameter with various separators
                pattern_str = r'{}\s*[:=\-–—.]?\s*'.format(re.escape(alias))
                param_patterns.append(re.compile(pattern_str, re.IGNORECASE))
            patterns[param] = param_patterns
        
        return patterns

    def _build_unit_patterns(self) -> Dict[str, Pattern]:
        """
        Build regex patterns for unit detection.

        Returns:
            Dict[str, Pattern]: Patterns for detecting measurement units.
        """
        unit_patterns = {
            r'g/dL': re.compile(r'g/dL', re.IGNORECASE),
            r'mg/dL': re.compile(r'mg/dL', re.IGNORECASE),
            r'/uL': re.compile(r'/uL', re.IGNORECASE),
            r'x10\^?3/uL': re.compile(r'x10\^?3/uL', re.IGNORECASE),
            r'x10\^?3/mm3': re.compile(r'x10\^?3/mm3', re.IGNORECASE),
            r'x10\^?6/uL': re.compile(r'x10\^?6/uL', re.IGNORECASE),
            r'fL': re.compile(r'fL', re.IGNORECASE),
            r'pg': re.compile(r'pg', re.IGNORECASE),
            r'%': re.compile(r'%'),
            r'mmol/L': re.compile(r'mmol/L', re.IGNORECASE),
            r'umol/L': re.compile(r'umol/L', re.IGNORECASE),
            r'mU/L': re.compile(r'mU/L', re.IGNORECASE),
            r'U/L': re.compile(r'U/L', re.IGNORECASE),
            r'IU/L': re.compile(r'IU/L', re.IGNORECASE),
            r'ng/mL': re.compile(r'ng/mL', re.IGNORECASE),
            r'pg/mL': re.compile(r'pg/mL', re.IGNORECASE),
            r'mEq/L': re.compile(r'mEq/L', re.IGNORECASE),
            r'mg/g': re.compile(r'mg/g', re.IGNORECASE),
        }
        
        # Combine all unit patterns into a single pattern
        combined_pattern = r'(' + '|'.join(unit_patterns.keys()) + r')'
        return re.compile(combined_pattern, re.IGNORECASE)

    def _process_line(self, line: str) -> Optional[Dict[str, Any]]:
        """
        Process a single line to extract parameter, value, and unit.

        Args:
            line (str): Single line of text to process.

        Returns:
            Optional[Dict[str, Any]]: Dictionary with parameter, value, and unit
                if extraction successful, None otherwise.
        """
        line = line.strip()
        if not line:
            return None

        # Try to match parameter patterns
        for param_name, patterns in self._parameter_patterns.items():
            for pattern in patterns:
                match = pattern.search(line)
                if match:
                    # Extract the remaining text after the parameter
                    remaining = line[match.end():].strip()
                    if not remaining:
                        continue
                    
                    # Extract value and unit
                    extracted = self._extract_value_and_unit(remaining)
                    if extracted:
                        return {
                            "parameter": param_name,
                            "value": extracted["value"],
                            "unit": extracted.get("unit", "")
                        }

        # Try alternative extraction for lines without clear parameter pattern
        return self._extract_loose_format(line)

    def _extract_value_and_unit(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extract numeric value and unit from text.

        Args:
            text (str): Text containing value and possibly unit.

        Returns:
            Optional[Dict[str, Any]]: Dictionary with value and unit if extraction
                successful, None otherwise.
        """
        # Try to extract unit first
        unit_match = self._unit_patterns.search(text)
        unit = unit_match.group(0) if unit_match else ""
        
        # Remove unit from text for value extraction
        text_without_unit = text.replace(unit, "").strip() if unit else text
        
        # Extract numeric value
        value = self._extract_numeric_value(text_without_unit)
        if value is not None:
            return {
                "value": value,
                "unit": unit
            }
        
        return None

    def _extract_numeric_value(self, text: str) -> Optional[float]:
        """
        Extract numeric value from text.

        Args:
            text (str): Text potentially containing a numeric value.

        Returns:
            Optional[float]: Extracted numeric value or None if not found.
        """
        # Find all numeric patterns
        matches = self._numeric_pattern.findall(text)
        if not matches:
            return None

        # Try to parse the first valid match
        for match in matches:
            try:
                # Remove commas and convert to Decimal for precision
                cleaned = match.replace(',', '')
                value = Decimal(cleaned)
                return float(value)
            except (InvalidOperation, ValueError):
                continue

        return None

    def _extract_loose_format(self, line: str) -> Optional[Dict[str, Any]]:
        """
        Attempt extraction from loosely formatted lines.

        Args:
            line (str): Line to attempt extraction from.

        Returns:
            Optional[Dict[str, Any]]: Extracted data if successful, None otherwise.
        """
        # Pattern for common lab report format: "Parameter Value Unit"
        pattern = re.compile(r'^(.+?)\s+([-+]?(?:\d{1,3}(?:,\d{3})*|\d+)(?:\.\d+)?(?:[eE][-+]?\d+)?)\s+(.+)$')
        match = pattern.match(line)
        if not match:
            return None

        param_part, value_str, unit_part = match.groups()
        param_part = param_part.strip()
        unit_part = unit_part.strip()

        # Try to match parameter part to known parameters
        for param_name, aliases in self._parameter_aliases.items():
            for alias in aliases:
                if alias.lower() in param_part.lower():
                    # Try to parse value
                    try:
                        cleaned_value = value_str.replace(',', '')
                        value = float(Decimal(cleaned_value))
                        return {
                            "parameter": param_name,
                            "value": value,
                            "unit": unit_part
                        }
                    except (InvalidOperation, ValueError):
                        continue

        return None