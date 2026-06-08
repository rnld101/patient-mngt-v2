import api from './api'

export const patientService = {
  createPatient: (patientData) => {
    return api.post('/patients', patientData)
  },

  getPatients: () => {
    return api.get('/patients')
  },

  getPatientById: (id) => {
    return api.get(`/patients/${id}`)
  },

  updatePatient: (id, patientData) => {
    return api.put(`/patients/${id}`, patientData)
  },

  deletePatient: (id) => {
    return api.delete(`/patients/${id}`)
  },
}

