"""
Clinical Insights Generator Module.

This module provides the ClinicalInsightsGenerator class for generating
structured clinical observations from laboratory results and findings.
"""

from typing import Dict, Any, List, Optional, Set
from datetime import datetime
from collections import defaultdict
from enum import Enum
from app.risk_assessment.utils.logging_utils import get_logger

logger = get_logger(__name__)


class Priority(Enum):
    """Priority levels for clinical insights."""
    CRITICAL = "Critical"
    HIGH = "High"
    MODERATE = "Moderate"
    LOW = "Low"
    INFORMATIONAL = "Informational"


class ClinicalInsightsGenerator:
    """
    Generate structured clinical insights from laboratory data.

    This class processes interpreted laboratory results, abnormal findings,
    and clinical summaries to produce structured, factual clinical observations.
    It prioritizes findings and generates professional, non-diagnostic insights.

    Attributes:
        _insight_templates (Dict[str, Dict[str, str]]): Templates for generating
            insights based on parameter status.
        _priority_mapping (Dict[str, Priority]): Mapping of severity to priority.
        _duplicate_threshold (float): Threshold for considering insights duplicates.
    """

    def __init__(self, duplicate_threshold: float = 0.8) -> None:
        """
        Initialize the ClinicalInsightsGenerator.

        Args:
            duplicate_threshold (float): Threshold for similarity (0.0-1.0)
                to consider insights as duplicates.
        """
        self._duplicate_threshold = duplicate_threshold
        self._insight_templates = self._load_insight_templates()
        self._priority_mapping = self._load_priority_mapping()
        logger.info("ClinicalInsightsGenerator initialized")

    def generate(
        self,
        interpreted_results: Dict[str, Any],
        abnormal_findings: List[Dict[str, Any]],
        clinical_summary: str
    ) -> Dict[str, Any]:
        """
        Generate clinical insights from laboratory data.

        Args:
            interpreted_results (Dict[str, Any]): Interpreted laboratory results.
            abnormal_findings (List[Dict[str, Any]]): List of abnormal findings.
            clinical_summary (str): AI-generated clinical summary.

        Returns:
            Dict[str, Any]: Dictionary containing insights, review_required flag,
                and generation timestamp.

        Example:
            >>> generator = ClinicalInsightsGenerator()
            >>> insights = generator.generate(
            ...     interpreted_results={"Glucose": {"status": "High"}},
            ...     abnormal_findings=[{"parameter": "Glucose", "severity": "Moderate"}],
            ...     clinical_summary="Elevated glucose levels detected..."
            ... )
            >>> print(insights["insights"][0]["title"])
            "Elevated Blood Glucose"
        """
        logger.info("Starting clinical insights generation")

        insights: List[Dict[str, Any]] = []

        # Generate insights from abnormal findings
        if abnormal_findings:
            finding_insights = self._generate_insights_from_findings(abnormal_findings)
            insights.extend(finding_insights)
            logger.debug(f"Generated {len(finding_insights)} insights from abnormal findings")

        # Generate insights from interpreted results
        if interpreted_results:
            result_insights = self._generate_insights_from_results(interpreted_results)
            insights.extend(result_insights)
            logger.debug(f"Generated {len(result_insights)} insights from interpreted results")

        # Remove duplicates
        unique_insights = self._remove_duplicates(insights)
        logger.debug(f"Removed {len(insights) - len(unique_insights)} duplicate insights")

        # Sort by priority
        sorted_insights = self._sort_by_priority(unique_insights)
        logger.debug(f"Sorted {len(sorted_insights)} insights by priority")

        # Determine if review is required
        review_required = self._determine_review_required(sorted_insights)

        # Build result
        result = {
            "insights": sorted_insights,
            "review_required": review_required,
            "generated_at": datetime.utcnow().isoformat()
        }

        logger.info(f"Clinical insights generation completed. Total insights: {len(sorted_insights)}")
        return result

    def _load_insight_templates(self) -> Dict[str, Dict[str, str]]:
        """
        Load templates for generating insights.

        Returns:
            Dict[str, Dict[str, str]]: Templates for different parameter statuses.
        """
        return {
            "High": {
                "title": "Elevated {parameter}",
                "description": "{parameter} level is above the reference interval.",
                "observation": "Laboratory analysis reveals elevated {parameter}."
            },
            "Low": {
                "title": "Reduced {parameter}",
                "description": "{parameter} level is below the expected range.",
                "observation": "Laboratory analysis reveals reduced {parameter}."
            },
            "Critical_High": {
                "title": "Critically Elevated {parameter}",
                "description": "{parameter} level is significantly above the reference interval.",
                "observation": "Critical elevation of {parameter} detected."
            },
            "Critical_Low": {
                "title": "Critically Reduced {parameter}",
                "description": "{parameter} level is significantly below the expected range.",
                "observation": "Critical reduction of {parameter} detected."
            }
        }

    def _load_priority_mapping(self) -> Dict[str, Priority]:
        """
        Load mapping of severity to priority.

        Returns:
            Dict[str, Priority]: Mapping of severity levels to priorities.
        """
        return {
            "Critical": Priority.CRITICAL,
            "High": Priority.HIGH,
            "Moderate": Priority.MODERATE,
            "Low": Priority.LOW,
            "Unknown": Priority.INFORMATIONAL
        }

    def _generate_insights_from_findings(
        self,
        abnormal_findings: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate insights from abnormal findings.

        Args:
            abnormal_findings (List[Dict[str, Any]]): List of abnormal findings.

        Returns:
            List[Dict[str, Any]]: List of generated insights.
        """
        insights = []

        for finding in abnormal_findings:
            param = finding.get("parameter", "")
            status = finding.get("status", "")
            severity = finding.get("severity", "Moderate")

            if not param or not status:
                continue

            insight = self._build_insight_from_finding(param, status, severity, finding)
            if insight:
                insights.append(insight)

        return insights

    def _generate_insights_from_results(
        self,
        interpreted_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate insights from interpreted results.

        Args:
            interpreted_results (Dict[str, Any]): Interpreted laboratory results.

        Returns:
            List[Dict[str, Any]]: List of generated insights.
        """
        insights = []

        for param, result in interpreted_results.items():
            status = result.get("status", "")
            if status not in ["High", "Low"]:
                continue

            # Check if this is already covered by abnormal findings
            # We'll still generate a basic insight to ensure coverage
            insight = self._build_insight_from_result(param, status, result)
            if insight:
                insights.append(insight)

        return insights

    def _build_insight_from_finding(
        self,
        parameter: str,
        status: str,
        severity: str,
        finding: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Build an insight from an abnormal finding.

        Args:
            parameter (str): Name of the parameter.
            status (str): Parameter status (High/Low).
            severity (str): Severity level.
            finding (Dict[str, Any]): The abnormal finding data.

        Returns:
            Optional[Dict[str, Any]]: Generated insight or None.
        """
        # Determine template key
        if severity == "Critical":
            template_key = f"Critical_{status}"
        else:
            template_key = status

        template = self._insight_templates.get(template_key)
        if not template:
            template = self._insight_templates.get(status)
            if not template:
                return None

        # Generate title and description
        title = template["title"].format(parameter=parameter)
        description = template["description"].format(parameter=parameter)

        # Get priority from severity
        priority = self._priority_mapping.get(severity, Priority.MODERATE)

        # Build insight
        insight = {
            "title": title,
            "description": description,
            "priority": priority.value,
            "parameter": parameter,
            "value": finding.get("value"),
            "unit": finding.get("unit", ""),
            "reference_range": finding.get("reference_range", "")
        }

        return insight

    def _build_insight_from_result(
        self,
        parameter: str,
        status: str,
        result: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Build an insight from an interpreted result.

        Args:
            parameter (str): Name of the parameter.
            status (str): Parameter status (High/Low).
            result (Dict[str, Any]): The interpreted result data.

        Returns:
            Optional[Dict[str, Any]]: Generated insight or None.
        """
        template = self._insight_templates.get(status)
        if not template:
            return None

        # Generate title and description
        title = template["title"].format(parameter=parameter)
        description = template["description"].format(parameter=parameter)

        # Assign priority based on status (default moderate)
        priority = Priority.MODERATE

        # Build insight
        insight = {
            "title": title,
            "description": description,
            "priority": priority.value,
            "parameter": parameter,
            "value": result.get("value"),
            "unit": result.get("unit", ""),
            "reference_range": result.get("reference_range", "")
        }

        return insight

    def _remove_duplicates(self, insights: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicate insights based on similarity.

        Args:
            insights (List[Dict[str, Any]]): List of insights.

        Returns:
            List[Dict[str, Any]]: List with duplicates removed.
        """
        if not insights:
            return []

        unique_insights = []
        seen_titles: Set[str] = set()

        for insight in insights:
            title = insight.get("title", "")
            if title in seen_titles:
                continue

            # Check for similar titles
            is_duplicate = False
            for existing in unique_insights:
                existing_title = existing.get("title", "")
                if self._are_similar_titles(title, existing_title):
                    is_duplicate = True
                    break

            if not is_duplicate:
                unique_insights.append(insight)
                seen_titles.add(title)

        return unique_insights

    def _are_similar_titles(self, title1: str, title2: str) -> bool:
        """
        Check if two titles are similar.

        Args:
            title1 (str): First title.
            title2 (str): Second title.

        Returns:
            bool: True if titles are similar.
        """
        # Simple similarity check based on common words
        words1 = set(title1.lower().split())
        words2 = set(title2.lower().split())

        if not words1 or not words2:
            return False

        # Count common words
        common = len(words1.intersection(words2))
        total = len(words1.union(words2))

        if total == 0:
            return False

        similarity = common / total
        return similarity >= self._duplicate_threshold

    def _sort_by_priority(self, insights: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Sort insights by priority (highest first).

        Args:
            insights (List[Dict[str, Any]]): List of insights.

        Returns:
            List[Dict[str, Any]]: Sorted insights.
        """
        priority_order = {
            Priority.CRITICAL.value: 0,
            Priority.HIGH.value: 1,
            Priority.MODERATE.value: 2,
            Priority.LOW.value: 3,
            Priority.INFORMATIONAL.value: 4
        }

        return sorted(
            insights,
            key=lambda x: priority_order.get(x.get("priority", "Moderate"), 2)
        )

    def _determine_review_required(self, insights: List[Dict[str, Any]]) -> bool:
        """
        Determine if physician review is required based on insights.

        Args:
            insights (List[Dict[str, Any]]): List of insights.

        Returns:
            bool: True if review is required.
        """
        if not insights:
            return False

        # Review required if any critical or high priority insights
        for insight in insights:
            priority = insight.get("priority", "")
            if priority in [Priority.CRITICAL.value, Priority.HIGH.value]:
                return True

        # Also review if there are moderate insights
        for insight in insights:
            priority = insight.get("priority", "")
            if priority == Priority.MODERATE.value:
                return True

        return False

    def _validate_output(self, result: Dict[str, Any]) -> bool:
        """
        Validate the generated insights output.

        Args:
            result (Dict[str, Any]): The result dictionary.

        Returns:
            bool: True if validation passes.
        """
        if "insights" not in result:
            logger.warning("Missing 'insights' key in output")
            return False

        if not isinstance(result["insights"], list):
            logger.warning("'insights' must be a list")
            return False

        # Validate each insight
        for insight in result["insights"]:
            if "title" not in insight or "description" not in insight:
                logger.warning("Insight missing required fields")
                return False

            if "priority" not in insight:
                logger.warning("Insight missing priority")
                return False

        return True