import { useEffect, useState } from 'react'
import axios from 'axios'
import { MapContainer, Popup, TileLayer, useMap, CircleMarker } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000,
})

const RISK_COLORS = {
  LOW: '#2f855a',
  MODERATE: '#b7791f',
  HIGH: '#c05621',
  CRITICAL: '#c53030',
}

function MapViewport({ center }) {
  const map = useMap()
  useEffect(() => {
    map.setView(center, 12)
    setTimeout(() => map.invalidateSize(), 0)
  }, [center, map])
  return null
}

function HeatMapPopup({ point }) {
  return (
    <div className="heat-map-popup">
      <strong>{point.name}</strong>
      <dl>
        <div><dt>Temperature</dt><dd>{point.temperature_c}°C</dd></div>
        <div><dt>Feels Like</dt><dd>{point.feels_like_utci_c}°C</dd></div>
        <div><dt>Risk Score</dt><dd>{point.risk_score}/100</dd></div>
        <div><dt>Risk Level</dt><dd>{point.risk_level}</dd></div>
      </dl>
    </div>
  )
}

export default function HeatMap({ location }) {
  const [mapData, setMapData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true

    async function fetchHeatMap() {
      setLoading(true)
      setError('')
      try {
        const response = await api.get('/api/heat-map', { params: { location } })
        if (active) setMapData(response.data)
      } catch (requestError) {
        if (!active) return
        const detail = requestError.response?.data?.detail
        setError(detail || 'Could not load hyperlocal heat-map data.')
        setMapData(null)
      } finally {
        if (active) setLoading(false)
      }
    }

    if (location) fetchHeatMap()
    return () => { active = false }
  }, [location])

  if (loading) return <div className="heat-map-status">Loading hyperlocal heat map...</div>
  if (error) return <div className="heat-map-error" role="alert">{error}</div>
  if (!mapData) return null

  const center = [mapData.center.latitude, mapData.center.longitude]

  return (
    <div className="heat-map-content">
      <div className="heat-map-frame">
        <MapContainer center={center} zoom={12} scrollWheelZoom className="heat-map-canvas">
          <MapViewport center={center} />
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          {mapData.points.map((point) => {
            const color = RISK_COLORS[point.risk_level] || RISK_COLORS.MODERATE
            const radius = 8 + (point.risk_score / 100) * 6
            return (
              <CircleMarker
                key={`${point.name}-${point.latitude}-${point.longitude}`}
                center={[point.latitude, point.longitude]}
                radius={radius}
                pathOptions={{
                  color,
                  fillColor: color,
                  fillOpacity: 0.7,
                  weight: 2,
                }}
              >
                <Popup><HeatMapPopup point={point} /></Popup>
              </CircleMarker>
            )
          })}
        </MapContainer>
      </div>

      <div className="heat-map-legend" aria-label="Heat risk legend">
        <span className="heat-map-legend-title">Heat Risk</span>
        {Object.entries(RISK_COLORS).map(([level, color]) => (
          <span key={level}><i style={{ backgroundColor: color }} />{level.charAt(0) + level.slice(1).toLowerCase()}</span>
        ))}
      </div>

      <p className="heat-map-note">{mapData.sampling_note}</p>
    </div>
  )
}