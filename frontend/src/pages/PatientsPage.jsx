import { useEffect, useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { patientService } from '../services/patientService'
import { getErrorMessage } from '../utils/errorHandler'

export const PatientsPage = () => {
  const { logout } = useAuth()
  const navigate = useNavigate()
  const [patients, setPatients] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    loadPatients()
  }, [])

  const loadPatients = async () => {
    try {
      setLoading(true)
      const response = await patientService.getPatients()
      setPatients(response.data.patients)
    } catch (err) {
      setError('Failed to load patients')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (patientId) => {
    if (window.confirm('Are you sure you want to delete this patient?')) {
      try {
        await patientService.deletePatient(patientId)
        loadPatients()
      } catch (err) {
        setError(getErrorMessage(err))
      }
    }
  }

  const handleLogout = () => {
    logout()
    navigate('/login')
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
              <Link
                to="/dashboard"
                className="text-gray-600 hover:text-gray-900 font-medium"
              >
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
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-3xl font-bold text-gray-900">Patients</h2>
            <Link
              to="/patients/add"
              className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 font-medium"
            >
              + Add Patient
            </Link>
          </div>

          {error && (
            <div className="mb-4 p-4 bg-red-100 border border-red-400 text-red-700 rounded whitespace-pre-line">
              {error}
            </div>
          )}

          {loading ? (
            <div className="text-center py-8">
              <p className="text-gray-600">Loading patients...</p>
            </div>
          ) : patients.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-gray-600 mb-4">No patients found</p>
              <Link
                to="/patients/add"
                className="text-blue-600 hover:underline"
              >
                Add your first patient
              </Link>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full bg-white border border-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 border-b text-left text-sm font-semibold text-gray-900">Photo</th>
                    <th className="px-6 py-3 border-b text-left text-sm font-semibold text-gray-900">Name</th>
                    <th className="px-6 py-3 border-b text-left text-sm font-semibold text-gray-900">Age</th>
                    <th className="px-6 py-3 border-b text-left text-sm font-semibold text-gray-900">Gender</th>
                    <th className="px-6 py-3 border-b text-left text-sm font-semibold text-gray-900">Blood Group</th>
                    <th className="px-6 py-3 border-b text-left text-sm font-semibold text-gray-900">Phone</th>
                    <th className="px-6 py-3 border-b text-left text-sm font-semibold text-gray-900">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {patients.map((patient) => (
                    <tr key={patient.id} className="hover:bg-gray-50 border-b">
                      <td className="px-6 py-3">
                        {patient.image_url ? (
                          <img
                            src={patient.image_url}
                            alt={patient.name}
                            className="w-10 h-10 rounded-full object-cover"
                          />
                        ) : (
                          <div className="w-10 h-10 rounded-full bg-gray-300 flex items-center justify-center">
                            <span className="text-gray-600 font-semibold">
                              {patient.name.charAt(0).toUpperCase()}
                            </span>
                          </div>
                        )}
                      </td>
                      <td className="px-6 py-3 text-sm text-gray-900 font-medium">{patient.name}</td>
                      <td className="px-6 py-3 text-sm text-gray-600">{patient.age}</td>
                      <td className="px-6 py-3 text-sm text-gray-600">{patient.gender}</td>
                      <td className="px-6 py-3 text-sm text-gray-600">{patient.blood_group}</td>
                      <td className="px-6 py-3 text-sm text-gray-600">{patient.phone}</td>
                      <td className="px-6 py-3 text-sm space-x-2">
                        <Link
                          to={`/patients/${patient.id}/edit`}
                          className="text-blue-600 hover:underline"
                        >
                          Edit
                        </Link>
                        <button
                          onClick={() => handleDelete(patient.id)}
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
    </div>
  )
}
