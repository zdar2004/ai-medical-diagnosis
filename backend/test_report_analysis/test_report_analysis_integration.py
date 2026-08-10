"""
Integration tests for the entire Medical Report Analysis pipeline.
"""

import unittest
from app.report_analysis.report_cleaner import MedicalReportCleaner
from app.report_analysis.laboratory_value_extractor import LaboratoryValueExtractor
from app.report_analysis.reference_range_interpreter import ReferenceRangeInterpreter
from app.report_analysis.abnormal_finding_detector import AbnormalFindingDetector
from app.report_analysis.clinical_insights_generator import ClinicalInsightsGenerator


class TestMedicalReportAnalysisIntegration(unittest.TestCase):
    """Integration tests for the complete pipeline."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.cleaner = MedicalReportCleaner()
        self.extractor = LaboratoryValueExtractor()
        self.interpreter = ReferenceRangeInterpreter()
        self.detector = AbnormalFindingDetector()
        self.insights_generator = ClinicalInsightsGenerator()

    def test_complete_pipeline(self) -> None:
        """Test the complete pipeline from raw text to insights."""
        # Sample raw report text
        raw_text = """
        Patient Name: John Doe
        DOB: 01/01/1980
        MRN: 123456
        
        Hemoglobin : 11.2 g/dL
        WBC : 9800 /uL
        Platelets : 275000 /uL
        Glucose : 145 mg/dL
        HbA1c : 7.4 %
        Creatinine : 1.6 mg/dL
        BUN : 18 mg/dL
        ALT : 45 U/L
        AST : 35 U/L
        
        ----- Page 1 -----
        End of Report
        """
        
        # Step 1: Clean the text
        cleaned_text = self.cleaner.clean(raw_text)
        self.assertNotIn("Page 1", cleaned_text)
        self.assertNotIn("End of Report", cleaned_text)
        
        # Step 2: Extract laboratory values
        laboratory_values = self.extractor.extract(cleaned_text)
        self.assertIn("Hemoglobin", laboratory_values)
        self.assertIn("Glucose", laboratory_values)
        self.assertIn("Creatinine", laboratory_values)
        
        # Step 3: Interpret results
        interpreted_results = self.interpreter.interpret(laboratory_values)
        self.assertEqual(interpreted_results["Glucose"]["status"], "High")
        self.assertEqual(interpreted_results["Hemoglobin"]["status"], "Low")
        self.assertEqual(interpreted_results["Creatinine"]["status"], "High")
        
        # Step 4: Detect abnormal findings
        abnormal_findings = self.detector.detect(interpreted_results)
        self.assertEqual(len(abnormal_findings), 3)
        
        # Step 5: Generate clinical insights
        insights_result = self.insights_generator.generate(
            interpreted_results,
            abnormal_findings,
            "Clinical summary placeholder"
        )
        
        self.assertIn("insights", insights_result)
        self.assertTrue(len(insights_result["insights"]) > 0)
        self.assertTrue(insights_result["review_required"])

    def test_pipeline_with_all_normal_values(self) -> None:
        """Test pipeline with all normal values."""
        raw_text = """
        Glucose : 85 mg/dL
        Hemoglobin : 15.0 g/dL
        Creatinine : 1.0 mg/dL
        """
        
        # Clean and extract
        cleaned_text = self.cleaner.clean(raw_text)
        laboratory_values = self.extractor.extract(cleaned_text)
        
        # Interpret
        interpreted_results = self.interpreter.interpret(laboratory_values)
        
        # All should be normal
        self.assertEqual(interpreted_results["Glucose"]["status"], "Normal")
        self.assertEqual(interpreted_results["Hemoglobin"]["status"], "Normal")
        self.assertEqual(interpreted_results["Creatinine"]["status"], "Normal")
        
        # Detect findings
        abnormal_findings = self.detector.detect(interpreted_results)
        self.assertEqual(len(abnormal_findings), 0)
        
        # Generate insights
        insights_result = self.insights_generator.generate(
            interpreted_results,
            abnormal_findings,
            "All values normal."
        )
        
        self.assertEqual(len(insights_result["insights"]), 0)
        self.assertFalse(insights_result["review_required"])

    def test_pipeline_with_mixed_findings(self) -> None:
        """Test pipeline with mixed normal and abnormal values."""
        raw_text = """
        Glucose : 145 mg/dL
        Hemoglobin : 15.0 g/dL
        Creatinine : 1.8 mg/dL
        WBC : 7.5 x10^3/uL
        """
        
        # Clean and extract
        cleaned_text = self.cleaner.clean(raw_text)
        laboratory_values = self.extractor.extract(cleaned_text)
        
        # Interpret
        interpreted_results = self.interpreter.interpret(laboratory_values)
        
        # Check statuses
        self.assertEqual(interpreted_results["Glucose"]["status"], "High")
        self.assertEqual(interpreted_results["Hemoglobin"]["status"], "Normal")
        self.assertEqual(interpreted_results["Creatinine"]["status"], "High")
        self.assertEqual(interpreted_results["WBC"]["status"], "Normal")
        
        # Detect findings
        abnormal_findings = self.detector.detect(interpreted_results)
        self.assertEqual(len(abnormal_findings), 2)
        
        # Verify only abnormal parameters are included
        params = [f["parameter"] for f in abnormal_findings]
        self.assertIn("Glucose", params)
        self.assertIn("Creatinine", params)
        self.assertNotIn("Hemoglobin", params)
        self.assertNotIn("WBC", params)

    def test_pipeline_with_complex_report(self) -> None:
        """Test pipeline with a complex multi-parameter report."""
        raw_text = """
        CBC Results:
        Hemoglobin: 11.2 g/dL
        RBC: 4.2 x10^6/uL
        WBC: 9800 /uL
        Platelets: 275000 /uL
        Hematocrit: 35.5 %
        
        Chemistry:
        Glucose: 145 mg/dL
        HbA1c: 7.4 %
        Creatinine: 1.6 mg/dL
        BUN: 18 mg/dL
        
        Liver Panel:
        ALT: 45 U/L
        AST: 35 U/L
        Bilirubin: 1.2 mg/dL
        Albumin: 4.0 g/dL
        """
        
        # Clean and extract
        cleaned_text = self.cleaner.clean(raw_text)
        laboratory_values = self.extractor.extract(cleaned_text)
        
        # All expected parameters should be extracted
        expected_params = [
            "Hemoglobin", "RBC", "WBC", "Platelets", "Hematocrit",
            "Glucose", "HbA1c", "Creatinine", "BUN",
            "ALT", "AST", "Bilirubin", "Albumin"
        ]
        
        for param in expected_params:
            self.assertIn(param, laboratory_values)
        
        # Interpret
        interpreted_results = self.interpreter.interpret(laboratory_values)
        
        # Check some key statuses
        self.assertEqual(interpreted_results["Glucose"]["status"], "High")
        self.assertEqual(interpreted_results["Hemoglobin"]["status"], "Low")
        self.assertEqual(interpreted_results["Creatinine"]["status"], "High")
        self.assertEqual(interpreted_results["HbA1c"]["status"], "High")
        
        # Detect findings
        abnormal_findings = self.detector.detect(interpreted_results)
        
        # Should find multiple abnormalities
        self.assertGreater(len(abnormal_findings), 3)


if __name__ == "__main__":
    unittest.main()