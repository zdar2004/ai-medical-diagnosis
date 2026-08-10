import { createBrowserRouter } from 'react-router-dom'
import MainLayout from '../layouts/MainLayout.jsx'
import DashboardLayout from '../layouts/DashboardLayout/DashboardLayout.jsx'
import ProtectedRoute from "../components/ProtectedRoute";
import Home from '../pages/Home/Home.jsx'
import Login from '../pages/Login/Login.jsx'
import NotFound from '../pages/NotFound/NotFound.jsx'

import Dashboard from '../pages/dashboard/Dashboard.jsx'

import Patients from '../pages/patients/Patients.jsx'
import AddPatient from '../pages/patients/AddPatient.jsx'
import PatientProfile from '../pages/patients/PatientProfile.jsx'

import Diagnosis from '../pages/diagnosis/Diagnosis.jsx'
import DiagnosisResult from '../pages/diagnosis/DiagnosisResult.jsx'

import ReportAnalysis from '../pages/reports/ReportAnalysis.jsx'
import RiskAssessment from '../pages/risk/RiskAssessment.jsx'
import AnalyticsDashboard from '../pages/analytics/AnalyticsDashboard.jsx'
import ClinicalAssistant from '../pages/assistant/ClinicalAssistant.jsx'

const router = createBrowserRouter([
  {
    path: '/login',
    element: <Login />,
  },

{
  element: (
    <ProtectedRoute>
      <DashboardLayout />
    </ProtectedRoute>
  ),
  children: [
      { path: '/dashboard', element: <Dashboard /> },

      { path: '/patients', element: <Patients /> },
      { path: '/patients/add', element: <AddPatient /> },
      { path: '/patients/profile', element: <PatientProfile /> },

      { path: '/diagnosis', element: <Diagnosis /> },
      { path: '/diagnosis/result', element: <DiagnosisResult /> },

      { path: '/reports', element: <ReportAnalysis /> },

      { path: '/risk', element: <RiskAssessment /> },

      { path: '/analytics', element: <AnalyticsDashboard /> },

      { path: '/assistant', element: <ClinicalAssistant /> },
    ],
  },

  {
    path: '/',
    element: <MainLayout />,
    children: [
      { index: true, element: <Home /> },
      { path: '*', element: <NotFound /> },
    ],
  },
])

export default router