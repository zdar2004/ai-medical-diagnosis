"""
Abnormal Findings Detection Module.

This module provides the AbnormalFindingDetector class for identifying and
reporting abnormal laboratory findings based on interpreted results.
"""

from typing import Dict, Any, List, Optional
from decimal import Decimal
from app.risk_assessment.utils.logging_utils import get_logger

logger = get_logger(__name__)


class AbnormalFindingDetector:
    """
    Detect and report abnormal laboratory findings.

    This class processes interpreted laboratory results and generates structured
    abnormal findings for parameters with High or Low status. It calculates
    severity levels based on deviation from reference ranges and generates
    professional, non-diagnostic messages.

    Attributes:
        _severity_thresholds (Dict[str, Dict[str, float]]): Thresholds for
            determining severity levels based on percentage deviation.
        _message_templates (Dict[str, str]): Templates for generating
            professional messages for abnormal findings.
    """

    def __init__(self) -> None:
        """Initialize the AbnormalFindingDetector with severity thresholds."""
        self._severity_thresholds = self._load_severity_thresholds()
        self._message_templates = self._load_message_templates()

    def detect(
        self,
        interpreted_results: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Detect abnormal findings from interpreted laboratory results.

        Args:
            interpreted_results (Dict[str, Any]): Dictionary of interpreted
                laboratory results with status, value, unit, and reference_range.

        Returns:
            Dict[str, Any]: Dictionary containing abnormal findings and summary statistics.

        Example:
            >>> detector = AbnormalFindingDetector()
            >>> results = {
            ...     "Glucose": {
            ...         "value": 145,
            ...         "unit": "mg/dL",
            ...         "status": "High",
            ...         "reference_range": "70-99"
            ...     }
            ... }
            >>> findings = detector.detect(results)
            >>> print(findings)
            [{
                "parameter": "Glucose",
                "value": 145,
                "unit": "mg/dL",
                "status": "High",
                "severity": "Moderate",
                "reference_range": "70-99",
                "message": "Glucose level is above the normal reference range."
            }]
        """
        if not interpreted_results:
            logger.warning("Empty interpreted results provided for detection")
            return {
                "abnormal_findings": [],
                "total_abnormal": 0,
                "has_abnormality": False
            }

        logger.info("Starting abnormal findings detection")
        findings: List[Dict[str, Any]] = []
        ignored_normal = 0

        for param_name, result in interpreted_results.items():
            if not self._should_include(result):
                ignored_normal += 1
                logger.debug(f"Ignored normal/unknown parameter: {param_name}")
                continue

            finding = self._build_finding(param_name, result)
            if finding:
                findings.append(finding)
                logger.debug(f"Abnormal finding detected: {param_name} - {finding['severity']}")

        total_findings = len(findings)

        logger.info(
            "Detection completed. Total findings: %d",
            total_findings,
        )

        logger.debug(
            "Ignored normal parameters: %d",
            ignored_normal,
        )

        return {
            "abnormal_findings": findings,
            "total_abnormal": total_findings,
            "has_abnormality": total_findings > 0,
        }

    def _load_severity_thresholds(self) -> Dict[str, Dict[str, float]]:
        """
        Load severity thresholds based on percentage deviation.

        Returns:
            Dict[str, Dict[str, float]]: Severity thresholds configuration.
        """
        return {
            "High": {
                "critical": 50.0,    # 50% above maximum
                "high": 25.0,        # 25% above maximum
                "moderate": 10.0,    # 10% above maximum
                "low": 0.0          # Below 10% above maximum
            },
            "Low": {
                "critical": 50.0,    # 50% below minimum
                "high": 25.0,        # 25% below minimum
                "moderate": 10.0,    # 10% below minimum
                "low": 0.0          # Below 10% below minimum
            }
        }

    def _load_message_templates(self) -> Dict[str, str]:
        """
        Load professional message templates for abnormal findings.

        Returns:
            Dict[str, str]: Message templates for different status types.
        """
        return {
            "High": "{parameter} level is above the normal reference range.",
            "Low": "{parameter} level is below the normal reference range.",
            "High_generic": "{parameter} level exceeds the expected reference interval.",
            "Low_generic": "{parameter} level is below the expected reference interval."
        }

    def _should_include(self, result: Dict[str, Any]) -> bool:
        """
        Determine if a result should be included in abnormal findings.

        Args:
            result (Dict[str, Any]): Interpreted result for a parameter.

        Returns:
            bool: True if result should be included, False otherwise.
        """
        status = result.get("status", "")
        if status not in ["High", "Low"]:
            return False

        # Ensure value and reference_range exist
        if "value" not in result or "reference_range" not in result:
            return False

        return True

    def _calculate_deviation(self, value: float, reference_range: str) -> Optional[float]:
        """
        Calculate percentage deviation from reference range.

        Args:
            value (float): Laboratory value.
            reference_range (str): Reference range string (e.g., "70-99").

        Returns:
            Optional[float]: Percentage deviation from reference range.
        """
        try:
            # Parse reference range
            if '-' in reference_range:
                min_val, max_val = reference_range.split('-')
                min_val = float(min_val.strip())
                max_val = float(max_val.strip())
            elif '<' in reference_range:
                # Handle ranges like "<100"
                max_val = float(reference_range.replace('<', '').strip())
                min_val = 0.0
            elif '>' in reference_range:
                # Handle ranges like ">60"
                min_val = float(reference_range.replace('>', '').strip())
                max_val = float('inf')
            else:
                return None

            # Calculate deviation
            if value < min_val:
                # Low value - calculate percentage below minimum
                if min_val > 0:
                    deviation = ((min_val - value) / min_val) * 100
                else:
                    deviation = float('inf')
            elif value > max_val:
                # High value - calculate percentage above maximum
                if max_val > 0:
                    deviation = ((value - max_val) / max_val) * 100
                else:
                    deviation = float('inf')
            else:
                deviation = 0.0

            return deviation

        except (ValueError, TypeError, AttributeError):
            logger.warning(f"Failed to parse reference range: {reference_range}")
            return None

    def _determine_severity(self, status: str, deviation: Optional[float]) -> str:
        """
        Determine severity level based on deviation from reference range.

        Args:
            status (str): Parameter status ("High" or "Low").
            deviation (Optional[float]): Percentage deviation from reference range.

        Returns:
            str: Severity level - "Critical", "High", "Moderate", "Low", or "Unknown".
        """
        if deviation is None:
            return "Moderate"  # Default severity for valid abnormalities

        thresholds = self._severity_thresholds.get(status, {})
        abs_deviation = abs(deviation)

        if abs_deviation >= thresholds.get("critical", float('inf')):
            return "Critical"
        elif abs_deviation >= thresholds.get("high", float('inf')):
            return "High"
        elif abs_deviation >= thresholds.get("moderate", float('inf')):
            return "Moderate"
        elif abs_deviation >= thresholds.get("low", float('inf')):
            return "Low"
        else:
            return "Moderate"

    def _build_message(self, parameter: str, status: str, severity: str) -> str:
        """
        Build a professional message for an abnormal finding.

        Args:
            parameter (str): Name of the laboratory parameter.
            status (str): Parameter status ("High" or "Low").
            severity (str): Severity level.

        Returns:
            str: Professional message describing the abnormality.
        """
        # Use status-specific template
        template = self._message_templates.get(status)

        if not template:
            template = self._message_templates.get(f"{status}_generic")

        if not template:
            # Fallback generic message
            template = "{parameter} level is outside the normal reference range."

        message = template.format(parameter=parameter)

        # Add severity context for critical findings
        if severity in ["Critical", "High"]:
            message = f"{message} ({severity} severity)"

        return message

    def _build_finding(self, param_name: str, result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Build a finding dictionary for an abnormal parameter.

        Args:
            param_name (str): Name of the parameter.
            result (Dict[str, Any]): Interpreted result for the parameter.

        Returns:
            Optional[Dict[str, Any]]: Finding dictionary or None if invalid.
        """
        try:
            value = result.get("value")
            unit = result.get("unit", "")
            status = result.get("status", "")
            reference_range = result.get("reference_range", "")

            # Validate required fields
            if value is None or not status:
                return None

            # Calculate deviation and determine severity
            deviation = self._calculate_deviation(float(value), reference_range)
            severity = self._determine_severity(status, deviation)

            # Build professional message
            message = self._build_message(param_name, status, severity)

            # Construct finding
            finding = {
                "parameter": param_name,
                "value": value,
                "unit": unit,
                "status": status,
                "severity": severity,
                "reference_range": reference_range,
                "message": message
            }

            return finding

        except (ValueError, TypeError, KeyError) as e:
            logger.error(f"Error building finding for {param_name}: {str(e)}")
            return None

    def _filter_normal_values(self, interpreted_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Filter out normal and unknown values from interpreted results.

        Args:
            interpreted_results (Dict[str, Any]): All interpreted results.

        Returns:
            Dict[str, Any]: Filtered results containing only abnormal values.
        """
        filtered = {}
        for param_name, result in interpreted_results.items():
            status = result.get("status", "")
            if status in ["High", "Low"]:
                filtered[param_name] = result

        return filtered