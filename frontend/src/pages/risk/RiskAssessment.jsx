import styles from './RiskAssessment.module.css'

// Toggle this to preview the loading state — kept static, no hooks needed.
const SHOW_LOADING = false

// Static, illustrative data only — no API, no prediction logic, no business logic.
const PATIENT = {
  name: 'Amelia Carter',
  age: '54 Years',
  gender: 'Female',
  height: '165 cm',
  weight: '72 kg',
  bmi: '26.4',
}

const FORM_FIELDS = [
  { id: 'age', label: 'Age', type: 'number', defaultValue: 54 },
  {
    id: 'gender',
    label: 'Gender',
    type: 'select',
    options: ['Female', 'Male', 'Other'],
  },
  { id: 'height', label: 'Height (cm)', type: 'number', defaultValue: 165 },
  { id: 'weight', label: 'Weight (kg)', type: 'number', defaultValue: 72 },
  {
    id: 'bloodPressure',
    label: 'Blood Pressure (mmHg)',
    type: 'text',
    defaultValue: '128/84',
  },
  {
    id: 'bloodGlucose',
    label: 'Blood Glucose (mg/dL)',
    type: 'number',
    defaultValue: 118,
  },
  {
    id: 'cholesterol',
    label: 'Cholesterol (mg/dL)',
    type: 'number',
    defaultValue: 210,
  },
  {
    id: 'smokingStatus',
    label: 'Smoking Status',
    type: 'select',
    options: ['Never Smoked', 'Former Smoker', 'Current Smoker'],
  },
  {
    id: 'familyHistory',
    label: 'Family History',
    type: 'select',
    options: ['None', 'Diabetes', 'Heart Disease', 'Both'],
  },
  {
    id: 'physicalActivity',
    label: 'Physical Activity',
    type: 'select',
    options: ['Sedentary', 'Light', 'Moderate', 'Active'],
  },
]

const RISK_PREDICTIONS = [
  { label: 'Diabetes Risk', percentage: '72%', level: 'Moderate Risk', tone: 'moderate' },
  { label: 'Heart Disease Risk', percentage: '34%', level: 'Low Risk', tone: 'low' },
  { label: 'Stroke Risk', percentage: '18%', level: 'Low Risk', tone: 'low' },
]

const OVERALL_RISK = {
  level: 'Moderate',
  score: 58,
}

const RISK_FACTORS = ['Elevated BMI', 'High Blood Glucose', 'Family History', 'Sedentary Lifestyle']

const RECOMMENDATIONS = [
  'Increase physical activity',
  'Reduce sugar intake',
  'Routine blood pressure monitoring',
  'Weight management',
  'Annual medical checkup',
]

function RiskLevelBadge({ tone, level }) {
  const badgeClass = tone === 'high' ? styles.riskHigh : tone === 'moderate' ? styles.riskModerate : styles.riskLow
  return <span className={`${styles.riskBadge} ${badgeClass}`}>{level}</span>
}

