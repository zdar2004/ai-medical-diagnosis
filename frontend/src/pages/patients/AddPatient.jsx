import styles from './AddPatient.module.css'

function AddPatient() {
  return (
    <div className={styles.page}>
      <section className={styles.header}>
        <p className={styles.eyebrow}>Patient Registration</p>
        <h1 className={styles.title}>Add Patient</h1>
        <p className={styles.subtitle}>
          Register a new patient in the MediSys system. Complete the required
          information before creating the patient record.
        </p>
      </section>

      <form className={styles.form} onSubmit={(event) => event.preventDefault()}>
        {/* Patient Information */}

        <section className={styles.card}>
          <div className={styles.cardHeader}>
            <h2 className={styles.cardTitle}>Patient Information</h2>
            <p className={styles.cardDescription}>
              Basic demographic information about the patient.
            </p>
          </div>

          <div className={styles.grid}>
            <div className={styles.field}>
              <label className={styles.label}>
                First Name <span className={styles.required}>*</span>
              </label>

              <input
                type="text"
                className={styles.input}
                placeholder="Enter first name"
                defaultValue=""
              />
            </div>

            <div className={styles.field}>
              <label className={styles.label}>
                Last Name <span className={styles.required}>*</span>
              </label>

              <input
                type="text"
                className={styles.input}
                placeholder="Enter last name"
                defaultValue=""
              />
            </div>

            <div className={styles.field}>
              <label className={styles.label}>
                CNIC <span className={styles.required}>*</span>
              </label>

              <input
                type="text"
                className={styles.input}
                placeholder="35202-1234567-1"
                defaultValue=""
              />
            </div>

            <div className={styles.field}>
              <label className={styles.label}>
                Date of Birth <span className={styles.required}>*</span>
              </label>

              <input
                type="date"
                className={styles.input}
                defaultValue=""
              />
            </div>

            <div className={styles.field}>
              <label className={styles.label}>
                Gender <span className={styles.required}>*</span>
              </label>

              <select className={styles.select} defaultValue="">
                <option value="" disabled>
                  Select gender
                </option>

                <option>Male</option>
                <option>Female</option>
                <option>Other</option>
              </select>
            </div>

            <div className={styles.field}>
              <label className={styles.label}>
                Phone Number <span className={styles.required}>*</span>
              </label>

              <input
                type="tel"
                className={styles.input}
                placeholder="+92 300 1234567"
                defaultValue=""
              />
            </div>

            <div className={styles.field}>
              <label className={styles.label}>
                Email Address
              </label>

              <input
                type="email"
                className={styles.input}
                placeholder="patient@example.com"
                defaultValue=""
              />
            </div>

            <div className={styles.field}>
              <label className={styles.label}>
                Blood Group
              </label>

              <select className={styles.select} defaultValue="">
                <option value="">Select blood group</option>

                <option>A+</option>
                <option>A-</option>
                <option>B+</option>
                <option>B-</option>
                <option>AB+</option>
                <option>AB-</option>
                <option>O+</option>
                <option>O-</option>
              </select>
            </div>
          </div>
        </section>

        {/* Medical Information */}

        <section className={styles.card}>
          <div className={styles.cardHeader}>
            <h2 className={styles.cardTitle}>Medical Information</h2>
            <p className={styles.cardDescription}>
              Optional medical details available during patient registration.
            </p>
          </div>

          <div className={styles.grid}>
            <div className={styles.field}>
              <label className={styles.label}>
                Primary Diagnosis
              </label>

              <input
                type="text"
                className={styles.input}
                placeholder="Enter diagnosis"
                defaultValue=""
              />
            </div>

            <div className={styles.field}>
              <label className={styles.label}>
                Allergies
              </label>

              <input
                type="text"
                className={styles.input}
                placeholder="Known allergies"
                defaultValue=""
              />
            </div>

            <div className={styles.fieldFull}>
              <label className={styles.label}>
                Medical History
              </label>

              <textarea
                className={styles.textarea}
                rows="5"
                placeholder="Previous illnesses, surgeries, chronic conditions..."
                defaultValue=""
              />
            </div>

            <div className={styles.fieldFull}>
              <label className={styles.label}>
                Address
              </label>

              <textarea
                className={styles.textarea}
                rows="3"
                placeholder="Enter patient address"
                defaultValue=""
              />
            </div>
          </div>
        </section>

        {/* Actions */}

        <section className={styles.actions}>
          <button
            type="button"
            className={styles.secondaryButton}
          >
            Cancel
          </button>

          <button
            type="submit"
            className={styles.primaryButton}
          >
            Register Patient
          </button>
        </section>
      </form>
    </div>
  )
}

export default AddPatient