import styles from './Dashboard.module.css'

// Static, illustrative data only — no API, no business logic.
// `accent` only selects a decorative border color; no behavior depends on it.
const STATS = [
  { label: 'Total Patients', value: '1,284', meta: '+32 this month', code: 'PT', accent: 'primary' },
  { label: "Today's Diagnoses", value: '18', meta: '6 pending review', code: 'DX', accent: 'accent' },
  { label: 'High Risk Patients', value: '27', meta: 'Needs follow-up', code: 'RK', accent: 'danger' },
  { label: 'Reports Analysed', value: '342', meta: '+14 this week', code: 'RA', accent: 'success' },
  { label: 'Prediction Accuracy', value: '96.4%', meta: 'Last 30 days', code: 'AC', accent: 'warning' },
]

const QUICK_ACTIONS = [
  {
    label: 'Add Patient',
    description: 'Register a new patient record',
    code: 'PT',
  },
  {
    label: 'New Diagnosis',
    description: 'Start a diagnosis workflow',
    code: 'DX',
  },
  {
    label: 'Analyse Report',
    description: 'Run analysis on a medical report',
    code: 'RA',
  },
  {
    label: 'Risk Assessment',
    description: 'Evaluate patient risk factors',
    code: 'RK',
  },
]

const RECENT_ACTIVITY = [
  { label: 'Patient added', detail: 'New patient record created', time: '12 min ago' },
  { label: 'Diagnosis completed', detail: 'Case reviewed and finalised', time: '48 min ago' },
  { label: 'Medical report analysed', detail: 'Lab report processed', time: '1 hr ago' },
  { label: 'Risk assessment generated', detail: 'Risk profile updated', time: '3 hr ago' },
  { label: 'Prediction completed', detail: 'Diagnostic prediction generated', time: 'Yesterday' },
]

const UPCOMING = [
  { label: 'Review pending reports', detail: '6 reports awaiting review' },
  { label: 'High risk patient follow-up', detail: '4 patients due for check-in' },
  { label: 'Update patient records', detail: '9 records flagged incomplete' },
]

const ACCENT_CLASS = {
  primary: 'accentPrimary',
  accent: 'accentAccent',
  danger: 'accentDanger',
  success: 'accentSuccess',
  warning: 'accentWarning',
}

function Dashboard() {
  return (
    <div className={styles.page}>
      <section className={styles.hero}>
        <div className={styles.heroText}>
          <p className={styles.eyebrow}>Overview</p>
          <h1 className={styles.title}>Welcome back, Doctor</h1>
          <p className={styles.subtitle}>
            Here&apos;s a summary of your patients, diagnoses, and recent
            workspace activity.
          </p>
        </div>
        <div className={styles.heroBadge} aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
            <path d="M12 21s-7-4.35-9.5-9A5.5 5.5 0 0 1 12 5a5.5 5.5 0 0 1 9.5 7c-2.5 4.65-9.5 9-9.5 9Z" />
          </svg>
        </div>
      </section>

      <section aria-labelledby="stats-heading" className={styles.section}>
        <h2 id="stats-heading" className={styles.sectionHeading}>
          Statistics
        </h2>
        <div className={styles.statsGrid}>
          {STATS.map((stat) => (
            <div
              className={`${styles.statCard} ${styles[ACCENT_CLASS[stat.accent]]}`}
              key={stat.label}
            >
              <div className={styles.statTop}>
                <span className={styles.badge} aria-hidden="true">
                  {stat.code}
                </span>
                <span className={styles.statLabel}>{stat.label}</span>
              </div>
              <p className={styles.statValue}>{stat.value}</p>
              <p className={styles.statMeta}>{stat.meta}</p>
            </div>
          ))}
        </div>
      </section>

      <section aria-labelledby="actions-heading" className={styles.section}>
        <h2 id="actions-heading" className={styles.sectionHeading}>
          Quick Actions
        </h2>
        <div className={styles.actionsGrid}>
          {QUICK_ACTIONS.map((action) => (
            <button type="button" className={styles.actionCard} key={action.label}>
              <span className={styles.badge} aria-hidden="true">
                {action.code}
              </span>
              <span className={styles.actionText}>
                <span className={styles.actionLabel}>{action.label}</span>
                <span className={styles.actionDescription}>{action.description}</span>
              </span>
              <svg className={styles.actionArrow} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" aria-hidden="true">
                <path d="M9 6l6 6-6 6" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </button>
          ))}
        </div>
      </section>

      <div className={styles.lowerGrid}>
        <section aria-labelledby="activity-heading" className={styles.section}>
          <h2 id="activity-heading" className={styles.sectionHeading}>
            Recent Activity
          </h2>
          <ul className={styles.activityList}>
            {RECENT_ACTIVITY.map((activity) => (
              <li className={styles.activityItem} key={activity.label}>
                <span className={styles.activityDot} aria-hidden="true" />
                <div className={styles.activityBody}>
                  <p className={styles.activityLabel}>{activity.label}</p>
                  <p className={styles.activityDetail}>{activity.detail}</p>
                </div>
                <span className={styles.activityTime}>{activity.time}</span>
              </li>
            ))}
          </ul>
        </section>

        <section aria-labelledby="upcoming-heading" className={styles.section}>
          <h2 id="upcoming-heading" className={styles.sectionHeading}>
            Upcoming
          </h2>
          <ul className={styles.upcomingList}>
            {UPCOMING.map((item) => (
              <li className={styles.upcomingItem} key={item.label}>
                <p className={styles.upcomingLabel}>{item.label}</p>
                <p className={styles.upcomingDetail}>{item.detail}</p>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </div>
  )
}

export default Dashboard