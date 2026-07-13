import sys
from pathlib import Path

sys.path.append(
    str(Path(__file__).resolve().parent.parent)
)


from app.report_analysis.report_parser import MedicalReportParser


def main():

    parser = MedicalReportParser()

    text = parser.parse(
        "sample_report.pdf"
    )

    print("=" * 60)
    print("PARSER OUTPUT")
    print("=" * 60)

    print(text)


if __name__ == "__main__":
    main()