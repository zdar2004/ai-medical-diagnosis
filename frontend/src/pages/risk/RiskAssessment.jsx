import { useState } from 'react'
import styles from './RiskAssessment.module.css'
import {
  assessHeartDisease,
  assessDiabetes,
  assessStroke,
  assessHypertension,
} from '../../services/riskAssessmentService'

const DISEASES = {
  heart_disease: {
    label: 'Heart Disease',
    fields: [
      { id: 'age', label: 'Age', type: 'number', defaultValue: 55 },
      {
        id: 'sex',
        label: 'Sex',
        type: 'select',
        options: [
          { label: 'Female', value: 0 },
          { label: 'Male', value: 1 },
        ],
      },
      {
        id: 'cp',
        label: 'Chest Pain Type',
        type: 'select',
        options: [
          { label: 'Typical Angina', value: 0 },
          { label: 'Atypical Angina', value: 1 },
          { label: 'Non-anginal Pain', value: 2 },
          { label: 'Asymptomatic', value: 3 },
        ],
      },
      { id: 'trestbps', label: 'Resting Blood Pressure (mmHg)', type: 'number', defaultValue: 140 },
      { id: 'chol', label: 'Cholesterol (mg/dL)', type: 'number', defaultValue: 250 },
      {
        id: 'fbs',
        label: 'Fasting Blood Sugar > 120 mg/dL',
        type: 'select',
        options: [
          { label: 'No', value: 0 },
          { label: 'Yes', value: 1 },
        ],
      },
      {
        id: 'restecg',
        label: 'Resting ECG',
        type: 'select',
        options: [
          { label: 'Normal', value: 0 },
          { label: 'ST-T Wave Abnormality', value: 1 },
          { label: 'Left Ventricular Hypertrophy', value: 2 },
        ],
      },
      { id: 'thalach', label: 'Maximum Heart Rate', type: 'number', defaultValue: 150 },
      {
        id: 'exang',
        label: 'Exercise Induced Angina',
        type: 'select',
        options: [
          { label: 'No', value: 0 },
          { label: 'Yes', value: 1 },
        ],
      },
      { id: 'oldpeak', label: 'Oldpeak', type: 'number', step: '0.1', defaultValue: 1.2 },
      {
        id: 'slope',
        label: 'Slope',
        type: 'select',
        options: [
          { label: 'Upsloping', value: 0 },
          { label: 'Flat', value: 1 },
          { label: 'Downsloping', value: 2 },
        ],
      },
      {
        id: 'ca',
        label: 'Number of Major Vessels (CA)',
        type: 'select',
        options: [
          { label: '0', value: 0 },
          { label: '1', value: 1 },
          { label: '2', value: 2 },
          { label: '3', value: 3 },
          { label: '4', value: 4 },
        ],
      },
      {
        id: 'thal',
        label: 'Thalassemia',
        type: 'select',
        options: [
          { label: '0', value: 0 },
          { label: '1', value: 1 },
          { label: '2', value: 2 },
          { label: '3', value: 3 },
        ],
      },
    ],
    submit: assessHeartDisease,
  },

  diabetes: {
    label: 'Diabetes',
    fields: [
      {
        id: 'gender',
        label: 'Gender',
        type: 'select',
        options: [
          { label: 'Female', value: 'Female' },
          { label: 'Male', value: 'Male' },
          { label: 'Other', value: 'Other' },
        ],
      },
      { id: 'age', label: 'Age', type: 'number', defaultValue: 25 },
      {
        id: 'hypertension',
        label: 'Hypertension',
        type: 'select',
        options: [
          { label: 'No', value: 0 },
          { label: 'Yes', value: 1 },
        ],
      },
      {
        id: 'heart_disease',
        label: 'Heart Disease',
        type: 'select',
        options: [
          { label: 'No', value: 0 },
          { label: 'Yes', value: 1 },
        ],
      },
      {
        id: 'smoking_history',
        label: 'Smoking History',
        type: 'select',
        options: [
          { label: 'Never', value: 'never' },
          { label: 'Former', value: 'former' },
          { label: 'Current', value: 'current' },
          { label: 'Not Current', value: 'not current' },
          { label: 'Ever', value: 'ever' },
          { label: 'No Info', value: 'No Info' },
        ],
      },
      { id: 'bmi', label: 'BMI', type: 'number', step: '0.1', defaultValue: 22.5 },
      { id: 'HbA1c_level', label: 'HbA1c Level', type: 'number', step: '0.1', defaultValue: 5.2 },
      {
        id: 'blood_glucose_level',
        label: 'Blood Glucose Level (mg/dL)',
        type: 'number',
        defaultValue: 95,
      },
    ],
    submit: assessDiabetes,
  },

  stroke: {
    label: 'Stroke',
    fields: [
      {
        id: 'gender',
        label: 'Gender',
        type: 'select',
        options: [
          { label: 'Female', value: 'Female' },
          { label: 'Male', value: 'Male' },
          { label: 'Other', value: 'Other' },
        ],
      },
      { id: 'age', label: 'Age', type: 'number', defaultValue: 45 },
      {
        id: 'hypertension',
        label: 'Hypertension',
        type: 'select',
        options: [
          { label: 'No', value: 0 },
          { label: 'Yes', value: 1 },
        ],
      },
      {
        id: 'heart_disease',
        label: 'Heart Disease',
        type: 'select',
        options: [
          { label: 'No', value: 0 },
          { label: 'Yes', value: 1 },
        ],
      },
      {
        id: 'ever_married',
        label: 'Ever Married',
        type: 'select',
        options: [
          { label: 'Yes', value: 'Yes' },
          { label: 'No', value: 'No' },
        ],
      },
      {
        id: 'work_type',
        label: 'Work Type',
        type: 'select',
        options: [
          { label: 'Private', value: 'Private' },
          { label: 'Self-employed', value: 'Self-employed' },
          { label: 'Government Job', value: 'Govt_job' },
          { label: 'Children', value: 'children' },
          { label: 'Never Worked', value: 'Never_worked' },
        ],
      },
      {
        id: 'Residence_type',
        label: 'Residence Type',
        type: 'select',
        options: [
          { label: 'Urban', value: 'Urban' },
          { label: 'Rural', value: 'Rural' },
        ],
      },
      {
        id: 'avg_glucose_level',
        label: 'Average Glucose Level',
        type: 'number',
        step: '0.1',
        defaultValue: 100,
      },
      { id: 'bmi', label: 'BMI', type: 'number', step: '0.1', defaultValue: 24.5 },
      {
        id: 'smoking_status',
        label: 'Smoking Status',
        type: 'select',
        options: [
          { label: 'Never Smoked', value: 'never smoked' },
          { label: 'Formerly Smoked', value: 'formerly smoked' },
          { label: 'Smokes', value: 'smokes' },
          { label: 'Unknown', value: 'Unknown' },
        ],
      },
    ],
    submit: assessStroke,
  },

  hypertension: {
    label: 'Hypertension',
    fields: [
      { id: 'Age', label: 'Age', type: 'number', defaultValue: 45 },
      { id: 'Salt_Intake', label: 'Salt Intake', type: 'number', step: '0.1', defaultValue: 5 },
      { id: 'Stress_Score', label: 'Stress Score', type: 'number', defaultValue: 4 },
      {
        id: 'BP_History',
        label: 'Blood Pressure History',
        type: 'select',
        options: [
          { label: 'Normal', value: 'Normal' },
          { label: 'Elevated', value: 'Elevated' },
          { label: 'High', value: 'High' },
        ],
      },
      {
        id: 'Sleep_Duration',
        label: 'Sleep Duration (hours)',
        type: 'number',
        step: '0.1',
        defaultValue: 7,
      },
      { id: 'BMI', label: 'BMI', type: 'number', step: '0.1', defaultValue: 24.5 },
      {
        id: 'Medication',
        label: 'Medication',
        type: 'select',
        options: [
          { label: 'No', value: 'No' },
          { label: 'Yes', value: 'Yes' },
        ],
      },
      {
        id: 'Family_History',
        label: 'Family History',
        type: 'select',
        options: [
          { label: 'No', value: 'No' },
          { label: 'Yes', value: 'Yes' },
        ],
      },
      {
        id: 'Exercise_Level',
        label: 'Exercise Level',
        type: 'select',
        options: [
          { label: 'Low', value: 'Low' },
          { label: 'Moderate', value: 'Moderate' },
          { label: 'High', value: 'High' },
        ],
      },
      {
        id: 'Smoking_Status',
        label: 'Smoking Status',
        type: 'select',
        options: [
          { label: 'No', value: 'No' },
          { label: 'Yes', value: 'Yes' },
        ],
      },
    ],
    submit: assessHypertension,
  },
}


