import { useEffect, useState } from 'react'
import styles from './AnalyticsDashboard.module.css'

import {
  getAnalyticsSummary,
  getDiseaseDistribution,
  getMonthlyAnalytics,
  getModelPerformance,
} from '../../services/analyticsService'

// These sections do not currently have dedicated backend endpoints.
const RECENT_PREDICTIONS = [
  { patient: 'Amelia Carter', disease: 'Type 2 Diabetes', confidence: '92%', risk: 'Moderate', date: '2026-07-03' },
  { patient: 'Daniel Osei', disease: 'Acute Myocardial Infarction', confidence: '96%', risk: 'High', date: '2026-07-02' },
  { patient: 'Priya Nair', disease: 'Community-Acquired Pneumonia', confidence: '90%', risk: 'Low', date: '2026-07-01' },
  { patient: 'Marcus Webb', disease: 'Hypertension', confidence: '88%', risk: 'Moderate', date: '2026-06-30' },
  { patient: 'Kenji Watanabe', disease: 'Chronic Kidney Disease', confidence: '91%', risk: 'High', date: '2026-06-29' },
]

const SYSTEM_OVERVIEW = [
  { label: 'Backend Status', status: 'Healthy', tone: 'good' },
  { label: 'AI Engine', status: 'Online', tone: 'good' },
  { label: 'Database', status: 'Connected', tone: 'good' },
  { label: 'Report Analysis', status: 'Available', tone: 'good' },
  { label: 'Clinical Assistant', status: 'Offline', tone: 'bad' },
]

const RISK_BADGE_CLASS = {
  Low: 'riskLow',
  Moderate: 'riskModerate',
  High: 'riskHigh',
}

function RiskBadge({ level }) {
  const variant = RISK_BADGE_CLASS[level] || 'riskModerate'

  return (
    <span className={`${styles.riskBadge} ${styles[variant]}`}>
      {level}
    </span>
  )
}

function StatusBadge({ tone, status }) {
  const statusClass = tone === 'bad'
    ? styles.statusBad
    : styles.statusGood

  return (
    <span className={`${styles.statusBadge} ${statusClass}`}>
      {status}
    </span>
  )
}

