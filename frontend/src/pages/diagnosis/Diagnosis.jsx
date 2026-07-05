import styles from './Diagnosis.module.css'

// Static, illustrative data only — no API, no AI calls, no business logic.
const SELECTED_PATIENT = {
  id: 'PT-1042',
  name: 'Amelia Carter',
  age: 54,
  gender: 'Female',
  bloodGroup: 'A+',
}

const PATIENT_OPTIONS = [
  'Amelia Carter — PT-1042',
  'Daniel Osei — PT-1043',
  'Priya Nair — PT-1044',
  'Marcus Webb — PT-1045',
]

const PREDICTION = {
  disease: 'Type 2 Diabetes Mellitus',
  confidence: '92%',
  riskLevel: 'Moderate',
  specialist: 'Endocrinologist',
}

const RECOMMENDATIONS = [
  'Order a confirmatory HbA1c test and fasting blood glucose panel.',
  'Begin dietary counselling and initiate routine blood pressure monitoring.',
  'Schedule a follow-up consultation within 2 weeks to assess response.',
]

function RiskBadge({ level }) {
  const badgeClass =
    level === 'High' ? styles.badgeHigh : level === 'Moderate' ? styles.badgeModerate : styles.badgeLow
  return <span className={`${styles.badge} ${badgeClass}`}>{level}</span>
}

function Diagnosis() {
  return (
    <div className={styles.page}>
      <section className={styles.header}>
        <p className={styles.eyebrow}>Clinical Decision Support</p>
        <h1 className={styles.title}>AI Disease Diagnosis</h1>
        <p className={styles.subtitle}>
          Enter patient symptoms to generate AI-assisted disease prediction.
        </p>
      </section>

      {/* Section — Patient Selection */}
      <section className={styles.card} aria-labelledby="patient-selection-heading">
        <h2 id="patient-selection-heading" className={styles.cardTitle}>
          Patient Selection
        </h2>

        <div className={styles.field}>
          <label htmlFor="patientSelect" className={styles.label}>
            Patient
          </label>
          <select
            id="patientSelect"
            className={styles.select}
            defaultValue={PATIENT_OPTIONS[0]}
          >
            {PATIENT_OPTIONS.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </div>

        <div className={styles.patientGrid}>
          <div className={styles.patientItem}>
            <p className={styles.patientLabel}>Age</p>
            <p className={styles.patientValue}>{SELECTED_PATIENT.age}</p>
          </div>
          <div className={styles.patientItem}>
            <p className={styles.patientLabel}>Gender</p>
            <p className={styles.patientValue}>{SELECTED_PATIENT.gender}</p>
          </div>
          <div className={styles.patientItem}>
            <p className={styles.patientLabel}>Blood Group</p>
            <p className={styles.patientValue}>{SELECTED_PATIENT.bloodGroup}</p>
          </div>
        </div>
      </section>

      {/* Section — Symptoms */}
      <section className={styles.card} aria-labelledby="symptoms-heading">
        <h2 id="symptoms-heading" className={styles.cardTitle}>
          Symptoms Input
        </h2>
        <textarea
          className={styles.symptomsTextarea}
          placeholder="Enter patient symptoms..."
          rows={7}
        />
        <p className={styles.helperNote}>
          Example: Fever, headache, cough, sore throat...
        </p>
      </section>

      {/* Section — AI Prediction Result */}
      <section className={styles.card} aria-labelledby="prediction-heading">
        <div className={styles.predictionHeader}>
          <h2 id="prediction-heading" className={styles.cardTitle}>
            AI Prediction Result
          </h2>
          <RiskBadge level={PREDICTION.riskLevel} />
        </div>

        <p className={styles.diseaseName}>{PREDICTION.disease}</p>

        <div className={styles.predictionGrid}>
          <div className={styles.predictionItem}>
            <p className={styles.predictionLabel}>Confidence</p>
            <p className={styles.predictionValue}>{PREDICTION.confidence}</p>
          </div>
          <div className={styles.predictionItem}>
            <p className={styles.predictionLabel}>Risk Level</p>
            <p className={styles.predictionValue}>{PREDICTION.riskLevel}</p>
          </div>
          <div className={styles.predictionItem}>
            <p className={styles.predictionLabel}>Recommended Specialist</p>
            <p className={styles.predictionValue}>{PREDICTION.specialist}</p>
          </div>
        </div>
      </section>

      {/* Section — Clinical Recommendations */}
      <section className={styles.card} aria-labelledby="recommendations-heading">
        <h2 id="recommendations-heading" className={styles.cardTitle}>
          Clinical Recommendations
        </h2>
        <ul className={styles.recommendationsList}>
          {RECOMMENDATIONS.map((recommendation) => (
            <li className={styles.recommendationItem} key={recommendation}>
              {recommendation}
            </li>
          ))}
        </ul>
      </section>

      {/* Section — Action Buttons */}
      <section className={styles.controls} aria-label="Diagnosis actions">
        <button type="button" className={styles.clearButton}>
          Clear Form
        </button>
        <button type="button" className={styles.primaryButton}>
          Predict Disease
        </button>
      </section>
    </div>
  )
}

export default Diagnosis