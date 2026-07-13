"""
Medical Report Cleaning Module.

This module provides the MedicalReportCleaner class for normalizing and cleaning
raw extracted text from medical report PDFs into standardized medical text format.
"""

import re
from typing import Optional
from app.risk_assessment.utils.logging_utils import get_logger

logger = get_logger(__name__)


class MedicalReportCleaner:
    """
    Clean and normalize raw extracted text from medical reports.

    This class processes raw text extracted from PDF medical reports and converts
    it into a normalized format suitable for further analysis. It removes headers,
    footers, excessive whitespace, and separators while preserving medical values,
    units, and report structure.

    Attributes:
        _header_patterns (list): List of regex patterns for common header formats.
        _footer_patterns (list): List of regex patterns for common footer formats.
        _separator_patterns (list): List of regex patterns for separators to remove.
        _unicode_replacements (dict): Mapping of Unicode characters to ASCII equivalents.
    """

    def __init__(self) -> None:
        """Initialize the MedicalReportCleaner with predefined patterns."""
        self._header_patterns = [
            r'^.{0,50}Page \d+ of \d+.{0,50}$',
            r'^.{0,50}Page \d+.{0,50}$',
            r'^.{0,50}Report Date: .{0,50}$',
            r'^.{0,50}Printed On: .{0,50}$',
            r'^.{0,50}Patient: .{0,50}$',
            r'^.{0,50}MRN: .{0,50}$',
            r'^.{0,50}DOB: .{0,50}$',
            r'^.{0,50}Age: .{0,50}$',
            r'^.{0,50}Gender: .{0,50}$',
            r'^.{0,50}Accession #: .{0,50}$',
            r'^.{0,50}Specimen: .{0,50}$',
        ]

        self._footer_patterns = [
            r'^.{0,50}Page \d+ of \d+.{0,50}$',
            r'^.{0,50}Page \d+.{0,50}$',
            r'^.{0,50}Printed On: .{0,50}$',
            r'^.{0,50}Generated: .{0,50}$',
            r'^.{0,50}End of Report.{0,50}$',
            r'^.{0,50}---{3,}Page \d+---{3,}.{0,50}$',
            r'^.{0,50}---{3,}\d+---{3,}.{0,50}$',
            r'^.{0,50}Signature: .{0,50}$',
            r'^.{0,50}Clinical Significance: .{0,50}$',
        ]

        self._separator_patterns = [
            r'^---+$',
            r'^===+$',
            r'^__+$',
            r'^\.\.\.+$',
            r'^[=*_\-]{5,}$',
        ]

        self._unicode_replacements = {
            '\u2018': "'",  # Left single quotation mark
            '\u2019': "'",  # Right single quotation mark
            '\u201C': '"',  # Left double quotation mark
            '\u201D': '"',  # Right double quotation mark
            '\u2013': '-',  # En dash
            '\u2014': '-',  # Em dash
            '\u00A0': ' ',  # Non-breaking space
            '\u00AD': '',   # Soft hyphen
            '\u2022': '*',  # Bullet
            '\u2026': '...',  # Horizontal ellipsis
            '\u2122': 'TM',  # Trademark
            '\u00AE': '(R)', # Registered trademark
            '\u00A9': '(C)', # Copyright
        }

    def clean(self, text: str) -> str:
        """
        Clean and normalize raw extracted medical report text.

        This is the main public API method that processes the raw text through
        a series of cleaning operations.

        Args:
            text (str): Raw extracted text from a medical report PDF.

        Returns:
            str: Cleaned and normalized medical text ready for further analysis.

        Example:
            >>> cleaner = MedicalReportCleaner()
            >>> raw_text = "Patient Name:\\n\\nJohn Doe\\n\\nGlucose: 145 mg/dL"
            >>> cleaned = cleaner.clean(raw_text)
            >>> print(cleaned)
            "Patient Name:\\nJohn Doe\\n\\nGlucose: 145 mg/dL"
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for cleaning")
            return ""

        logger.info("Starting medical report cleaning")
        original_length = len(text)
        logger.debug(
        "Original text length: %d",
        original_length,
    )

        cleaned_text = self._preprocess_unicode(text)
        cleaned_text = self._remove_headers(cleaned_text)
        cleaned_text = self._remove_footers(cleaned_text)
        cleaned_text = self._remove_duplicate_blank_lines(cleaned_text)
        cleaned_text = self._normalize_whitespace(cleaned_text)
        cleaned_text = self._remove_separators(cleaned_text)
        cleaned_text = self._normalize_colons(cleaned_text)
        cleaned_text = self._finalize_text(cleaned_text)

        final_length = len(cleaned_text)
        logger.info(
            "Cleaning completed. Final length: %d characters",
            final_length,
        )

        logger.debug(
            "Reduction: %d characters removed",
            original_length - final_length,
        )
        cleaned_text = cleaned_text.strip()
        return cleaned_text

    def _preprocess_unicode(self, text: str) -> str:
        """
        Replace Unicode characters with ASCII equivalents.

        Args:
            text (str): Text containing Unicode characters.

        Returns:
            str: Text with Unicode characters replaced by ASCII equivalents.
        """
        if not text:
            return text

        for unicode_char, replacement in self._unicode_replacements.items():
            text = text.replace(unicode_char, replacement)

        return text

    def _remove_headers(self, text: str) -> str:
        """
        Remove header lines from the text.

        Args:
            text (str): Text potentially containing headers.

        Returns:
            str: Text with headers removed.
        """
        if not text:
            return text

        lines = text.splitlines()
        cleaned_lines = []

        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                cleaned_lines.append(line)
                continue

            is_header = False
            for pattern in self._header_patterns:
                if re.match(pattern, line_stripped, re.IGNORECASE):
                    is_header = True
                    break

            if not is_header:
                cleaned_lines.append(line)

        return '\n'.join(cleaned_lines)

    def _remove_footers(self, text: str) -> str:
        """
        Remove footer lines from the text.

        Args:
            text (str): Text potentially containing footers.

        Returns:
            str: Text with footers removed.
        """
        if not text:
            return text

        lines = text.splitlines()
        cleaned_lines = []

        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                cleaned_lines.append(line)
                continue

            is_footer = False
            for pattern in self._footer_patterns:
                if re.match(pattern, line_stripped, re.IGNORECASE):
                    is_footer = True
                    break

            if not is_footer:
                cleaned_lines.append(line)

        return '\n'.join(cleaned_lines)

    def _normalize_whitespace(self, text: str) -> str:
        """
        Normalize all whitespace in the text.

        This method normalizes tabs to spaces, collapses multiple spaces,
        and ensures consistent whitespace formatting.

        Args:
            text (str): Text with inconsistent whitespace.

        Returns:
            str: Text with normalized whitespace.
        """
        if not text:
            return text

        # Replace tabs with spaces
        text = text.replace('\t', ' ')

        # Replace multiple spaces with single space (but preserve newlines)
        lines = text.splitlines()
        normalized_lines = []

        for line in lines:
            # Collapse multiple spaces but preserve indentation structure
            line = re.sub(r' +', ' ', line)
            normalized_lines.append(line)

        return '\n'.join(normalized_lines)

    def _remove_duplicate_blank_lines(self, text: str) -> str:
        """
        Remove duplicate blank lines from the text.

        Args:
            text (str): Text with potential duplicate blank lines.

        Returns:
            str: Text with duplicate blank lines removed (max 1 blank line).
        """
        if not text:
            return text

        lines = text.splitlines()
        cleaned_lines = []
        previous_was_blank = False

        for line in lines:
            is_blank = not line.strip()

            if is_blank and previous_was_blank:
                continue

            cleaned_lines.append(line)
            previous_was_blank = is_blank

        return '\n'.join(cleaned_lines)

    def _remove_separators(self, text: str) -> str:
        """
        Remove separator lines from the text.

        Args:
            text (str): Text potentially containing separator lines.

        Returns:
            str: Text with separators removed.
        """
        if not text:
            return text

        lines = text.splitlines()
        cleaned_lines = []

        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                cleaned_lines.append(line)
                continue

            is_separator = False
            for pattern in self._separator_patterns:
                if re.match(pattern, line_stripped, re.IGNORECASE):
                    is_separator = True
                    break

            if not is_separator:
                cleaned_lines.append(line)

        return '\n'.join(cleaned_lines)

    def _normalize_colons(self, text: str) -> str:
        """
        Normalize colon spacing in the text.

        Args:
            text (str): Text with potentially inconsistent colon spacing.

        Returns:
            str: Text with normalized colon spacing.
        """
        if not text:
            return text

        # Normalize spacing around colons
        # Convert "Label : Value" to "Label: Value"
        text = re.sub(
            r'([A-Za-z0-9])\s*:\s*',
            r'\1: ',
            text,
        )

        return text

    def _finalize_text(self, text: str) -> str:
        """
        Perform final text cleanup and formatting.

        This method ensures consistent line endings, removes trailing whitespace,
        and performs final text validation.

        Args:
            text (str): Text to finalize.

        Returns:
            str: Finalized text.
        """
        if not text:
            return text

        # Remove trailing whitespace from each line
        lines = text.splitlines()
        lines = [line.rstrip() for line in lines]

        # Remove trailing whitespace from the end of the text
        text = '\n'.join(lines)
        text = text.rstrip()

        # Ensure consistent line endings (convert to \n)
        text = text.replace('\r\n', '\n')
        text = text.replace('\r', '\n')

        return text