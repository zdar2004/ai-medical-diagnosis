import { NavLink } from 'react-router-dom'
import styles from './Sidebar.module.css'

// Navigation items — each maps to a route via NavLink, with an SVG icon
// and a short mono badge, matching the existing sidebar visual language.
const NAV_ITEMS = [
  { label: 'Dashboard', to: '/dashboard', icon: 'dashboard', badge: 'DB' },
  { label: 'Patients', to: '/patients', icon: 'patients', badge: 'PT' },
  { label: 'Diagnosis', to: '/diagnosis', icon: 'diagnosis', badge: 'DX' },
  { label: 'Report Analysis', to: '/reports', icon: 'reports', badge: 'RA' },
  { label: 'Risk Assessment', to: '/risk', icon: 'risk', badge: 'RK' },
  { label: 'Analytics', to: '/analytics', icon: 'analytics', badge: 'AZ' },
  { label: 'Clinical Assistant', to: '/assistant', icon: 'assistant', badge: 'CA' },
]

function NavIcon({ name }) {
  switch (name) {
    case 'dashboard':
      return (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" aria-hidden="true">
          <rect x="3.5" y="3.5" width="7" height="7" rx="1.2" />
          <rect x="13.5" y="3.5" width="7" height="7" rx="1.2" />
          <rect x="3.5" y="13.5" width="7" height="7" rx="1.2" />
          <rect x="13.5" y="13.5" width="7" height="7" rx="1.2" />
        </svg>
      )
    case 'patients':
      return (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" aria-hidden="true">
          <circle cx="9" cy="8.5" r="2.8" />
          <path d="M3.5 19c1.2-3 3.3-4.5 5.5-4.5s4.3 1.5 5.5 4.5" strokeLinecap="round" />
          <circle cx="17" cy="8" r="2.2" />
          <path d="M15.2 14.8c1.9.4 3.4 1.9 4.3 4.2" strokeLinecap="round" />
        </svg>
      )
    case 'diagnosis':
      return (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" aria-hidden="true">
          <path
            d="M3.5 12h3.4l1.6-4 3 8 1.6-4h3.9"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          <path d="M17.5 12h3" strokeLinecap="round" />
        </svg>
      )
    case 'reports':
      return (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" aria-hidden="true">
          <path d="M7 3h7l5 5v13a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1Z" strokeLinejoin="round" />
          <path d="M14 3v5h5" strokeLinejoin="round" />
          <path d="M8.5 13h7M8.5 16.5h7" strokeLinecap="round" />
        </svg>
      )
    case 'risk':
      return (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" aria-hidden="true">
          <path
            d="M12 3.5 19.5 7v5.5c0 4.5-3.2 7.7-7.5 9-4.3-1.3-7.5-4.5-7.5-9V7L12 3.5Z"
            strokeLinejoin="round"
          />
          <path d="M12 8.5v4.2" strokeLinecap="round" />
          <path d="M12 15.8h.01" strokeLinecap="round" />
        </svg>
      )
    case 'analytics':
      return (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" aria-hidden="true">
          <path d="M4 20V10M10 20V4M16 20v-7M20 20v-4" strokeLinecap="round" />
        </svg>
      )
    case 'assistant':
      return (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" aria-hidden="true">
          <path
            d="M4 5.5h16v10H9.5L5 19v-3.5H4Z"
            strokeLinejoin="round"
          />
          <path d="M8 9.5h8M8 12.5h5" strokeLinecap="round" />
        </svg>
      )
    default:
      return null
  }
}

function Sidebar({ isOpen = false, onNavigate }) {
  const sidebarClassName = isOpen
    ? `${styles.sidebar} ${styles.sidebarOpen}`
    : styles.sidebar

  return (
    <aside className={sidebarClassName} aria-label="Primary navigation">
      <div className={styles.section}>
        <p className={styles.sectionLabel}>Workspace</p>
        <nav aria-label="Main navigation">
          <ul className={styles.list}>
            {NAV_ITEMS.map((item) => (
              <li key={item.label}>
                <NavLink
                  to={item.to}
                  onClick={onNavigate}
                  className={({ isActive }) =>
                    isActive ? `${styles.navItem} ${styles.navItemActive}` : styles.navItem
                  }
                >
                  <span className={styles.navIcon} aria-hidden="true">
                    <NavIcon name={item.icon} />
                  </span>
                  <span className={styles.navLabel}>{item.label}</span>
                  <span className={styles.badge} aria-hidden="true">
                    {item.badge}
                  </span>
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>
      </div>
    </aside>
  )
}

export default Sidebar