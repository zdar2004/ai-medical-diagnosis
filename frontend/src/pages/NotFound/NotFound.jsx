import { Link } from 'react-router-dom'
import styles from './NotFound.module.css'

function NotFound() {
  return (
    <section className={styles.wrapper}>
      <p className={styles.code}>404</p>
      <h1 className={styles.title}>This chart doesn&apos;t exist</h1>
      <p className={styles.message}>
        The page you&apos;re looking for isn&apos;t part of the workspace. Check the
        address or head back to the home page.
      </p>
      <Link to="/" className={styles.action}>
        Back to home
      </Link>
    </section>
  )
}

export default NotFound