export function RiskLevelBadge({ level }) {
  const normalizedLevel = level?.toLowerCase()

  const badgeClass =
    normalizedLevel === 'high'
      ? styles.riskHigh
      : normalizedLevel === 'moderate'
        ? styles.riskModerate
        : styles.riskLow

  return (
    <span className={`${styles.riskBadge} ${badgeClass}`}>
      {level}
    </span>
  )
}

function RiskAssessment() {
  const [disease, setDisease] = useState('heart_disease')
  const [formData, setFormData] = useState(
    getInitialFormData(DISEASES.heart_disease.fields)
  )
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const currentDisease = DISEASES[disease]

  const handleDiseaseChange = (event) => {
    const selectedDisease = event.target.value

    setDisease(selectedDisease)
    setFormData(getInitialFormData(DISEASES[selectedDisease].fields))
    setResult(null)
    setError('')
  }

  const handleChange = (event) => {
    const { name, value, type } = event.target

    setFormData((previous) => ({
      ...previous,
      [name]:
        type === 'number' && value !== ''
          ? Number(value)
          : value,
    }))
  }

  const handleSubmit = async () => {
    setError('')
    setResult(null)
    setLoading(true)

    try {
      const response = await currentDisease.submit(formData)
      setResult(response)
    } catch (err) {
      console.error('Risk assessment error:', err)

      const detail = err.response?.data?.detail

      if (Array.isArray(detail)) {
        setError(
          detail
            .map((item) => `${item.loc?.join('.')}: ${item.msg}`)
            .join(' | ')
        )
      } else if (typeof detail === 'string') {
        setError(detail)
      } else {
        setError(
          err.response?.data?.message ||
            'Unable to complete the risk assessment. Please try again.'
        )
      }
    } finally {
      setLoading(false)
    }
  }


    function getInitialFormData(fields = []) {
      return fields.reduce((acc, field) => {
        const { id, type, defaultValue, options } = field

        if (defaultValue !== undefined) {
          acc[id] = defaultValue
        } else if (type === 'select' && Array.isArray(options) && options.length > 0) {
          acc[id] = options[0].value
        } else if (type === 'number') {
          acc[id] = ''
        } else {
          acc[id] = ''
        }

        return acc
      }, {})
    }

  const confidencePercentage =
    result ? (Number(result.confidence) * 100).toFixed(2) : null

  return (
    <div className={styles.page}>
      <section className={styles.header}>
        <p className={styles.eyebrow}>Risk Assessment</p>

        <h1 className={styles.title}>
          AI Health Risk Assessment
        </h1>

        <p className={styles.subtitle}>
          Estimate the patient&apos;s risk for common chronic diseases using
          AI-powered prediction models.
        </p>
      </section>

      <section className={styles.card} aria-labelledby="disease-heading">
        <h2 id="disease-heading" className={styles.cardTitle}>
          Select Disease
        </h2>

        <select
          className={styles.select}
          value={disease}
          onChange={handleDiseaseChange}
        >
          {Object.entries(DISEASES).map(([key, item]) => (
            <option key={key} value={key}>
              {item.label}
            </option>
          ))}
        </select>
      </section>

      <section className={styles.card} aria-labelledby="risk-form-heading">
        <h2 id="risk-form-heading" className={styles.cardTitle}>
          {currentDisease.label} Risk Prediction
        </h2>

        <div className={styles.grid}>
          {currentDisease.fields.map((field) => (
            <div className={styles.field} key={field.id}>
              <label
                htmlFor={field.id}
                className={styles.label}
              >
                {field.label}
              </label>

              {field.type === 'select' ? (
                <select
                  id={field.id}
                  name={field.id}
                  className={styles.select}
                  value={
                    formData[field.id] ??
                    field.options[0].value
                  }
                  onChange={handleChange}
                >
                  {field.options.map((option) => (
                    <option
                      key={String(option.value)}
                      value={option.value}
                    >
                      {option.label}
                    </option>
                  ))}
                </select>
              ) : (
                <input
                  id={field.id}
                  name={field.id}
                  type={field.type}
                  step={field.step}
                  className={styles.input}
                  value={
                    formData[field.id] ??
                    field.defaultValue ??
                    ''
                  }
                  onChange={handleChange}
                />
              )}
            </div>
          ))}
        </div>
      </section>

      <section
        className={styles.predictSection}
        aria-label="Predict risk action"
      >
        <button
          type="button"
          className={styles.predictButton}
          onClick={handleSubmit}
          disabled={loading}
        >
          {loading ? 'Calculating Risk...' : 'Predict Risk'}
        </button>
      </section>

      {loading && (
        <section
          className={styles.loadingCard}
          aria-label="Calculating risk"
          aria-live="polite"
        >
          <span
            className={styles.spinner}
            aria-hidden="true"
          />

          <p className={styles.loadingTitle}>
            Calculating Risk...
          </p>

          <p className={styles.loadingSubtitle}>
            Analyzing patient profile using the {currentDisease.label} model...
          </p>
        </section>
      )}

      {error && (
        <section
          className={styles.noticeCard}
          aria-label="Risk assessment error"
        >
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
            {error}
          </p>
        </section>
      )}

      {result && (
        <>
          <section
            className={styles.card}
            aria-labelledby="risk-summary-heading"
          >
            <h2
              id="risk-summary-heading"
              className={styles.cardTitle}
            >
              Risk Assessment Result
            </h2>

            <div className={styles.riskGrid}>
              <div className={styles.riskCard}>
                <p className={styles.riskLabel}>
                  Disease
                </p>

                <p className={styles.riskPercentage}>
                  {result.disease}
                </p>
              </div>

              <div className={styles.riskCard}>
                <p className={styles.riskLabel}>
                  Prediction
                </p>

                <p className={styles.riskPercentage}>
                  {result.prediction === 1
                    ? 'Positive'
                    : 'Negative'}
                </p>
              </div>

              <div className={styles.riskCard}>
                <p className={styles.riskLabel}>
                  Risk Probability
                </p>

                <p className={styles.riskPercentage}>
                  {confidencePercentage}%
                </p>
              </div>
            </div>

            <RiskLevelBadge level={result.risk_level} />
          </section>

          <section
            className={styles.overallCard}
            aria-labelledby="overall-risk-heading"
          >
            <div className={styles.overallTop}>
              <div>
                <p className={styles.overallLabel}>
                  Risk Level
                </p>

                <p
                  className={styles.overallLevel}
                  id="overall-risk-heading"
                >
                  {result.risk_level}
                </p>
              </div>
            </div>

            <div
              className={styles.progressTrack}
              role="progressbar"
              aria-valuenow={Number(result.confidence) * 100}
              aria-valuemin="0"
              aria-valuemax="100"
              aria-label="Prediction confidence"
            >
              <div
                className={styles.progressFill}
                style={{
                  width: `${Number(result.confidence) * 100}%`,
                }}
              />
            </div>
          </section>

          <section
            className={styles.card}
            aria-labelledby="model-heading"
          >
            <h2
              id="model-heading"
              className={styles.cardTitle}
            >
              Model Information
            </h2>

            <div className={styles.patientGrid}>
              <div className={styles.patientItem}>
                <p className={styles.patientLabel}>
                  Model
                </p>

                <p className={styles.patientValue}>
                  {result.model}
                </p>
              </div>

              <div className={styles.patientItem}>
                <p className={styles.patientLabel}>
                  Prediction
                </p>

                <p className={styles.patientValue}>
                  {result.prediction}
                </p>
              </div>

              <div className={styles.patientItem}>
                <p className={styles.patientLabel}>
                  Timestamp
                </p>

                <p className={styles.patientValue}>
                  {new Date(result.timestamp).toLocaleString()}
                </p>
              </div>
            </div>
          </section>
        </>
      )}

      <section
        className={styles.noticeCard}
        aria-label="Important notice"
      >
        <svg
          className={styles.noticeIcon}
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.75"
          aria-hidden="true"
        >
          <circle cx="12" cy="12" r="9" />
          <path
            d="M12 8v5"
            strokeLinecap="round"
          />
          <path
            d="M12 16h.01"
            strokeLinecap="round"
          />
        </svg>

        <p className={styles.noticeText}>
          This assessment is AI-assisted and should not replace
          professional medical evaluation.
        </p>
      </section>
    </div>
  )
}

export default RiskAssessment