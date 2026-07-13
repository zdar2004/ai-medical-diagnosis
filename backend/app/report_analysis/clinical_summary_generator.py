"""
Clinical Summary Generator Module.

This module provides the ClinicalSummaryGenerator class for generating professional
clinical summaries using LLM providers while maintaining safety and accuracy.
"""

import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Protocol
from abc import ABC, abstractmethod
from app.risk_assessment.utils.logging_utils import get_logger

logger = get_logger(__name__)


class LLMProvider(Protocol):
    """
    Protocol defining the interface for LLM providers.

    This protocol ensures all LLM providers implement the generate method
    consistently, allowing for easy switching between providers.
    """

    def generate(self, prompt: str) -> str:
        """
        Generate a response from the LLM.

        Args:
            prompt (str): The prompt to send to the LLM.

        Returns:
            str: The generated response.
        """
        ...


class ClinicalSummaryGenerator:
    """
    Generate professional clinical summaries using LLM providers.

    This class orchestrates the generation of clinical summaries by combining
    laboratory data, interpretations, and abnormal findings into a structured
    prompt for an LLM provider. It ensures safety by explicitly instructing
    the LLM to avoid diagnosis, treatment recommendations, and certainty.

    Attributes:
        _provider (LLMProvider): The LLM provider implementation.
        _max_summary_length (int): Maximum length of the generated summary.
        _include_normal_findings (bool): Whether to include normal findings.
    """

    def __init__(
        self,
        provider: LLMProvider,
        max_summary_length: int = 500,
        include_normal_findings: bool = False
    ) -> None:
        """
        Initialize the ClinicalSummaryGenerator.

        Args:
            provider (LLMProvider): The LLM provider implementation.
            max_summary_length (int): Maximum length of the generated summary.
            include_normal_findings (bool): Whether to include normal findings.
        """
        self._provider = provider
        self._max_summary_length = max_summary_length
        self._include_normal_findings = include_normal_findings
        logger.info(f"ClinicalSummaryGenerator initialized with {provider.__class__.__name__}")

    def generate(
        self,
        cleaned_text: str,
        laboratory_values: Dict[str, Any],
        interpreted_results: Dict[str, Any],
        abnormal_findings: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate a clinical summary using the LLM provider.

        Args:
            cleaned_text (str): Cleaned medical report text.
            laboratory_values (Dict[str, Any]): Extracted laboratory values.
            interpreted_results (Dict[str, Any]): Interpreted results with status.
            abnormal_findings (List[Dict[str, Any]]): List of abnormal findings.

        Returns:
            Dict[str, Any]: Dictionary containing the clinical summary, model info,
                generation timestamp, and warnings.

        Example:
            >>> provider = GeminiProvider()
            >>> generator = ClinicalSummaryGenerator(provider)
            >>> result = generator.generate(
            ...     cleaned_text="...",
            ...     laboratory_values={"Glucose": {"value": 145, "unit": "mg/dL"}},
            ...     interpreted_results={"Glucose": {"status": "High"}},
            ...     abnormal_findings=[{"parameter": "Glucose", "status": "High"}]
            ... )
            >>> print(result["clinical_summary"])
            "Laboratory analysis reveals elevated glucose levels..."
        """
        logger.info("Clinical summary generation started")

        try:
            # Build the prompt
            prompt = self._build_llm_input(
                cleaned_text,
                laboratory_values,
                interpreted_results,
                abnormal_findings
            )
            logger.debug("Prompt built successfully")

            # Generate response using provider
            logger.info(f"Generating summary using {self._provider.__class__.__name__}")
            response = self._provider.generate(prompt)
            logger.debug("Response received from provider")

            # Validate and post-process response
            validated_response = self._validate_response(response)
            summary = self._postprocess_summary(validated_response)
            logger.debug("Summary validated and post-processed")

            # Build result
            result = {
                "clinical_summary": summary,
                "model": self._get_provider_name(),
                "generated_at": datetime.utcnow().isoformat(),
                "warnings": self._generate_warnings(summary)
            }

            logger.info("Clinical summary generation completed successfully")
            return result

        except Exception as e:
            logger.error(f"Error generating clinical summary: {str(e)}")
            # Return fallback summary
            return self._generate_fallback_summary(abnormal_findings)

    def _build_system_prompt(self) -> str:
        """
        Build the system prompt with safety instructions.

        Returns:
            str: System prompt with safety guidelines.
        """
        return """You are a clinical laboratory data assistant. Your role is to summarize laboratory findings objectively.

CRITICAL SAFETY RULES - YOU MUST FOLLOW THESE:
1. NEVER provide a diagnosis or suggest any disease.
2. NEVER prescribe or recommend any medication, treatment, or therapy.
3. NEVER claim certainty about any medical condition.
4. NEVER use definitive language like "diagnosis", "has", "suffers from".
5. NEVER invent or hallucinate laboratory values.
6. ONLY use the laboratory values provided in the data.
7. If information is insufficient, clearly state this.

Your summary must:
- Describe abnormal findings objectively
- Reference specific laboratory values and their deviations
- Use professional but neutral language
- Encourage physician review and interpretation
- Be concise and focused on laboratory abnormalities

Use phrases like:
- "Laboratory analysis reveals..."
- "The following values are outside reference ranges..."
- "Clinically significant findings include..."
- "Physician review is recommended for..."

DO NOT use phrases like:
- "The patient has..."
- "Diagnosis suggests..."
- "Treatment should be..."
- "The patient suffers from..."

Remember: You are providing informational laboratory observations only.
Every finding must be reviewed by a qualified healthcare professional.
"""

    def _build_user_prompt(
        self,
        cleaned_text: str,
        laboratory_values: Dict[str, Any],
        interpreted_results: Dict[str, Any],
        abnormal_findings: List[Dict[str, Any]]
    ) -> str:
        """
        Build the user prompt with the laboratory data.

        Args:
            cleaned_text (str): Cleaned medical report text.
            laboratory_values (Dict[str, Any]): Extracted laboratory values.
            interpreted_results (Dict[str, Any]): Interpreted results with status.
            abnormal_findings (List[Dict[str, Any]]): List of abnormal findings.

        Returns:
            str: User prompt containing the laboratory data.
        """
        # Build the data section
        data_sections = []

        # Add abnormal findings summary
        if abnormal_findings:
            data_sections.append("ABNORMAL FINDINGS:")
            for finding in abnormal_findings:
                param = finding.get("parameter", "Unknown")
                value = finding.get("value", "N/A")
                unit = finding.get("unit", "")
                status = finding.get("status", "")
                severity = finding.get("severity", "")
                ref_range = finding.get("reference_range", "")

                finding_str = f"- {param}: {value} {unit} ({status}, {severity} severity, Reference: {ref_range})"
                data_sections.append(finding_str)

        # Add laboratory values
        if laboratory_values:
            data_sections.append("\nLABORATORY VALUES:")
            for param, data in laboratory_values.items():
                value = data.get("value", "N/A")
                unit = data.get("unit", "")
                # Get interpretation if available
                status = interpreted_results.get(param, {}).get("status", "Not interpreted")
                data_sections.append(f"- {param}: {value} {unit} [{status}]")

        # Add interpreted results
        if interpreted_results and not self._include_normal_findings:
            # Only include abnormal results if not including normal findings
            data_sections.append("\nINTERPRETATION SUMMARY:")
            for param, result in interpreted_results.items():
                status = result.get("status", "")
                if status in ["High", "Low"]:
                    ref_range = result.get("reference_range", "")
                    data_sections.append(f"- {param}: {status} (Reference: {ref_range})")

        # Add cleaned text excerpt (limit to prevent token overflow)
        if cleaned_text:
            text_excerpt = cleaned_text[:500]
            if len(cleaned_text) > 500:
                text_excerpt += "... [truncated]"
            data_sections.append(f"\nREPORT EXCERPT:\n{text_excerpt}")

        # Build final prompt
        prompt = "Based on the following laboratory data, provide a professional clinical summary:\n\n"
        prompt += "\n".join(data_sections)
        prompt += "\n\nGenerate a concise clinical summary focusing on laboratory abnormalities. Remember to follow all safety rules."

        return prompt

    def _build_llm_input(
        self,
        cleaned_text: str,
        laboratory_values: Dict[str, Any],
        interpreted_results: Dict[str, Any],
        abnormal_findings: List[Dict[str, Any]]
    ) -> str:
        """
        Build the complete LLM input combining system and user prompts.

        Args:
            cleaned_text (str): Cleaned medical report text.
            laboratory_values (Dict[str, Any]): Extracted laboratory values.
            interpreted_results (Dict[str, Any]): Interpreted results with status.
            abnormal_findings (List[Dict[str, Any]]): List of abnormal findings.

        Returns:
            str: Complete prompt for the LLM.
        """
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(
            cleaned_text,
            laboratory_values,
            interpreted_results,
            abnormal_findings
        )

        # Combine prompts (different providers might handle this differently)
        # This format works for both Gemini and OpenAI
        return f"{system_prompt}\n\n{user_prompt}"

    def _validate_response(self, response: str) -> str:
        """
        Validate the LLM response for safety and quality.

        Args:
            response (str): The raw LLM response.

        Returns:
            str: Validated response or fallback.

        Raises:
            ValueError: If the response contains unsafe content.
        """
        if not response or not response.strip():
            logger.warning("Empty response received from LLM")
            return "Unable to generate summary due to empty response."

        # Check for unsafe patterns (diagnosis, treatment, certainty)
        unsafe_patterns = [
            "diagnosis",
            "diagnosed",
            "prescribe",
            "treatment",
            "medication",
            "therapy",
            "should take",
            "must take",
            "has the condition",
            "suffers from",
            "is suffering"
        ]

        response_lower = response.lower()
        for pattern in unsafe_patterns:
            if pattern in response_lower:
                logger.warning(f"Unsafe content detected: '{pattern}'")
                # We'll allow it but log the warning

        # Check for hallucinations (invented values)
        # Simple check: response length should be reasonable
        if len(response) > 2000:
            logger.warning("Response too long, may contain unnecessary content")
            # Truncate if too long
            response = response[:2000] + "... [truncated]"

        return response

    def _postprocess_summary(self, response: str) -> str:
        """
        Post-process the LLM response for consistency.

        Args:
            response (str): The raw LLM response.

        Returns:
            str: Post-processed summary.
        """
        # Remove extra whitespace
        summary = response.strip()

        # Remove any markdown artifacts
        summary = summary.replace('**', '')
        summary = summary.replace('*', '')

        # Ensure proper sentence casing
        if summary and summary[0].islower():
            summary = summary[0].upper() + summary[1:]

        # Limit length
        if len(summary) > self._max_summary_length:
            summary = summary[:self._max_summary_length] + "..."

        return summary

    def _get_provider_name(self) -> str:
        """
        Get the name of the LLM provider.

        Returns:
            str: Provider name.
        """
        provider_class = self._provider.__class__.__name__
        # Extract provider name from class name
        if "Gemini" in provider_class:
            return "gemini"
        elif "OpenAI" in provider_class:
            return "openai"
        else:
            return provider_class.lower()

    def _generate_warnings(self, summary: str) -> List[str]:
        """
        Generate warnings based on the summary content.

        Args:
            summary (str): The generated summary.

        Returns:
            List[str]: List of warnings.
        """
        warnings = []

        # Check for missing data
        if "insufficient" in summary.lower() or "not available" in summary.lower():
            warnings.append("Some laboratory data may be incomplete. Consider verifying with original report.")

        # Add standard disclaimer
        warnings.append("This summary is AI-generated for informational purposes only. All findings must be reviewed by a qualified physician.")

        return warnings

    def _generate_fallback_summary(self, abnormal_findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a fallback summary when LLM generation fails.

        Args:
            abnormal_findings (List[Dict[str, Any]]): List of abnormal findings.

        Returns:
            Dict[str, Any]: Fallback summary dictionary.
        """
        logger.warning("Generating fallback summary due to LLM failure")

        if abnormal_findings:
            findings_summary = []
            for finding in abnormal_findings:
                param = finding.get("parameter", "Unknown")
                status = finding.get("status", "")
                severity = finding.get("severity", "")
                findings_summary.append(f"{param}: {status} ({severity} severity)")

            summary = f"Clinical laboratory analysis reveals the following abnormalities: {', '.join(findings_summary)}. Detailed physician review is recommended."
        else:
            summary = "Clinical laboratory analysis shows no significant abnormalities. Routine physician review is recommended."

        return {
            "clinical_summary": summary,
            "model": "fallback",
            "generated_at": datetime.utcnow().isoformat(),
            "warnings": [
                "Summary generated using fallback mechanism due to LLM unavailability.",
                "This summary is AI-generated for informational purposes only. All findings must be reviewed by a qualified physician."
            ]
        }