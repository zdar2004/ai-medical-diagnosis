import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import Navbar from '../../components/layout/Navbar/Navbar.jsx'
import Sidebar from '../../components/layout/Sidebar/Sidebar.jsx'
import PageContainer from '../../components/layout/PageContainer/PageContainer.jsx'
import styles from './DashboardLayout.module.css'

// Reusable app shell for authenticated/dashboard-style pages.
// Not wired into the router yet — this component is intentionally
// self-contained so it can be adopted as a layout route later.
function DashboardLayout() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)

  const toggleSidebar = () => setIsSidebarOpen((open) => !open)
  const closeSidebar = () => setIsSidebarOpen(false)

  return (
    <div className={styles.shell}>
      <Navbar isSidebarOpen={isSidebarOpen} onMenuToggle={toggleSidebar} />

      <div className={styles.body}>
        <Sidebar isOpen={isSidebarOpen} onNavigate={closeSidebar} />

        {isSidebarOpen && (
          <button
            type="button"
            className={styles.backdrop}
            aria-label="Close navigation menu"
            onClick={closeSidebar}
          />
        )}

        <PageContainer>
          <Outlet />
        </PageContainer>
      </div>
    </div>
  )
}

export default DashboardLayout
