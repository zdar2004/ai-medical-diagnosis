import api from './api'

export const assessHeartDisease = async (data) => {
  const response = await api.post('/risk-assessment/heart-disease', data)
  return response.data
}

export const assessDiabetes = async (data) => {
  const response = await api.post('/risk-assessment/diabetes', data)
  return response.data
}

export const assessStroke = async (data) => {
  const response = await api.post('/risk-assessment/stroke', data)
  return response.data
}

export const assessHypertension = async (data) => {
  const response = await api.post('/risk-assessment/hypertension', data)
  return response.data
}