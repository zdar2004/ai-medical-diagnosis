import styles from './ReportAnalysis.module.css'

// Toggle this to preview the loading state — kept static, no hooks needed.
const SHOW_LOADING = false

// Static, illustrative data only — no API, no upload logic, no business logic.
const SELECTED_FILE = {
  name: 'CBC_Report.pdf',
  size: '2.4 MB',
  status: 'Uploaded Successfully',
}

const OVERVIEW =
  'AI analysis detected mild anemia with elevated white blood cell count. Clinical correlation is recommended.'

const KEY_FINDINGS = [
  {
    name: 'Haemoglobin',
    status: 'Low',
    direction: 'down',
    interpretation: 'Below normal range, consistent with mild anemia.',
  },
  {
    name: 'White Blood Cells',
    status: 'High',
    direction: 'up',
    interpretation: 'Elevated count may indicate an underlying infection.',
  },
  {
    name: 'Platelets',
    status: 'Normal',
    direction: 'normal',
    interpretation: 'Within the expected reference range.',
  },
  {
    name: 'Blood Glucose',
    status: 'Normal',
    direction: 'normal',
    interpretation: 'Within the expected reference range.',
  },
]

const RECOMMENDATIONS = [
  'Repeat CBC in 2 weeks',
  'Order iron studies',
  'Schedule a clinical review',
  'Monitor symptoms and report any changes',
]

function FindingStatus({ direction, status }) {
  const statusClass =
    direction === 'up' ? styles.findingUp : direction === 'down' ? styles.findingDown : styles.findingNormal

  return (
    <span className={`${styles.findingStatus} ${statusClass}`}>
      {status}
      {direction === 'up' && <span aria-hidden="true"> ↑</span>}
      {direction === 'down' && <span aria-hidden="true"> ↓</span>}
    </span>
  )
}

function ReportAnalysis() {
  return (
    <div className={styles.page}>
      <section className={styles.header}>
        <p className={styles.eyebrow}>Medical Report Analysis</p>
        <h1 className={styles.title}>Analyze Medical Report</h1>
        <p className={styles.subtitle}>
          Upload laboratory reports or clinical documents and review the
          AI-generated medical summary.
        </p>
      </section>

      {/* Upload Card */}
      <section className={styles.card} aria-labelledby="upload-heading">
        <h2 id="upload-heading" className={styles.cardTitle}>
          Upload Report
        </h2>

        <div className={styles.uploadArea}>
          <svg
            className={styles.uploadIcon}
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.75"
            aria-hidden="true"
          >
            <path d="M12 16V4" strokeLinecap="round" strokeLinejoin="round" />
            <path d="M7 9l5-5 5 5" strokeLinecap="round" strokeLinejoin="round" />
            <path d="M4 16v3a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-3" strokeLinecap="round" strokeLinejoin="round" />
          </svg>

          <p className={styles.uploadTitle}>Drag &amp; Drop PDF or TXT Report</p>
          <p className={styles.uploadSubtitle}>or click to browse</p>

          <button type="button" className={styles.chooseFileButton}>
            Choose File
          </button>

          <p className={styles.uploadMeta}>
            Allowed formats: PDF, TXT &middot; Maximum size: 10 MB
          </p>
        </div>
      </section>

      {/* Selected File Card */}
      <section className={styles.card} aria-labelledby="selected-file-heading">
        <h2 id="selected-file-heading" className={styles.cardTitle}>
          Selected File
        </h2>

        <div className={styles.fileRow}>
          <div className={styles.fileIcon} aria-hidden="true">
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.75"
            >
              <path d="M7 3h7l5 5v13a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1Z" strokeLinejoin="round" />
              <path d="M14 3v5h5" strokeLinejoin="round" />
            </svg>
          </div>

          <div className={styles.fileInfo}>
            <p className={styles.fileName}>{SELECTED_FILE.name}</p>
            <p className={styles.fileMeta}>
              {SELECTED_FILE.size} &middot; {SELECTED_FILE.status}
            </p>
          </div>

          <button type="button" className={styles.removeButton} aria-label="Remove selected file">
            Remove
          </button>
        </div>
      </section>

      {/* Analyze Button */}
      <section className={styles.analyzeSection} aria-label="Analyze report action">
        <button type="button" className={styles.analyzeButton}>
          Analyze Report
        </button>
      </section>

      {/* Loading Card */}
      {SHOW_LOADING && (
        <section className={styles.loadingCard} aria-label="Analyzing report" aria-live="polite">
          <span className={styles.spinner} aria-hidden="true" />
          <p className={styles.loadingTitle}>Analyzing Report...</p>
          <p className={styles.loadingSubtitle}>Preparing clinical summary...</p>
        </section>
      )}

      {/* Analysis Summary Card */}
      <section className={styles.card} aria-labelledby="overview-heading">
        <h2 id="overview-heading" className={styles.cardTitle}>
          Analysis Summary
        </h2>
        <p className={styles.overviewText}>{OVERVIEW}</p>
      </section>

      {/* Key Findings Card */}
      <section className={styles.card} aria-labelledby="findings-heading">
        <h2 id="findings-heading" className={styles.cardTitle}>
          Key Findings
        </h2>
        <ul className={styles.findingsList}>
          {KEY_FINDINGS.map((finding) => (
            <li className={styles.findingItem} key={finding.name}>
              <div className={styles.findingTop}>
                <p className={styles.findingName}>{finding.name}</p>
                <FindingStatus direction={finding.direction} status={finding.status} />
              </div>
              <p className={styles.findingInterpretation}>{finding.interpretation}</p>
            </li>
          ))}
        </ul>
      </section>

      {/* Recommendations Card */}
      <section className={styles.card} aria-labelledby="recommendations-heading">
        <h2 id="recommendations-heading" className={styles.cardTitle}>
          Recommendations
        </h2>
        <ul className={styles.recommendationList}>
          {RECOMMENDATIONS.map((recommendation) => (
            <li className={styles.recommendationItem} key={recommendation}>
              {recommendation}
            </li>
          ))}
        </ul>
      </section>

      {/* Important Notice Card */}
      <section className={styles.noticeCard} aria-label="Important notice">
        <svg
          className={styles.noticeIcon}
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.75"
          aria-hidden="true"
        >
          <circle cx="12" cy="12" r="9" />
          <path d="M12 8v5" strokeLinecap="round" />
          <path d="M12 16h.01" strokeLinecap="round" />
        </svg>
        <p className={styles.noticeText}>
          This analysis is AI-assisted and should always be reviewed by a
          qualified healthcare professional.
        </p>
      </section>

      {/* Bottom Actions */}
      <section className={styles.actions} aria-label="Report analysis actions">
        <button type="button" className={styles.ghostButton}>
          Back
        </button>
        <button type="button" className={styles.secondaryButton}>
          Download Report
        </button>
        <button type="button" className={styles.primaryButton}>
          Save Analysis
        </button>
      </section>
    </div>
  )
}

export default ReportAnalysis