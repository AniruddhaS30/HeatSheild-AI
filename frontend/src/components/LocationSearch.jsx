import { useState } from 'react'

export default function LocationSearch({ defaultLocation, loading, onSearch }) {
  const [location, setLocation] = useState(defaultLocation)

  function handleSubmit(event) {
    event.preventDefault()
    const trimmedLocation = location.trim()
    if (trimmedLocation) onSearch(trimmedLocation)
  }

  return (
    <form className="search-panel" onSubmit={handleSubmit}>
      <label htmlFor="location">Location</label>
      <div className="search-row">
        <input
          id="location"
          name="location"
          value={location}
          onChange={(event) => setLocation(event.target.value)}
          placeholder="e.g. Bengaluru"
          autoComplete="off"
        />
        <button type="submit" disabled={loading || !location.trim()}>
          {loading ? 'Searching...' : 'Search'}
        </button>
      </div>
    </form>
  )
}
