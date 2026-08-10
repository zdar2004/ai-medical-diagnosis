"""
report_analysis_service.py
==========================

Medical Report Analysis Orchestration Service.

This module connects all medical report analysis components
into a complete processing pipeline.

Responsibilities
----------------
- Parse medical reports
- Clean extracted text
- Extract laboratory values
- Interpret reference ranges
- Detect abnormal findings
- Generate clinical summary
- Generate clinical insights

This service does NOT:
- Train ML models
- Diagnose diseases
- Prescribe treatment
- Store patient data
"""

from __future__ import annotations

from typing import Any, Dict, List

from app.report_analysis.report_parser import (
    MedicalReportParser,
)
from app.ai_clinical_assistant.provider_factory import ProviderFactory

from app.report_analysis.report_cleaner import (
    MedicalReportCleaner,
)

from app.report_analysis.laboratory_value_extractor import (
    LaboratoryValueExtractor,
)

from app.report_analysis.reference_range_interpreter import (
    ReferenceRangeInterpreter,
)

from app.report_analysis.abnormal_finding_detector import (
    AbnormalFindingDetector,
)

from app.report_analysis.clinical_summary_generator import (
    ClinicalSummaryGenerator,
)

from app.report_analysis.clinical_insights_generator import (
    ClinicalInsightsGenerator,
)

from app.risk_assessment.utils.logging_utils import get_logger


logger = get_logger(__name__)

