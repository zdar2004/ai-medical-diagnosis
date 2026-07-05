import styles from './PageContainer.module.css'

function PageContainer({ children }) {
  return (
    <main className={styles.container}>
      <div className={styles.inner}>{children}</div>
    </main>
  )
}

export default PageContainer
