import styles from './Patients.module.css'
import { useEffect, useState } from "react";
import api from "../../services/api";

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
  const [patients, setPatients] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadPatients() {
      try {
        const response = await api.get("/patients/");
        console.log(response.data);
        setPatients(response.data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }

    loadPatients();
  }, []);
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
                {patients.map((patient) => (
                  <tr key={patient.id}>
                    <td data-label="Patient ID">
                      <span className={styles.patientId}>{patient.id}</span>
                    </td>
                    <td data-label="Full Name">
                      <span className={styles.patientName}>{patient.first_name} {patient.last_name}</span>
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