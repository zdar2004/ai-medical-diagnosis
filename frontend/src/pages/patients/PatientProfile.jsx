import styles from './PatientProfile.module.css'

const PATIENT = {
  id: 'PT-1042',
  firstName: 'Amelia',
  lastName: 'Carter',
  age: 54,
  gender: 'Female',
  dob: '1972-03-15',
  bloodGroup: 'O+',
  phone: '+92 300 1234567',
  email: 'amelia.carter@example.com',
  address: 'Lahore, Pakistan',
}

const MEDICAL = {
  diagnosis: 'Type 2 Diabetes',
  allergies: 'Penicillin',
  history:
    'Diagnosed with Type 2 Diabetes in 2019. Hypertension controlled with medication.',
}

const VISITS = [
  {
    date: '2026-07-01',
    doctor: 'Dr. Sarah Ahmed',
    reason: 'Routine Follow-up',
    status: 'Completed',
  },
  {
    date: '2026-06-10',
    doctor: 'Dr. Sarah Ahmed',
    reason: 'Blood Sugar Review',
    status: 'Completed',
  },
  {
    date: '2026-05-02',
    doctor: 'Dr. Imran Khan',
    reason: 'General Checkup',
    status: 'Completed',
  },
]

function InfoRow({ label, value }) {
  return (
    <div className={styles.infoRow}>
      <span className={styles.label}>{label}</span>
      <span className={styles.value}>{value}</span>
    </div>
  )
}

function PatientProfile() {
  return (
    <div className={styles.page}>
      <section className={styles.header}>
        <p className={styles.eyebrow}>Patient Details</p>

        <h1 className={styles.title}>
          {PATIENT.firstName} {PATIENT.lastName}
        </h1>

        <p className={styles.subtitle}>
          View demographic information, medical history and recent visits.
        </p>
      </section>

      <section className={styles.profileBanner}>
        <div className={styles.avatar}>
          {PATIENT.firstName.charAt(0)}
          {PATIENT.lastName.charAt(0)}
        </div>

        <div className={styles.profileMeta}>
          <h2>
            {PATIENT.firstName} {PATIENT.lastName}
          </h2>

          <p>{PATIENT.id}</p>

          <div className={styles.badges}>
            <span className={styles.badge}>
              {PATIENT.gender}
            </span>

            <span className={styles.badge}>
              {PATIENT.age} Years
            </span>

            <span className={styles.badgePrimary}>
              {PATIENT.bloodGroup}
            </span>
          </div>
        </div>
      </section>

      <div className={styles.grid}>
        <section className={styles.card}>
          <div className={styles.cardHeader}>
            <h2 className={styles.cardTitle}>
              Personal Information
            </h2>
          </div>

          <div className={styles.infoList}>
            <InfoRow label="Patient ID" value={PATIENT.id} />
            <InfoRow label="Date of Birth" value={PATIENT.dob} />
            <InfoRow label="Gender" value={PATIENT.gender} />
            <InfoRow label="Phone" value={PATIENT.phone} />
            <InfoRow label="Email" value={PATIENT.email} />
            <InfoRow label="Address" value={PATIENT.address} />
          </div>
        </section>

        <section className={styles.card}>
          <div className={styles.cardHeader}>
            <h2 className={styles.cardTitle}>
              Medical Information
            </h2>
          </div>

          <div className={styles.infoList}>
            <InfoRow
              label="Primary Diagnosis"
              value={MEDICAL.diagnosis}
            />

            <InfoRow
              label="Blood Group"
              value={PATIENT.bloodGroup}
            />

            <InfoRow
              label="Known Allergies"
              value={MEDICAL.allergies}
            />

            <div className={styles.history}>
              <p className={styles.label}>
                Medical History
              </p>

              <p className={styles.historyText}>
                {MEDICAL.history}
              </p>
            </div>
          </div>
        </section>
      </div>

      <section className={styles.card}>
        <div className={styles.cardHeader}>
          <h2 className={styles.cardTitle}>
            Recent Visits
          </h2>
        </div>

        <div className={styles.tableWrapper}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Date</th>
                <th>Doctor</th>
                <th>Reason</th>
                <th>Status</th>
              </tr>
            </thead>

            <tbody>
              {VISITS.map((visit) => (
                <tr key={visit.date}>
                  <td>{visit.date}</td>

                  <td>{visit.doctor}</td>

                  <td>{visit.reason}</td>

                  <td>
                    <span className={styles.status}>
                      {visit.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  )
}

export default PatientProfile