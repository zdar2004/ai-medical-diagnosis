import styles from './DiagnosisResult.module.css'

// Static, illustrative data only — no API, no AI calls, no business logic.
const PREDICTION = {
  disease: 'Type 2 Diabetes Mellitus',
  confidence: '92%',
  riskLevel: 'Moderate',
  specialist: 'Endocrinologist',
}

const DESCRIPTION =
  'Type 2 Diabetes Mellitus is a chronic condition affecting how the body processes blood sugar (glucose). It develops when the body becomes resistant to insulin or does not produce enough insulin to maintain normal glucose levels. Left unmanaged, it can affect the heart, kidneys, eyes, and nerves, making early detection and consistent monitoring important.'

const MATCHED_SYMPTOMS = [
  'Increased thirst',
  'Frequent urination',
  'Fatigue',
  'Blurred vision',
  'Slow-healing sores',
  'Unexplained weight loss',
  'Tingling in hands or feet',
  'Increased hunger',
]

const RECOMMENDED_TESTS = ['CBC', 'Blood Glucose', 'Chest X-Ray', 'ECG', 'Liver Function Test']

const LIFESTYLE_RECOMMENDATIONS = [
  'Adopt a balanced, low-glycemic diet with reduced refined sugar intake.',
  'Engage in at least 30 minutes of moderate physical activity most days.',
  'Monitor blood glucose levels regularly and keep a log for review.',
  'Maintain a healthy body weight and avoid prolonged periods of inactivity.',
  'Attend scheduled follow-up visits to track treatment response.',
]

function RiskBadge({ level }) {
  const badgeClass =
    level === 'High' ? styles.riskHigh : level === 'Moderate' ? styles.riskModerate : styles.riskLow
  return <span className={`${styles.riskBadge} ${badgeClass}`}>{level}</span>
}

function DiagnosisResult() {
  return (
    <div className={styles.page}>
      <section className={styles.header}>
        <p className={styles.eyebrow}>Clinical Decision Support</p>
        <h1 className={styles.title}>Diagnosis Result</h1>
        <p className={styles.subtitle}>
          Review the AI-generated prediction and supporting clinical details.
        </p>
      </section>

      {/* Section — Prediction Summary */}
      <section className={styles.summaryCard} aria-labelledby="summary-heading">
        <div className={styles.summaryHeader}>
          <h2 id="summary-heading" className={styles.cardTitle}>
            Prediction Summary
          </h2>
          <RiskBadge level={PREDICTION.riskLevel} />
        </div>

        <p className={styles.diseaseName}>{PREDICTION.disease}</p>

        <div className={styles.summaryGrid}>
          <div className={styles.summaryItem}>
            <p className={styles.summaryLabel}>Confidence</p>
            <p className={styles.summaryValue}>{PREDICTION.confidence}</p>
          </div>
          <div className={styles.summaryItem}>
            <p className={styles.summaryLabel}>Risk Level</p>
            <p className={styles.summaryValue}>{PREDICTION.riskLevel}</p>
          </div>
          <div className={styles.summaryItem}>
            <p className={styles.summaryLabel}>Recommended Specialist</p>
            <p className={styles.summaryValue}>{PREDICTION.specialist}</p>
          </div>
        </div>
      </section>

      {/* Section — Disease Description */}
      <section className={styles.card} aria-labelledby="description-heading">
        <h2 id="description-heading" className={styles.cardTitle}>
          Disease Description
        </h2>
        <p className={styles.description}>{DESCRIPTION}</p>
      </section>

      {/* Section — Symptoms Matched */}
      <section className={styles.card} aria-labelledby="symptoms-heading">
        <h2 id="symptoms-heading" className={styles.cardTitle}>
          Symptoms Matched
        </h2>
        <ul className={styles.tagList}>
          {MATCHED_SYMPTOMS.map((symptom) => (
            <li className={styles.tagItem} key={symptom}>
              <span className={styles.tagDot} aria-hidden="true" />
              {symptom}
            </li>
          ))}
        </ul>
      </section>

      {/* Section — Recommended Tests */}
      <section className={styles.card} aria-labelledby="tests-heading">
        <h2 id="tests-heading" className={styles.cardTitle}>
          Recommended Tests
        </h2>
        <ul className={styles.tagList}>
          {RECOMMENDED_TESTS.map((test) => (
            <li className={styles.tagItem} key={test}>
              <span className={styles.tagDot} aria-hidden="true" />
              {test}
            </li>
          ))}
        </ul>
      </section>

      {/* Section — Lifestyle Recommendations */}
      <section className={styles.card} aria-labelledby="lifestyle-heading">
        <h2 id="lifestyle-heading" className={styles.cardTitle}>
          Lifestyle Recommendations
        </h2>
        <ul className={styles.recommendationList}>
          {LIFESTYLE_RECOMMENDATIONS.map((recommendation) => (
            <li className={styles.recommendationItem} key={recommendation}>
              {recommendation}
            </li>
          ))}
        </ul>
      </section>

      {/* Section — Medication Notice */}
      <section className={styles.noticeCard} aria-label="Medication notice">
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
          Medication recommendations should always be confirmed by a qualified
          healthcare professional.
        </p>
      </section>

      {/* Section — Bottom Actions */}
      <section className={styles.actions} aria-label="Diagnosis result actions">
        <button type="button" className={styles.ghostButton}>
          Back
        </button>
        <button type="button" className={styles.secondaryButton}>
          Print Report
        </button>
        <button type="button" className={styles.primaryButton}>
          Save Diagnosis
        </button>
      </section>
    </div>
  )
}

export default DiagnosisResult