"""
Gemini-based disease prediction provider.

Uses Gemini to predict the most likely disease from a list of symptoms
and returns the result in PredictionResult format.
"""

from __future__ import annotations

import json

from app.ai.models.prediction_result import PredictionResult
from app.report_analysis.providers.gemini_provider import GeminiProvider


class GeminiPredictionProvider:
    """
    Gemini-powered disease prediction provider.
    """

    def __init__(self) -> None:
        self.provider = GeminiProvider()

    def predict(self, symptoms: list[str]) -> PredictionResult:
        """
        Predict disease using Gemini.

        Args:
            symptoms: List of symptom strings.

        Returns:
            PredictionResult
        """
        symptom_text = "\n".join(f"- {symptom}" for symptom in symptoms)

        prompt = f"""
        You are an experienced clinical diagnostic assistant.

        Based ONLY on the symptoms below, predict the three most likely diseases.

        Symptoms:
        {symptom_text}

        Return ONLY valid JSON.

        {{
        "disease": "Most likely disease",
        "confidence": 85.5,
        "top_predictions": [
            {{
            "disease": "Disease 1",
            "confidence": 85.5
            }},
            {{
            "disease": "Disease 2",
            "confidence": 10.3
            }},
            {{
            "disease": "Disease 3",
            "confidence": 4.2
            }}
        ]
        }}
        """
        print("✅ Using Gemini Prediction Provider...")
        # Generate response from Gemini
        response = self.provider.generate(prompt)
        print(response)
        # Convert Gemini JSON string into Python dictionary
        data = json.loads(response)
        return PredictionResult(
            disease=data["disease"],
            confidence=data["confidence"],
            top_predictions=data["top_predictions"],
        )