function AnalyticsDashboard() {
  const [summary, setSummary] = useState(null)
  const [diseaseDistribution, setDiseaseDistribution] = useState([])
  const [monthlyActivity, setMonthlyActivity] = useState([])
  const [modelPerformance, setModelPerformance] = useState([])
  const [bestModel, setBestModel] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const loadAnalytics = async () => {
    try {
      setLoading(true)
      setError(null)

      const [
        summaryData,
        diseaseData,
        monthlyData,
        performanceData,
      ] = await Promise.all([
        getAnalyticsSummary(),
        getDiseaseDistribution(),
        getMonthlyAnalytics(12),
        getModelPerformance(),
      ])

      setSummary(summaryData)

      const totalDiseases = diseaseData.total || 1

      setDiseaseDistribution(
        diseaseData.distribution.map((item) => ({
          name: item.disease,
          count: item.count,
          percentage: Math.round(
            (item.count / totalDiseases) * 100
          ),
        }))
      )

      setMonthlyActivity(
        monthlyData.data.map((item) => ({
          month: item.month_label,
          value: item.new_diagnoses,
        }))
      )

      setModelPerformance(performanceData.results || [])
      setBestModel(performanceData.best_model || '')
    } catch (err) {
      console.error('Failed to load analytics:', err)
      setError('Failed to load analytics data. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadAnalytics()
  }, [])

  const maxActivity = monthlyActivity.length
    ? Math.max(...monthlyActivity.map((item) => item.value), 1)
    : 1

  const STATS = summary
    ? [
        {
          label: 'Total Patients',
          value: summary.total_patients,
          code: 'PT',
        },
        {
          label: 'Total Diagnoses',
          value: summary.total_diagnoses,
          code: 'DX',
        },
        {
          label: 'Reports Analysed',
          value: summary.total_report_analyses,
          code: 'RA',
        },
        {
          label: 'High Risk Patients',
          value: summary.high_risk_patients,
          code: 'RK',
        },
        {
          label: 'Prediction Accuracy',
          value:
            summary.average_prediction_confidence !== null
              ? `${(summary.average_prediction_confidence * 100).toFixed(2)}%`
              : 'N/A',
          code: 'AC',
        },
        {
          label: 'AI Reviewed',
          value: summary.ai_reviewed_diagnoses,
          code: 'AI',
        },
      ]
    : []

  if (loading) {
    return (
      <div className={styles.page}>
        <section className={styles.header}>
          <p className={styles.eyebrow}>Analytics</p>
          <h1 className={styles.title}>Medical Analytics Dashboard</h1>
          <p className={styles.subtitle}>
            Loading analytics data...
          </p>
        </section>
      </div>
    )
  }

  return (
    <div className={styles.page}>
      <section className={styles.header}>
        <p className={styles.eyebrow}>Analytics</p>
        <h1 className={styles.title}>Medical Analytics Dashboard</h1>
        <p className={styles.subtitle}>
          View AI prediction performance, patient statistics, and overall
          clinical insights.
        </p>

        {error && (
          <p style={{ marginTop: '12px' }}>
            {error}
          </p>
        )}
      </section>

      {/* Statistics Section */}
      <section aria-labelledby="stats-heading" className={styles.section}>
        <h2 id="stats-heading" className={styles.sectionHeading}>
          Statistics
        </h2>

        <div className={styles.statsGrid}>
          {STATS.map((stat) => (
            <div className={styles.statCard} key={stat.label}>
              <div className={styles.statTop}>
                <span className={styles.badge} aria-hidden="true">
                  {stat.code}
                </span>

                <span className={styles.statLabel}>
                  {stat.label}
                </span>
              </div>

              <p className={styles.statValue}>
                {stat.value}
              </p>
            </div>
          ))}
        </div>
      </section>

      <div className={styles.splitGrid}>

        {/* Disease Distribution Card */}
        <section
          className={styles.card}
          aria-labelledby="disease-distribution-heading"
        >
          <h2
            id="disease-distribution-heading"
            className={styles.cardTitle}
          >
            Disease Distribution
          </h2>

          {diseaseDistribution.length > 0 ? (
            <ul className={styles.distributionList}>
              {diseaseDistribution.map((disease) => (
                <li
                  className={styles.distributionItem}
                  key={disease.name}
                >
                  <div className={styles.distributionTop}>
                    <span className={styles.distributionName}>
                      {disease.name}
                    </span>

                    <span className={styles.distributionPercentage}>
                      {disease.percentage}%
                    </span>
                  </div>

                  <div className={styles.distributionTrack}>
                    <div
                      className={styles.distributionFill}
                      style={{
                        width: `${disease.percentage}%`,
                      }}
                    />
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <p>No disease prediction data available.</p>
          )}
        </section>

        {/* Monthly Prediction Activity */}
        <section
          className={styles.card}
          aria-labelledby="monthly-activity-heading"
        >
          <h2
            id="monthly-activity-heading"
            className={styles.cardTitle}
          >
            Monthly Prediction Activity
          </h2>

          {monthlyActivity.length > 0 ? (
            <div
              className={styles.barChart}
              role="img"
              aria-label="Monthly prediction activity bar chart"
            >
              {monthlyActivity.map((item) => (
                <div
                  className={styles.barColumn}
                  key={item.month}
                >
                  <div className={styles.barTrack}>
                    <div
                      className={styles.bar}
                      style={{
                        height: `${(item.value / maxActivity) * 100}%`,
                      }}
                    />
                  </div>

                  <span className={styles.barLabel}>
                    {item.month}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p>No monthly analytics data available.</p>
          )}
        </section>
      </div>

      {/* Model Performance Card */}
      <section
        className={styles.card}
        aria-labelledby="model-performance-heading"
      >
        <h2
          id="model-performance-heading"
          className={styles.cardTitle}
        >
          Model Performance
          {bestModel && ` — Best Model: ${bestModel}`}
        </h2>

        <div className={styles.tableWrapper}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th scope="col">Model</th>
                <th scope="col">Accuracy</th>
                <th scope="col">Precision</th>
                <th scope="col">Recall</th>
                <th scope="col">F1 Score</th>
              </tr>
            </thead>

            <tbody>
              {modelPerformance.length > 0 ? (
                modelPerformance.map((model) => (
                  <tr key={model.model}>
                    <td data-label="Model">
                      {model.model}
                    </td>

                    <td data-label="Accuracy">
                      {(model.accuracy * 100).toFixed(2)}%
                    </td>

                    <td data-label="Precision">
                      {(model.precision * 100).toFixed(2)}%
                    </td>

                    <td data-label="Recall">
                      {(model.recall * 100).toFixed(2)}%
                    </td>

                    <td data-label="F1 Score">
                      {(model.f1_score * 100).toFixed(2)}%
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="5">
                    No model performance data available.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      {/* Recent AI Predictions */}
      <section
        className={styles.card}
        aria-labelledby="recent-predictions-heading"
      >
        <h2
          id="recent-predictions-heading"
          className={styles.cardTitle}
        >
          Recent AI Predictions
        </h2>

        <div className={styles.tableWrapper}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th scope="col">Patient</th>
                <th scope="col">Disease</th>
                <th scope="col">Confidence</th>
                <th scope="col">Risk</th>
                <th scope="col">Date</th>
              </tr>
            </thead>

            <tbody>
              {RECENT_PREDICTIONS.map((prediction) => (
                <tr
                  key={`${prediction.patient}-${prediction.date}`}
                >
                  <td data-label="Patient">
                    {prediction.patient}
                  </td>

                  <td data-label="Disease">
                    {prediction.disease}
                  </td>

                  <td data-label="Confidence">
                    {prediction.confidence}
                  </td>

                  <td data-label="Risk">
                    <RiskBadge level={prediction.risk} />
                  </td>

                  <td data-label="Date">
                    {prediction.date}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* System Overview Card */}
      <section
        className={styles.card}
        aria-labelledby="system-overview-heading"
      >
        <h2
          id="system-overview-heading"
          className={styles.cardTitle}
        >
          System Overview
        </h2>

        <ul className={styles.overviewList}>
          {SYSTEM_OVERVIEW.map((item) => (
            <li
              className={styles.overviewItem}
              key={item.label}
            >
              <span className={styles.overviewLabel}>
                {item.label}
              </span>

              <StatusBadge
                tone={item.tone}
                status={item.status}
              />
            </li>
          ))}
        </ul>
      </section>

      {/* Bottom Actions */}
      <section
        className={styles.actions}
        aria-label="Analytics dashboard actions"
      >
        <button
          type="button"
          className={styles.ghostButton}
          onClick={loadAnalytics}
        >
          Refresh
        </button>

        <button
          type="button"
          className={styles.secondaryButton}
        >
          Export Analytics
        </button>

        <button
          type="button"
          className={styles.primaryButton}
        >
          Generate Report
        </button>
      </section>
    </div>
  )
}

export default AnalyticsDashboard