function FormField({ field }) {
  return (
    <div className={styles.field}>
      <label htmlFor={field.id} className={styles.label}>
        {field.label}
      </label>

      {field.type === 'select' ? (
        <select id={field.id} name={field.id} className={styles.select} defaultValue={field.options[0]}>
          {field.options.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      ) : (
        <input
          id={field.id}
          name={field.id}
          type={field.type}
          className={styles.input}
          defaultValue={field.defaultValue}
        />
      )}
    </div>
  )
}

function RiskAssessment() {
  return (
    <div className={styles.page}>
      <section className={styles.header}>
        <p className={styles.eyebrow}>Risk Assessment</p>
        <h1 className={styles.title}>AI Health Risk Assessment</h1>
        <p className={styles.subtitle}>
          Estimate the patient&apos;s risk for common chronic diseases using
          AI-powered prediction models.
        </p>
      </section>

      {/* Patient Information Card */}
      <section className={styles.card} aria-labelledby="patient-info-heading">
        <h2 id="patient-info-heading" className={styles.cardTitle}>
          Patient Information
        </h2>
        <dl className={styles.patientGrid}>
          <div className={styles.patientItem}>
            <dt className={styles.patientLabel}>Name</dt>
            <dd className={styles.patientValue}>{PATIENT.name}</dd>
          </div>
          <div className={styles.patientItem}>
            <dt className={styles.patientLabel}>Age</dt>
            <dd className={styles.patientValue}>{PATIENT.age}</dd>
          </div>
          <div className={styles.patientItem}>
            <dt className={styles.patientLabel}>Gender</dt>
            <dd className={styles.patientValue}>{PATIENT.gender}</dd>
          </div>
          <div className={styles.patientItem}>
            <dt className={styles.patientLabel}>Height</dt>
            <dd className={styles.patientValue}>{PATIENT.height}</dd>
          </div>
          <div className={styles.patientItem}>
            <dt className={styles.patientLabel}>Weight</dt>
            <dd className={styles.patientValue}>{PATIENT.weight}</dd>
          </div>
          <div className={styles.patientItem}>
            <dt className={styles.patientLabel}>BMI</dt>
            <dd className={styles.patientValue}>{PATIENT.bmi}</dd>
          </div>
        </dl>
      </section>

      {/* Risk Prediction Form */}
      <section className={styles.card} aria-labelledby="risk-form-heading">
        <h2 id="risk-form-heading" className={styles.cardTitle}>
          Risk Prediction Form
        </h2>
        <div className={styles.grid}>
          {FORM_FIELDS.map((field) => (
            <FormField field={field} key={field.id} />
          ))}
        </div>
      </section>

      {/* Predict Risk Button */}
      <section className={styles.predictSection} aria-label="Predict risk action">
        <button type="button" className={styles.predictButton}>
          Predict Risk
        </button>
      </section>

      {/* Loading Card */}
      {SHOW_LOADING && (
        <section className={styles.loadingCard} aria-label="Calculating risk" aria-live="polite">
          <span className={styles.spinner} aria-hidden="true" />
          <p className={styles.loadingTitle}>Calculating Risk...</p>
          <p className={styles.loadingSubtitle}>Analyzing patient profile...</p>
        </section>
      )}

      {/* Risk Summary Card */}
      <section className={styles.card} aria-labelledby="risk-summary-heading">
        <h2 id="risk-summary-heading" className={styles.cardTitle}>
          Risk Summary
        </h2>
        <div className={styles.riskGrid}>
          {RISK_PREDICTIONS.map((risk) => (
            <div className={styles.riskCard} key={risk.label}>
              <p className={styles.riskLabel}>{risk.label}</p>
              <p className={styles.riskPercentage}>{risk.percentage}</p>
              <RiskLevelBadge tone={risk.tone} level={risk.level} />
            </div>
          ))}
        </div>
      </section>

      {/* Overall Risk Score Card */}
      <section className={styles.overallCard} aria-labelledby="overall-risk-heading">
        <div className={styles.overallTop}>
          <div>
            <p className={styles.overallLabel}>Overall Risk</p>
            <p className={styles.overallLevel} id="overall-risk-heading">
              {OVERALL_RISK.level}
            </p>
          </div>
          <div className={styles.overallScoreBlock}>
            <p className={styles.overallLabel}>Risk Score</p>
            <p className={styles.overallScore}>{OVERALL_RISK.score}%</p>
          </div>
        </div>

        <div
          className={styles.progressTrack}
          role="progressbar"
          aria-valuenow={OVERALL_RISK.score}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label="Overall risk score"
        >
          <div className={styles.progressFill} style={{ width: `${OVERALL_RISK.score}%` }} />
        </div>
      </section>

      {/* Risk Factors Card */}
      <section className={styles.card} aria-labelledby="risk-factors-heading">
        <h2 id="risk-factors-heading" className={styles.cardTitle}>
          Risk Factors
        </h2>
        <ul className={styles.tagList}>
          {RISK_FACTORS.map((factor) => (
            <li className={styles.tagItem} key={factor}>
              <span className={styles.tagDot} aria-hidden="true" />
              {factor}
            </li>
          ))}
        </ul>
      </section>

      {/* Lifestyle Recommendations Card */}
      <section className={styles.card} aria-labelledby="recommendations-heading">
        <h2 id="recommendations-heading" className={styles.cardTitle}>
          Lifestyle Recommendations
        </h2>
        <ul className={styles.recommendationList}>
          {RECOMMENDATIONS.map((recommendation) => (
            <li className={styles.recommendationItem} key={recommendation}>
              {recommendation}
            </li>
          ))}
        </ul>
      </section>

      {/* Notice Card */}
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
          This assessment is AI-assisted and should not replace professional
          medical evaluation.
        </p>
      </section>

      {/* Bottom Actions */}
      <section className={styles.actions} aria-label="Risk assessment actions">
        <button type="button" className={styles.ghostButton}>
          Back
        </button>
        <button type="button" className={styles.secondaryButton}>
          Download Assessment
        </button>
        <button type="button" className={styles.primaryButton}>
          Save Result
        </button>
      </section>
    </div>
  )
}

export default RiskAssessment