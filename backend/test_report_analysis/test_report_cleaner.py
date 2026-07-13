import sys
from pathlib import Path

# Add backend root to Python path
sys.path.append(
    str(Path(__file__).resolve().parent.parent)
)

from app.report_analysis.report_cleaner import MedicalReportCleaner


def main():

    raw_text = """
===================================================

              MEDICAL LAB REPORT

===================================================


Patient Name :     Ali Khan


Age :   45


Gender : Male




Glucose :      145      mg/dL



Hemoglobin :      11.2      g/dL




WBC :     8500      cells/uL




---------------------------------------------------

Doctor Notes:



Patient shows elevated glucose level.



Follow up recommended.




===================================================



"""

    cleaner = MedicalReportCleaner()

    cleaned_text = cleaner.clean(raw_text)

    print("=" * 70)
    print("RAW TEXT")
    print("=" * 70)
    print(raw_text)

    print()

    print("=" * 70)
    print("CLEANED TEXT")
    print("=" * 70)
    print(cleaned_text)

    print()

    print("=" * 70)
    print("TEST COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main()