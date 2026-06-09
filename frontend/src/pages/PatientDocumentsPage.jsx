import { useEffect, useState } from 'react'
import { useNavigate, Link, useParams } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { patientService } from '../services/patientService'
import { documentService } from '../services/documentService'
import { getErrorMessage } from '../utils/errorHandler'
import { DocumentViewerModal } from '../components/DocumentViewerModal'

const DOCUMENT_TYPES = [
  'Prescription',
  'Blood Report',
  'X-Ray',
  'MRI',
  'CT Scan',
  'Other',
]

export const PatientDocumentsPage = () => {
  const { logout } = useAuth()
  const navigate = useNavigate()
  const { id: patientId } = useParams()

  const [patient, setPatient] = useState(null)
  const [documents, setDocuments] = useState([])
  const [loadingPage, setLoadingPage] = useState(true)
  const [error, setError] = useState('')

  // Upload form state
  const [selectedFile, setSelectedFile] = useState(null)
  const [documentType, setDocumentType] = useState(DOCUMENT_TYPES[0])
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState('')

  // Viewer modal state
  const [isViewerOpen, setIsViewerOpen] = useState(false)
  const [viewerDoc, setViewerDoc] = useState(null)
  const [viewerUrl, setViewerUrl] = useState('')

  useEffect(() => {
    loadPage()
  }, [patientId])

  const loadPage = async () => {
    try {
      setLoadingPage(true)
      const [patientRes, docsRes] = await Promise.all([
        patientService.getPatientById(patientId),
        documentService.getDocuments(patientId),
      ])
      setPatient(patientRes.data)
      setDocuments(docsRes.data.documents)
    } catch (err) {
      setError('Failed to load patient data')
      console.error(err)
    } finally {
      setLoadingPage(false)
    }
  }

  const handleFileChange = (e) => {
    const file = e.target.files?.[0]
    if (file) setSelectedFile(file)
  }

  const handleUpload = async (e) => {
    e.preventDefault()
    if (!selectedFile) return

    setUploadError('')
    setUploading(true)

    try {
      const res = await documentService.uploadDocument(patientId, selectedFile, documentType)
      // Prepend the new document to the top of the list
      setDocuments(prev => [res.data, ...prev])
      setSelectedFile(null)
      setDocumentType(DOCUMENT_TYPES[0])
      // Reset file input
      document.getElementById('doc-file-input').value = ''
    } catch (err) {
      setUploadError(getErrorMessage(err))
    } finally {
      setUploading(false)
    }
  }

  const handleView = async (doc) => {
    try {
      const res = await documentService.getDocumentUrl(patientId, doc.id)
      setViewerDoc(doc)
      setViewerUrl(res.data.url)
      setIsViewerOpen(true)
    } catch (err) {
      setError('Failed to generate document URL. Please try again.')
    }
  }

  const handleDelete = async (docId) => {
    if (!window.confirm('Are you sure you want to delete this document?')) return

    try {
      await documentService.deleteDocument(patientId, docId)
      setDocuments(prev => prev.filter(d => d.id !== docId))
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric', month: 'short', day: 'numeric',
    })
  }

  if (loadingPage) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <p className="text-gray-600">Loading...</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Navigation */}
      <nav className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-gray-900">Patient Management</h1>
            </div>
            <div className="flex items-center space-x-4">
              <Link to="/patients" className="text-gray-600 hover:text-gray-900 font-medium">
                Patients
              </Link>
              <Link to="/dashboard" className="text-gray-600 hover:text-gray-900 font-medium">
                Dashboard
              </Link>
              <button
                onClick={handleLogout}
                className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8 space-y-6">

        {/* Page header */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
              <span className="text-blue-700 font-bold text-lg">
                {patient?.name?.charAt(0).toUpperCase()}
              </span>
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900">
                {patient?.name} — Documents
              </h2>
              <p className="text-sm text-gray-500">
                {patient?.age} yrs · {patient?.gender} · {patient?.blood_group}
              </p>
            </div>
            <Link
              to={`/patients/${patientId}/edit`}
              className="ml-auto text-sm text-blue-600 hover:underline"
            >
              Edit Patient
            </Link>
          </div>
        </div>

        {/* Global error banner */}
        {error && (
          <div className="p-4 bg-red-100 border border-red-400 text-red-700 rounded whitespace-pre-line">
            {error}
          </div>
        )}

        {/* Upload form */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Upload Document</h3>

          {uploadError && (
            <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded text-sm">
              {uploadError}
            </div>
          )}

          <form onSubmit={handleUpload} className="flex flex-col sm:flex-row gap-4 items-end">
            <div className="flex-1">
              <label htmlFor="doc-type" className="block text-sm font-medium text-gray-700 mb-1">
                Document Type
              </label>
              <select
                id="doc-type"
                value={documentType}
                onChange={(e) => setDocumentType(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                {DOCUMENT_TYPES.map(type => (
                  <option key={type} value={type}>{type}</option>
                ))}
              </select>
            </div>

            <div className="flex-[2]">
              <label htmlFor="doc-file-input" className="block text-sm font-medium text-gray-700 mb-1">
                File <span className="text-gray-400 font-normal">(PDF, JPG, PNG, DICOM — max 10 MB)</span>
              </label>
              <input
                id="doc-file-input"
                type="file"
                accept=".pdf,.jpg,.jpeg,.png,.gif,.webp,.dcm"
                onChange={handleFileChange}
                required
                className="w-full px-4 py-2 border border-gray-300 rounded-lg"
              />
            </div>

            <button
              type="submit"
              disabled={uploading || !selectedFile}
              className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400 font-medium whitespace-nowrap"
            >
              {uploading ? 'Uploading...' : 'Upload'}
            </button>
          </form>
        </div>

        {/* Documents list */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Documents
            <span className="ml-2 text-sm font-normal text-gray-500">({documents.length})</span>
          </h3>

          {documents.length === 0 ? (
            <p className="text-gray-500 text-center py-6">
              No documents uploaded yet. Use the form above to add the first document.
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full border border-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 border-b text-left text-sm font-semibold text-gray-900">File Name</th>
                    <th className="px-6 py-3 border-b text-left text-sm font-semibold text-gray-900">Type</th>
                    <th className="px-6 py-3 border-b text-left text-sm font-semibold text-gray-900">Uploaded</th>
                    <th className="px-6 py-3 border-b text-left text-sm font-semibold text-gray-900">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {documents.map((doc) => (
                    <tr key={doc.id} className="hover:bg-gray-50 border-b">
                      <td className="px-6 py-3 text-sm text-gray-900 font-medium">{doc.file_name}</td>
                      <td className="px-6 py-3">
                        <span className="inline-block px-2 py-1 text-xs font-medium bg-blue-100 text-blue-700 rounded-full">
                          {doc.document_type}
                        </span>
                      </td>
                      <td className="px-6 py-3 text-sm text-gray-600">{formatDate(doc.uploaded_at)}</td>
                      <td className="px-6 py-3 text-sm space-x-3">
                        <button
                          onClick={() => handleView(doc)}
                          className="text-blue-600 hover:underline"
                        >
                          View
                        </button>
                        <button
                          onClick={() => handleDelete(doc.id)}
                          className="text-red-600 hover:underline"
                        >
                          Delete
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>

      <DocumentViewerModal
        isOpen={isViewerOpen}
        onClose={() => {
          setIsViewerOpen(false)
          setViewerDoc(null)
          setViewerUrl('')
        }}
        doc={viewerDoc}
        url={viewerUrl}
      />
    </div>
  )
}
