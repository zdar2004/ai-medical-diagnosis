import { Link } from 'react-router-dom'
import styles from './Home.module.css'

function Home() {
  return (
    <>
      <section className={styles.hero}>
        <div className={styles.heroInner}>
          <p className={styles.eyebrow}>Clinical Decision Support</p>
          <h1 className={styles.title}>
            Structured, evidence-aware support for the moment a diagnosis is made.
          </h1>
          <p className={styles.lead}>
            MediSysAI CDS brings patient data, clinical history, and AI-assisted analysis
            into a single workspace — helping clinicians reach a diagnosis with more
            context, not less scrutiny.
          </p>
          <div className={styles.actions}>
            <Link to="/login" className={styles.primaryAction}>
              Sign in to your workspace
            </Link>
          </div>
        </div>
      </section>

      <section className={styles.workflow} aria-labelledby="workflow-heading">
        <h2 id="workflow-heading" className={styles.workflowHeading}>
          How a case moves through the system
        </h2>
        <ol className={styles.steps}>
          <li className={styles.step}>
            <span className={styles.stepIndex}>01</span>
            <h3 className={styles.stepTitle}>Capture</h3>
            <p>Patient history, symptoms, and clinical data are recorded in a structured intake.</p>
          </li>
          <li className={styles.step}>
            <span className={styles.stepIndex}>02</span>
            <h3 className={styles.stepTitle}>Analyze</h3>
            <p>The case is assessed against clinical patterns to surface relevant considerations.</p>
          </li>
          <li className={styles.step}>
            <span className={styles.stepIndex}>03</span>
            <h3 className={styles.stepTitle}>Decide</h3>
            <p>The clinician reviews the supporting evidence and makes the final call.</p>
          </li>
        </ol>
      </section>

      <section className={styles.notice}>
        <p>
          This platform assists clinical judgment. It does not replace the expertise
          and responsibility of a licensed medical professional.
        </p>
      </section>
    </>
  )
}

export default Home
