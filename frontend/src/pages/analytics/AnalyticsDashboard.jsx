import styles from './AnalyticsDashboard.module.css'

// Static, illustrative data only — no API, no chart libraries, no business logic.
const STATS = [
  { label: 'Total Patients', value: '1,248', code: 'PT' },
  { label: "Today's Diagnoses", value: '42', code: 'DX' },
  { label: 'Reports Analysed', value: '386', code: 'RA' },
  { label: 'High Risk Patients', value: '96', code: 'RK' },
  { label: 'Prediction Accuracy', value: '94%', code: 'AC' },
  { label: 'Active Doctors', value: '12', code: 'DR' },
]

const DISEASE_DISTRIBUTION = [
  { name: 'Diabetes', percentage: 34 },
  { name: 'Hypertension', percentage: 24 },
  { name: 'Pneumonia', percentage: 18 },
  { name: 'Heart Disease', percentage: 13 },
  { name: 'Others', percentage: 11 },
]

const MONTHLY_ACTIVITY = [
  { month: 'Jan', value: 45 },
  { month: 'Feb', value: 58 },
  { month: 'Mar', value: 40 },
  { month: 'Apr', value: 72 },
  { month: 'May', value: 65 },
  { month: 'Jun', value: 88 },
  { month: 'Jul', value: 76 },
]

const MODEL_PERFORMANCE = [
  { model: 'Logistic Regression', accuracy: '89%', precision: '87%', recall: '85%', f1: '86%' },
  { model: 'Random Forest', accuracy: '93%', precision: '91%', recall: '90%', f1: '90%' },
  { model: 'SVM', accuracy: '88%', precision: '86%', recall: '84%', f1: '85%' },
  { model: 'XGBoost', accuracy: '94%', precision: '93%', recall: '92%', f1: '92%' },
]

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
  return <span className={`${styles.riskBadge} ${styles[variant]}`}>{level}</span>
}

function StatusBadge({ tone, status }) {
  const statusClass = tone === 'bad' ? styles.statusBad : styles.statusGood
  return <span className={`${styles.statusBadge} ${statusClass}`}>{status}</span>
}

function AnalyticsDashboard() {
  const maxActivity = Math.max(...MONTHLY_ACTIVITY.map((item) => item.value))

  return (
    <div className={styles.page}>
      <section className={styles.header}>
        <p className={styles.eyebrow}>Analytics</p>
        <h1 className={styles.title}>Medical Analytics Dashboard</h1>
        <p className={styles.subtitle}>
          View AI prediction performance, patient statistics, and overall
          clinical insights.
        </p>
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
                <span className={styles.statLabel}>{stat.label}</span>
              </div>
              <p className={styles.statValue}>{stat.value}</p>
            </div>
          ))}
        </div>
      </section>

      <div className={styles.splitGrid}>
        {/* Disease Distribution Card */}
        <section className={styles.card} aria-labelledby="disease-distribution-heading">
          <h2 id="disease-distribution-heading" className={styles.cardTitle}>
            Disease Distribution
          </h2>
          <ul className={styles.distributionList}>
            {DISEASE_DISTRIBUTION.map((disease) => (
              <li className={styles.distributionItem} key={disease.name}>
                <div className={styles.distributionTop}>
                  <span className={styles.distributionName}>{disease.name}</span>
                  <span className={styles.distributionPercentage}>{disease.percentage}%</span>
                </div>
                <div className={styles.distributionTrack}>
                  <div
                    className={styles.distributionFill}
                    style={{ width: `${disease.percentage}%` }}
                  />
                </div>
              </li>
            ))}
          </ul>
        </section>

        {/* Monthly Prediction Activity */}
        <section className={styles.card} aria-labelledby="monthly-activity-heading">
          <h2 id="monthly-activity-heading" className={styles.cardTitle}>
            Monthly Prediction Activity
          </h2>
          <div className={styles.barChart} role="img" aria-label="Monthly prediction activity bar chart">
            {MONTHLY_ACTIVITY.map((item) => (
              <div className={styles.barColumn} key={item.month}>
                <div className={styles.barTrack}>
                  <div
                    className={styles.bar}
                    style={{ height: `${(item.value / maxActivity) * 100}%` }}
                  />
                </div>
                <span className={styles.barLabel}>{item.month}</span>
              </div>
            ))}
          </div>
        </section>
      </div>

      {/* Model Performance Card */}
      <section className={styles.card} aria-labelledby="model-performance-heading">
        <h2 id="model-performance-heading" className={styles.cardTitle}>
          Model Performance
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
              {MODEL_PERFORMANCE.map((model) => (
                <tr key={model.model}>
                  <td data-label="Model">{model.model}</td>
                  <td data-label="Accuracy">{model.accuracy}</td>
                  <td data-label="Precision">{model.precision}</td>
                  <td data-label="Recall">{model.recall}</td>
                  <td data-label="F1 Score">{model.f1}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Recent AI Predictions */}
      <section className={styles.card} aria-labelledby="recent-predictions-heading">
        <h2 id="recent-predictions-heading" className={styles.cardTitle}>
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
                <tr key={`${prediction.patient}-${prediction.date}`}>
                  <td data-label="Patient">{prediction.patient}</td>
                  <td data-label="Disease">{prediction.disease}</td>
                  <td data-label="Confidence">{prediction.confidence}</td>
                  <td data-label="Risk">
                    <RiskBadge level={prediction.risk} />
                  </td>
                  <td data-label="Date">{prediction.date}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* System Overview Card */}
      <section className={styles.card} aria-labelledby="system-overview-heading">
        <h2 id="system-overview-heading" className={styles.cardTitle}>
          System Overview
        </h2>
        <ul className={styles.overviewList}>
          {SYSTEM_OVERVIEW.map((item) => (
            <li className={styles.overviewItem} key={item.label}>
              <span className={styles.overviewLabel}>{item.label}</span>
              <StatusBadge tone={item.tone} status={item.status} />
            </li>
          ))}
        </ul>
      </section>

      {/* Bottom Actions */}
      <section className={styles.actions} aria-label="Analytics dashboard actions">
        <button type="button" className={styles.ghostButton}>
          Refresh
        </button>
        <button type="button" className={styles.secondaryButton}>
          Export Analytics
        </button>
        <button type="button" className={styles.primaryButton}>
          Generate Report
        </button>
      </section>
    </div>
  )
}

export default AnalyticsDashboard