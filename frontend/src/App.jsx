import { useEffect, useState } from 'react'
import axios from 'axios'
import Dashboard from './components/Dashboard.jsx'
import LocationSearch from './components/LocationSearch.jsx'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000,
})

export default function App() {
  const [analysis, setAnalysis] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [searchedLocation, setSearchedLocation] = useState('Bengaluru')

  async function fetchAnalysis(location) {
    setLoading(true)
    setError('')

    try {
      const response = await api.get('/api/analysis', { params: { location } })
      setAnalysis(response.data)
      setSearchedLocation(location)
    } catch (requestError) {
      const detail = requestError.response?.data?.detail
      setError(detail || 'Could not load heat intelligence. Check that the backend is running.')
      setAnalysis(null)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAnalysis('Bengaluru')
  }, [])

  return (
    <main className="app-shell">
      <header className="app-header">
        <div>
          <p className="eyebrow">SIH26083 · Heat intelligence</p>
          <h1>HeatShield AI</h1>
          <p className="intro">Extreme Heatwave Early Warning System</p>
        </div>
        <span className="connection-dot">Live data connected</span>
      </header>

      <LocationSearch
        defaultLocation={searchedLocation}
        loading={loading}
        onSearch={fetchAnalysis}
      />

      {loading && <p className="status-message">Loading real weather analysis...</p>}
      {error && <p className="error-message" role="alert">{error}</p>}
      {analysis && !loading && <Dashboard data={analysis} />}
    </main>
  )
}
