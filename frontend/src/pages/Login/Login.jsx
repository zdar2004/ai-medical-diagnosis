import { useState } from 'react'
import { Link } from 'react-router-dom'
import styles from './Login.module.css'

function Login() {
  const [formData, setFormData] = useState({ email: '', password: '' })

  const handleChange = (event) => {
    const { name, value } = event.target
    setFormData((previous) => ({ ...previous, [name]: value }))
  }

  const handleSubmit = (event) => {
    // Intentionally not wired up yet — the backend integration will
    // replace this once the API layer is implemented.
    event.preventDefault()
  }

  return (
    <section className={styles.wrapper}>
      <div className={styles.card}>
        <p className={styles.eyebrow}>Clinician access</p>
        <h1 className={styles.title}>Sign in</h1>
        <p className={styles.subtitle}>
          Enter your credentials to access the clinical workspace.
        </p>

        <form className={styles.form} onSubmit={handleSubmit} noValidate>
          <label className={styles.field}>
            <span className={styles.label}>Email</span>
            <input
              type="email"
              name="email"
              autoComplete="email"
              value={formData.email}
              onChange={handleChange}
              className={styles.input}
              placeholder="you@hospital.org"
            />
          </label>

          <label className={styles.field}>
            <span className={styles.label}>Password</span>
            <input
              type="password"
              name="password"
              autoComplete="current-password"
              value={formData.password}
              onChange={handleChange}
              className={styles.input}
              placeholder="••••••••"
            />
          </label>

          <button type="submit" className={styles.submit}>
            Sign in
          </button>
        </form>

        <p className={styles.footnote}>
          Not a member of this workspace? <Link to="/">Return home</Link>.
        </p>
      </div>
    </section>
  )
}

export default Login
