import styles from './Patients.module.css'

// Static, illustrative data only — no API, no business logic.
const PATIENTS = [
  {
    id: 'PT-1042',
    name: 'Amelia Carter',
    age: 54,
    gender: 'Female',
    diagnosis: 'Type 2 Diabetes',
    status: 'Active',
    lastVisit: '2026-06-28',
  },
  {
    id: 'PT-1043',
    name: 'Daniel Osei',
    age: 67,
    gender: 'Male',
    diagnosis: 'Acute Myocardial Infarction',
    status: 'Critical',
    lastVisit: '2026-07-01',
  },
  {
    id: 'PT-1044',
    name: 'Priya Nair',
    age: 34,
    gender: 'Female',
    diagnosis: 'Community-Acquired Pneumonia',
    status: 'Recovered',
    lastVisit: '2026-06-15',
  },
  {
    id: 'PT-1045',
    name: 'Marcus Webb',
    age: 45,
    gender: 'Male',
    diagnosis: 'Hypertension',
    status: 'Follow-up',
    lastVisit: '2026-06-30',
  },
  {
    id: 'PT-1046',
    name: 'Isabella Rossi',
    age: 29,
    gender: 'Female',
    diagnosis: 'Migraine with Aura',
    status: 'Active',
    lastVisit: '2026-06-27',
  },
  {
    id: 'PT-1047',
    name: 'Kenji Watanabe',
    age: 71,
    gender: 'Male',
    diagnosis: 'Chronic Kidney Disease, Stage 3',
    status: 'Critical',
    lastVisit: '2026-07-02',
  },
  {
    id: 'PT-1048',
    name: 'Grace Mensah',
    age: 38,
    gender: 'Female',
    diagnosis: 'Asthma Exacerbation',
    status: 'Recovered',
    lastVisit: '2026-06-10',
  },
  {
    id: 'PT-1049',
    name: 'Tomasz Nowak',
    age: 58,
    gender: 'Male',
    diagnosis: 'Atrial Fibrillation',
    status: 'Follow-up',
    lastVisit: '2026-06-24',
  },
  {
    id: 'PT-1050',
    name: 'Fatima Al-Sayed',
    age: 62,
    gender: 'Female',
    diagnosis: 'Osteoarthritis',
    status: 'Active',
    lastVisit: '2026-06-29',
  },
  {
    id: 'PT-1051',
    name: 'Liam O\u2019Brien',
    age: 49,
    gender: 'Male',
    diagnosis: 'Gastroesophageal Reflux Disease',
    status: 'Follow-up',
    lastVisit: '2026-06-21',
  },
]

const STATUS_OPTIONS = ['All Statuses', 'Active', 'Critical', 'Recovered', 'Follow-up']

const STATUS_BADGE_CLASS = {
  Active: styles.badgeActive,
  Critical: styles.badgeCritical,
  Recovered: styles.badgeRecovered,
  'Follow-up': styles.badgeFollowUp,
}

// Toggle this to preview the empty state — kept static, no hooks needed.
const SHOW_EMPTY_STATE = false

function StatusBadge({ status }) {
  const badgeClass = STATUS_BADGE_CLASS[status] || styles.badgeFollowUp
  return <span className={`${styles.badge} ${badgeClass}`}>{status}</span>
}

function Patients() {
  return (
    <div className={styles.page}>
      <section className={styles.header}>
        <p className={styles.eyebrow}>Patient Management</p>
        <h1 className={styles.title}>Patients</h1>
        <p className={styles.subtitle}>
          Manage patient records and monitor patient information.
        </p>
      </section>

      <section className={styles.actionBar} aria-label="Patient filters and actions">
        <div className={styles.filters}>
          <div className={styles.searchField}>
            <svg
              className={styles.searchIcon}
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.75"
              aria-hidden="true"
            >
              <circle cx="11" cy="11" r="6.5" />
              <path d="M20 20L15.8 15.8" strokeLinecap="round" />
            </svg>
            <input
              type="text"
              className={styles.searchInput}
              placeholder="Search patient by name or ID"
              aria-label="Search patient"
            />
          </div>

          <select className={styles.statusSelect} aria-label="Filter by status" defaultValue="All Statuses">
            {STATUS_OPTIONS.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </div>

        <div className={styles.actions}>
          <button type="button" className={styles.secondaryButton} disabled>
            Export
          </button>
          <button type="button" className={styles.primaryButton}>
            Add Patient
          </button>
        </div>
      </section>

      {SHOW_EMPTY_STATE ? (
        <section className={styles.emptyState}>
          <p className={styles.emptyTitle}>No patients found</p>
          <p className={styles.emptyMessage}>
            Try adjusting your search or filter criteria, or add a new patient to
            get started.
          </p>
          <button type="button" className={styles.primaryButton}>
            Add Patient
          </button>
        </section>
      ) : (
        <section className={styles.tableSection} aria-label="Patient records">
          <div className={styles.tableWrapper}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th scope="col">Patient ID</th>
                  <th scope="col">Full Name</th>
                  <th scope="col">Age</th>
                  <th scope="col">Gender</th>
                  <th scope="col">Diagnosis</th>
                  <th scope="col">Status</th>
                  <th scope="col">Last Visit</th>
                  <th scope="col">Actions</th>
                </tr>
              </thead>
              <tbody>
                {PATIENTS.map((patient) => (
                  <tr key={patient.id}>
                    <td data-label="Patient ID">
                      <span className={styles.patientId}>{patient.id}</span>
                    </td>
                    <td data-label="Full Name">
                      <span className={styles.patientName}>{patient.name}</span>
                    </td>
                    <td data-label="Age">{patient.age}</td>
                    <td data-label="Gender">{patient.gender}</td>
                    <td data-label="Diagnosis">{patient.diagnosis}</td>
                    <td data-label="Status">
                      <StatusBadge status={patient.status} />
                    </td>
                    <td data-label="Last Visit">{patient.lastVisit}</td>
                    <td data-label="Actions">
                      <div className={styles.rowActions}>
                        <button type="button" className={styles.rowAction}>
                          View
                        </button>
                        <button type="button" className={styles.rowAction}>
                          Edit
                        </button>
                        <button type="button" className={`${styles.rowAction} ${styles.rowActionDanger}`}>
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </div>
  )
}

export default Patients