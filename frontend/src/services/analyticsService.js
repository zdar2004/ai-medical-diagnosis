import api from './api'

export const getAnalyticsSummary = async () => {
  const response = await api.get('/dashboard/summary')
  return response.data
}

export const getDiseaseDistribution = async () => {
  const response = await api.get('/dashboard/disease-distribution')
  return response.data
}

export const getMonthlyAnalytics = async (months = 12) => {
  const response = await api.get(
    `/dashboard/monthly-analytics?months=${months}`
  )
  return response.data
}

export const getModelPerformance = async () => {
  const response = await api.get('/dashboard/model-performance')
  return response.data
}