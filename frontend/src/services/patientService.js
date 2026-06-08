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

  uploadPatientImage: (patientId, file) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post(`/patients/${patientId}/upload-image`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
  },
}
