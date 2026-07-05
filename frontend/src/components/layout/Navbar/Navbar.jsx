import { useLocation } from 'react-router-dom'
import styles from './Navbar.module.css'

// Maps a pathname to a page title and a breadcrumb trail.
// Static lookup only — no routing logic beyond reading the current path.
const PAGE_INFO = {
  '/': { title: 'Home', breadcrumb: ['Home'] },
  '/dashboard': { title: 'Dashboard', breadcrumb: ['Home', 'Dashboard'] },
  '/patients': { title: 'Patients', breadcrumb: ['Home', 'Patients'] },
  '/patients/add': { title: 'Add Patient', breadcrumb: ['Home', 'Patients', 'Add Patient'] },
  '/patients/profile': { title: 'Patient Profile', breadcrumb: ['Home', 'Patients', 'Patient Profile'] },
  '/diagnosis': { title: 'Diagnosis', breadcrumb: ['Home', 'Diagnosis'] },
  '/diagnosis/result': { title: 'Diagnosis Result', breadcrumb: ['Home', 'Diagnosis', 'Diagnosis Result'] },
  '/reports': { title: 'Report Analysis', breadcrumb: ['Home', 'Report Analysis'] },
  '/risk': { title: 'Risk Assessment', breadcrumb: ['Home', 'Risk Assessment'] },
  '/analytics': { title: 'Analytics Dashboard', breadcrumb: ['Home', 'Analytics Dashboard'] },
  '/assistant': { title: 'Clinical Assistant', breadcrumb: ['Home', 'Clinical Assistant'] },
}

const DEFAULT_PAGE_INFO = { title: 'MediAI CDSS', breadcrumb: ['Home'] }

// Static, illustrative user data only — no authentication, no API.
const CURRENT_USER = {
  name: 'Dr. Sarah Malik',
  role: 'Cardiologist',
}

function getPageInfo(pathname) {
  return PAGE_INFO[pathname] || DEFAULT_PAGE_INFO
}

function Breadcrumb({ trail }) {
  return (
    <nav aria-label="Breadcrumb">
      <ol className={styles.breadcrumb}>
        {trail.map((segment, index) => (
          <li className={styles.breadcrumbItem} key={segment}>
            <span className={index === trail.length - 1 ? styles.breadcrumbCurrent : undefined}>
              {segment}
            </span>
            {index < trail.length - 1 && (
              <span className={styles.breadcrumbSeparator} aria-hidden="true">
                /
              </span>
            )}
          </li>
        ))}
      </ol>
    </nav>
  )
}

function Navbar({ isSidebarOpen = false, onMenuToggle }) {
  const location = useLocation()
  const { title, breadcrumb } = getPageInfo(location.pathname)

  return (
    <header className={styles.navbar}>
      <div className={styles.left}>
        <button
          type="button"
          className={styles.menuButton}
          onClick={onMenuToggle}
          aria-label={isSidebarOpen ? 'Close navigation menu' : 'Open navigation menu'}
          aria-expanded={isSidebarOpen}
        >
          <span className={styles.menuBar} />
          <span className={styles.menuBar} />
          <span className={styles.menuBar} />
        </button>

        <div className={styles.titleBlock}>
          <h1 className={styles.pageTitle}>{title}</h1>
          <Breadcrumb trail={breadcrumb} />
        </div>
      </div>

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
          placeholder="Search patients, diagnoses, reports..."
          aria-label="Search workspace"
        />
      </div>

      <div className={styles.right}>
        <button type="button" className={styles.iconButton} aria-label="Notifications">
          <svg
            className={styles.icon}
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.75"
            aria-hidden="true"
          >
            <path
              d="M6 9a6 6 0 0 1 12 0c0 4.2 1.4 5.6 1.4 5.6H4.6S6 13.2 6 9Z"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            <path d="M9.5 17.2a2.5 2.5 0 0 0 5 0" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
          <span className={styles.notificationBadge} aria-hidden="true">
            3
          </span>
        </button>

        <div className={styles.profile}>
          <span className={styles.avatar} aria-hidden="true">
            <svg
              className={styles.avatarIcon}
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.75"
            >
              <circle cx="12" cy="8.5" r="3.2" />
              <path d="M5 19.5c1.4-3.2 4.2-4.8 7-4.8s5.6 1.6 7 4.8" strokeLinecap="round" />
            </svg>
          </span>

          <span className={styles.profileText}>
            <span className={styles.profileName}>{CURRENT_USER.name}</span>
            <span className={styles.profileRole}>{CURRENT_USER.role}</span>
          </span>

          <button type="button" className={styles.profileToggle} aria-label="Profile menu">
            <svg
              className={styles.chevronIcon}
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.75"
              aria-hidden="true"
            >
              <path d="M6 9l6 6 6-6" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>
        </div>
      </div>
    </header>
  )
}

export default Navbar