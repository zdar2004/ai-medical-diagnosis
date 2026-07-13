import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.report_analysis.report_analysis_service import (
    MedicalReportAnalysisService,
)

PDF_PATH = "sample_report.pdf"

service = MedicalReportAnalysisService()

result = service.analyze_report(PDF_PATH)

print("=" * 80)
print("REPORT ANALYSIS SERVICE")
print("=" * 80)

print("\nStatus:")
print(result["status"])

print("\nMetadata:")
print(result["metadata"])

analysis = result["report_analysis"]

print("\n" + "=" * 80)
print("LABORATORY VALUES")
print("=" * 80)
for k, v in analysis["laboratory_values"].items():
    print(k, ":", v)

print("\n" + "=" * 80)
print("INTERPRETED VALUES")
print("=" * 80)
for k, v in analysis["interpreted_values"].items():
    print(k, ":", v)

print("\n" + "=" * 80)
print("ABNORMAL FINDINGS")
print("=" * 80)
for finding in analysis["abnormal_findings"]:
    print(finding)

print("\n" + "=" * 80)
print("CLINICAL SUMMARY")
print("=" * 80)
print(analysis["clinical_summary"])

print("\n" + "=" * 80)
print("CLINICAL INSIGHTS")
print("=" * 80)

for insight in analysis["clinical_insights"]["insights"]:
    print(insight)

print("\nReview Required:")
print(analysis["clinical_insights"]["review_required"])

print("\n" + "=" * 80)
print("PIPELINE TEST COMPLETED")
print("=" * 80)