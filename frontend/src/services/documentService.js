import api from './api'

export const documentService = {
  // Upload a document for a patient
  uploadDocument: (patientId, file, documentType) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('document_type', documentType)
    return api.post(`/patients/${patientId}/documents`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  // List all documents for a patient
  getDocuments: (patientId) => {
    return api.get(`/patients/${patientId}/documents`)
  },

  // Get a temporary pre-signed URL to view/download a document
  getDocumentUrl: (patientId, documentId) => {
    return api.get(`/patients/${patientId}/documents/${documentId}/url`)
  },

  // Delete a document
  deleteDocument: (patientId, documentId) => {
    return api.delete(`/patients/${patientId}/documents/${documentId}`)
  },
}
