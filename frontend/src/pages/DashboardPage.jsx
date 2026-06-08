import { useEffect, useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { patientService } from '../services/patientService'

export const DashboardPage = () => {
  const { logout } = useAuth()
  const navigate = useNavigate()
  const [totalPatients, setTotalPatients] = useState(0)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const loadPatients = async () => {
      try {
        const response = await patientService.getPatients()
        setTotalPatients(response.data.total)
      } catch (error) {
        console.error('Failed to load patients:', error)
      } finally {
        setLoading(false)
      }
    }

    loadPatients()
  }, [])

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
                to="/patients"
                className="text-gray-600 hover:text-gray-900 font-medium"
              >
                Patients
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
          <h2 className="text-3xl font-bold text-gray-900 mb-8">Dashboard</h2>

          <div className="grid grid-cols-1 gap-6 mb-8">
            {/* Total Patients Card */}
            <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg p-6 text-white">
              <h3 className="text-lg font-semibold mb-2">Total Patients</h3>
              <p className="text-4xl font-bold">
                {loading ? '...' : totalPatients}
              </p>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="mb-8">
            <h3 className="text-xl font-semibold text-gray-900 mb-4">Quick Actions</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Link
                to="/patients"
                className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 text-center font-medium"
              >
                View Patients
              </Link>
              <Link
                to="/patients/add"
                className="bg-green-600 text-white px-6 py-3 rounded-lg hover:bg-green-700 text-center font-medium"
              >
                Add New Patient
              </Link>
            </div>
          </div>

          {/* Welcome Message */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-blue-800">
              Welcome to the Patient Management System! Use the navigation menu to manage your patients.
            </p>
          </div>
        </div>
      </main>
    </div>
  )
}