class MedicalReportAnalysisService:
    """
    Orchestrate the complete medical report analysis pipeline.

    This class acts as the main coordinator between individual
    report analysis components.

    Workflow:

        Report File
            |
            v
        Parser
            |
            v
        Cleaner
            |
            v
        Laboratory Extraction
            |
            v
        Reference Interpretation
            |
            v
        Abnormal Detection
            |
            v
        Clinical Summary
            |
            v
        Clinical Insights
    """

    def __init__(
        self,
        parser: MedicalReportParser | None = None,
        cleaner: MedicalReportCleaner | None = None,
        extractor: LaboratoryValueExtractor | None = None,
        interpreter: ReferenceRangeInterpreter | None = None,
        detector: AbnormalFindingDetector | None = None,
        summary_generator: ClinicalSummaryGenerator | None = None,
        insights_generator: ClinicalInsightsGenerator | None = None,
    ) -> None:
        """
        Initialize Medical Report Analysis Service.

        Dependency injection is used so individual components
        can be replaced or tested independently.

        Args:
            parser:
                Report parser instance.

            cleaner:
                Report cleaner instance.

            extractor:
                Laboratory value extractor.

            interpreter:
                Reference range interpreter.

            detector:
                Abnormal finding detector.

            summary_generator:
                AI clinical summary generator.

            insights_generator:
                Clinical insights generator.
        """
        provider=ProviderFactory().get_provider()
        self.summary_generator = (
            summary_generator
            if summary_generator
            else ClinicalSummaryGenerator(
                provider=provider
            )
        )
        self.parser = (
            parser
            if parser
            else MedicalReportParser()
        )

        self.cleaner = (
            cleaner
            if cleaner
            else MedicalReportCleaner()
        )

        self.extractor = (
            extractor
            if extractor
            else LaboratoryValueExtractor()
        )

        self.interpreter = (
            interpreter
            if interpreter
            else ReferenceRangeInterpreter()
        )

        self.detector = (
            detector
            if detector
            else AbnormalFindingDetector()
        )

        self.insights_generator = (
            insights_generator
            if insights_generator
            else ClinicalInsightsGenerator()
        )

        logger.info(
            "MedicalReportAnalysisService initialized."
        )
        
        # ---------------------------------------------------------
    # Main Analysis Pipeline
    # ---------------------------------------------------------
    
    def analyze_report(
        self,
        file_path: str,
    ) -> Dict[str, Any]:
        """
        Execute complete medical report analysis pipeline.

        Workflow:

            Medical Report File
                    |
                    v
            Text Extraction
                    |
                    v
            Text Cleaning
                    |
                    v
            Laboratory Extraction
                    |
                    v
            Reference Interpretation
                    |
                    v
            Abnormal Detection
                    |
                    v
            Clinical Summary
                    |
                    v
            Clinical Insights


        Args:
            file_path:
                Path of medical report file.

        Returns:
            Dictionary containing complete analysis result.

        Raises:
            Exception:
                If any pipeline stage fails.
        """

        logger.info(
            "Medical report analysis started."
        )

        try:

            # -------------------------------------------------
            # Step 1: Parse Report
            # -------------------------------------------------

            raw_text = self.parser.parse(
                file_path
            )

            logger.info(
                "Report parsing completed."
            )


            # -------------------------------------------------
            # Step 2: Clean Text
            # -------------------------------------------------

            cleaned_text = self.cleaner.clean(
                raw_text
            )

            logger.info(
                "Report cleaning completed."
            )


            # -------------------------------------------------
            # Step 3: Extract Laboratory Values
            # -------------------------------------------------

            laboratory_values = (
                self.extractor.extract(
                    cleaned_text
                )
            )

            logger.info(
                "Laboratory extraction completed."
            )


            # -------------------------------------------------
            # Step 4: Interpret Reference Ranges
            # -------------------------------------------------

            interpreted_values = (
                self.interpreter.interpret(
                    laboratory_values
                )
            )

            logger.info(
                "Reference range interpretation completed."
            )


            # -------------------------------------------------
            # Step 5: Detect Abnormal Findings
            # -------------------------------------------------

            abnormal_result = self.detector.detect(interpreted_values)
            abnormal_findings = abnormal_result["abnormal_findings"]

            logger.info(
                "Abnormal finding detection completed."
            )

            print("\n===== DEBUG abnormal_findings =====")
            print(type(abnormal_findings))
            print(abnormal_findings)
            print(type(abnormal_findings[0]) if abnormal_findings else "EMPTY")
            # -------------------------------------------------
            # Step 6: Generate Clinical Summary
            # -------------------------------------------------

            clinical_summary = self.summary_generator.generate(
                cleaned_text=cleaned_text,
                laboratory_values=laboratory_values,
                interpreted_results=interpreted_values,
                abnormal_findings=abnormal_findings,
            )

            logger.info(
                "Clinical summary generated."
            )


            # -------------------------------------------------
            # Step 7: Generate Clinical Insights
            # -------------------------------------------------

            clinical_insights = self.insights_generator.generate(
                interpreted_results=interpreted_values,
                abnormal_findings=abnormal_findings,
                clinical_summary=clinical_summary["clinical_summary"],
            )

            logger.info(
                "Clinical insights generated."
            )


            # -------------------------------------------------
            # Final Response
            # -------------------------------------------------

            result = {

                "raw_text": raw_text,

                "cleaned_text": cleaned_text,

                "laboratory_values":
                    laboratory_values,

                "interpreted_values":
                    interpreted_values,

                "abnormal_findings":
                    abnormal_findings,

                "clinical_summary":
                    clinical_summary,

                "clinical_insights":
                    clinical_insights,

            }


            logger.info(
                "Medical report analysis completed successfully."
            )


            return self.format_response(
            result
        )


        except Exception as error:

            logger.exception(
                "Medical report analysis failed: %s",
                error,
            )

            raise
        # ---------------------------------------------------------
    # Analyze Uploaded File Bytes
    # ---------------------------------------------------------

    def analyze_bytes(
        self,
        file_data: bytes,
        filename: str,
    ) -> Dict[str, Any]:
        """
        Analyze uploaded medical report bytes.

        This method is designed for FastAPI UploadFile.

        Workflow:

            Uploaded File
                    |
                    v
            Parser Bytes
                    |
                    v
            Cleaning
                    |
                    v
            Analysis Pipeline


        Args:
            file_data:
                Uploaded file bytes.

            filename:
                Original uploaded filename.

        Returns:
            Complete medical report analysis result.
        """

        logger.info(
            "Starting analysis from uploaded file: %s",
            filename,
        )

        try:

            # ---------------------------------------------
            # Validate File
            # ---------------------------------------------

            self._validate_filename(
                filename
            )

            self._validate_file_size(
                file_data
            )


            # ---------------------------------------------
            # Parse Bytes
            # ---------------------------------------------

            raw_text = self.parser.parse_bytes(
                file_data=file_data,
                filename=filename,
            )


            logger.info(
                "Uploaded report parsing completed."
            )


            # ---------------------------------------------
            # Continue Analysis
            # ---------------------------------------------

            result = self._process_text(
                raw_text
            )


            logger.info(
                "Uploaded report analysis completed."
            )


            return self.format_response(
            result
        )


        except Exception as error:

            logger.exception(
                "Uploaded report analysis failed: %s",
                error,
            )

            raise
        # ---------------------------------------------------------
    # Text Processing Pipeline
    # ---------------------------------------------------------

    def _process_text(
        self,
        raw_text: str,
    ) -> Dict[str, Any]:
        """
        Process extracted medical report text.

        Args:
            raw_text:
                Extracted report text.

        Returns:
            Structured analysis result.
        """

        cleaned_text = self.cleaner.clean(
            raw_text
        )


        laboratory_values = (
            self.extractor.extract(
                cleaned_text
            )
        )


        interpreted_values = (
            self.interpreter.interpret(
                laboratory_values
            )
        )


        abnormal_result = self.detector.detect(
        interpreted_values
        )

        abnormal_findings = abnormal_result["abnormal_findings"]

        print("\n===== DEBUG abnormal_findings =====")
        print(type(abnormal_findings))
        print(abnormal_findings)
        print(
            type(abnormal_findings[0])
            if abnormal_findings
            else "EMPTY"
        )

        clinical_summary = self.summary_generator.generate(
            cleaned_text=cleaned_text,
            laboratory_values=laboratory_values,
            interpreted_results=interpreted_values,
            abnormal_findings=abnormal_findings,
        )


        clinical_insights = self.insights_generator.generate(
            interpreted_results=interpreted_values,
            abnormal_findings=abnormal_findings,
            clinical_summary=clinical_summary["clinical_summary"],
        )


        return {

            "raw_text": raw_text,

            "cleaned_text": cleaned_text,

            "laboratory_values":
                laboratory_values,

            "interpreted_values":
                interpreted_values,

            "abnormal_findings":
                abnormal_findings,

            "clinical_summary":
                clinical_summary,

            "clinical_insights":
                clinical_insights,

        }
        # ---------------------------------------------------------
    # Validation Helpers
    # ---------------------------------------------------------

    @staticmethod
    def _validate_filename(
        filename: str,
    ) -> None:
        """
        Validate uploaded filename.
        """

        allowed_extensions = (
            ".pdf",
            ".docx",
            ".txt",
        )


        if not filename.lower().endswith(
            allowed_extensions
        ):

            raise ValueError(
                "Unsupported medical report format."
            )


    @staticmethod
    def _validate_file_size(
        file_data: bytes,
    ) -> None:
        """
        Validate uploaded file size.

        Maximum:
            10 MB
        """

        max_size = (
            10 * 1024 * 1024
        )


        if len(file_data) > max_size:

            raise ValueError(
                "File size exceeds 10 MB limit."
            )
        # ---------------------------------------------------------
    # Response Formatter
    # ---------------------------------------------------------

    def format_response(
        self,
        analysis_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Format raw analysis output into API response format.

        This creates a clean response structure
        for FastAPI endpoints.

        Args:
            analysis_result:
                Complete analysis dictionary.

        Returns:
            API-ready response dictionary.
        """

        logger.info(
            "Formatting medical report response."
        )


        response = {

            "status": "success",

            "report_analysis": {

                "laboratory_values":
                    analysis_result.get(
                        "laboratory_values",
                        [],
                    ),


                "interpreted_values":
                    analysis_result.get(
                        "interpreted_values",
                        [],
                    ),


                "abnormal_findings":
                    analysis_result.get(
                        "abnormal_findings",
                        [],
                    ),


                "clinical_summary":
                    analysis_result.get(
                        "clinical_summary",
                        {},
                    ),


                "clinical_insights":
                    analysis_result.get(
                        "clinical_insights",
                        [],
                    ),

            },


            "metadata": {

                "module":
                    "Medical Report Analysis",

                "version":
                    "1.0",

                "processed":
                    True,

            }

        }


        logger.info(
            "Response formatting completed."
        )


        return response
    
        # ---------------------------------------------------------
    # Service Status
    # ---------------------------------------------------------

    def get_pipeline_status(
        self,
    ) -> Dict[str, Any]:
        """
        Return service health information.

        Used for monitoring and debugging.

        Returns:
            Service status dictionary.
        """

        return {

            "service":
                "MedicalReportAnalysisService",

            "status":
                "active",

            "components": {

                "parser":
                    self.parser is not None,

                "cleaner":
                    self.cleaner is not None,

                "laboratory_extractor":
                    self.extractor is not None,

                "reference_interpreter":
                    self.interpreter is not None,

                "abnormal_detector":
                    self.detector is not None,

                "summary_generator":
                    self.summary_generator is not None,

                "insights_generator":
                    self.insights_generator is not None,

            }

        }
    