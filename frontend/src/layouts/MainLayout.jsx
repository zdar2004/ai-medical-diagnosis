import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import Navbar from '../components/layout/Navbar/Navbar.jsx'
import Sidebar from '../components/layout/Sidebar/Sidebar.jsx'
import PageContainer from '../components/layout/PageContainer/PageContainer.jsx'
import styles from './MainLayout.module.css'

function MainLayout() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)

  const toggleSidebar = () => setIsSidebarOpen((open) => !open)
  const closeSidebar = () => setIsSidebarOpen(false)

  return (
    <div className={styles.shell}>
      <Navbar isSidebarOpen={isSidebarOpen} onMenuToggle={toggleSidebar} />

      <div style={{ display: 'flex', flex: 1, minHeight: 0, position: 'relative' }}>
        <Sidebar isOpen={isSidebarOpen} onNavigate={closeSidebar} />

        {isSidebarOpen && (
          <button
            type="button"
            aria-label="Close navigation menu"
            onClick={closeSidebar}
            style={{
              position: 'fixed',
              top: 'var(--header-height)',
              right: 0,
              bottom: 0,
              left: 0,
              margin: 0,
              padding: 0,
              border: 'none',
              backgroundColor: 'rgba(15, 27, 45, 0.4)',
              cursor: 'pointer',
              zIndex: 15,
            }}
          />
        )}

        <main className={styles.main} style={{ minWidth: 0 }} aria-label="Page content">
          <section aria-label="Page section">
            <PageContainer>
              <Outlet />
            </PageContainer>
          </section>
        </main>
      </div>

      <footer className={styles.footer}>
        <div className={styles.footerInner}>
          <span>&copy; {new Date().getFullYear()} MediAI CDSS</span>
          <span className={styles.footerNote}>Clinical decision support — for research &amp; educational use</span>
        </div>
      </footer>
    </div>
  )
}

export default MainLayout