import { useState } from 'react'
import HeatMap from './HeatMap.jsx'
import EarlyWarningBanner from './EarlyWarningBanner.jsx'

export default function Dashboard({ data }) {
  const risk = data.heat_health_risk
  const conditions = data.current_weather
  const riskLevel = risk.level.toLowerCase()
  const forecast = data.forecast || []
  const anomaly = data.historical_anomaly
  const vulnerabilityProfiles = data.vulnerability_profiles || []
  const smartInterventions = data.smart_interventions || { interventions: [] }
  const interventionsList = smartInterventions.interventions || []
  const [filterCategory, setFilterCategory] = useState('ALL')

  const highestImpactProfile = vulnerabilityProfiles.length > 0
    ? vulnerabilityProfiles.reduce((highest, profile) => (
      profile.impact_score > highest.impact_score ? profile : highest
    ))
    : null

  const profileMeta = {
    GENERAL_POPULATION: { name: 'General Population', icon: '👥' },
    ELDERLY: { name: 'Elderly', icon: '👴' },
    CHILDREN: { name: 'Children', icon: '👶' },
    OUTDOOR_WORKERS: { name: 'Outdoor Workers', icon: '👷' },
  }

  const categoryMeta = {
    PUBLIC_SAFETY: { name: 'Public Safety', icon: '📢', badgeClass: 'cat-public' },
    MUNICIPAL_ACTION: { name: 'Municipal Action', icon: '🏛️', badgeClass: 'cat-municipal' },
    HEALTHCARE: { name: 'Healthcare System', icon: '🏥', badgeClass: 'cat-healthcare' },
    OUTDOOR_WORK: { name: 'Outdoor Work', icon: '👷', badgeClass: 'cat-outdoor' },
    VULNERABLE_POPULATIONS: { name: 'Vulnerable Care', icon: '🛡️', badgeClass: 'cat-vulnerable' },
  }

  function formatForecastDate(dateValue, index) {
    const date = new Date(`${dateValue}T00:00:00`)
    const today = new Date()
    const tomorrow = new Date(today)
    tomorrow.setDate(today.getDate() + 1)

    if (date.toDateString() === today.toDateString()) return 'Today'
    if (date.toDateString() === tomorrow.toDateString()) return 'Tomorrow'
    if (Number.isNaN(date.getTime())) return `Day ${index + 1}`
    return new Intl.DateTimeFormat('en-IN', { weekday: 'short', day: 'numeric', month: 'short' }).format(date)
  }

  function formatStressCategory(category) {
    return category
      .replace(/\b\w/g, (letter) => letter.toUpperCase())
      .replace(' Stress', '')
  }

  function anomalyMessage(deviation) {
    if (deviation > 0.5) return "Today's temperature is warmer than the historical average for this date."
    if (deviation < -0.5) return "Today's temperature is cooler than the historical average for this date."
    return "Current temperatures are close to the historical average."
  }

  function anomalyLabel(deviation) {
    if (deviation > 0.5) return `${deviation > 0 ? '+' : ''}${deviation}°C Above Normal`
    if (deviation < -0.5) return `${deviation}°C Below Normal`
    return 'Near Historical Normal'
  }

  function profileExplanation(explanation) {
    return explanation.split(' This is a generalized prototype decision-support assessment')[0]
  }

  return (
    <section className="dashboard" aria-live="polite">
      <div className="dashboard-heading">
        <div>
          <p className="eyebrow">Current heat assessment</p>
          <h2>{data.location}</h2>
        </div>
        <p className="updated-label">Live environmental signals</p>
      </div>

      <EarlyWarningBanner level={risk.level} score={risk.score} />

      <div className={`risk-hero risk-${riskLevel}`}>
        <div className="risk-hero-main">
          <p className="section-kicker">Heat Health Risk</p>
          <div className="risk-score-line">
            <strong>{risk.score}</strong>
            <span>/ 100</span>
          </div>
          <div className="risk-level-label">{risk.level}</div>
          <div className="risk-meter" aria-label={`Risk score ${risk.score} out of 100`}>
            <span style={{ width: `${Math.min(100, Math.max(0, risk.score))}%` }} />
          </div>
        </div>
        <div className="risk-explanation">
          <p className="section-kicker">Why is this happening?</p>
          <div className="contributor-list">
            {risk.contributors.length > 0 ? risk.contributors.map((contributor) => (
              <div className="contributor" key={contributor.factor}>
                <span className="contributor-marker" />
                <div>
                  <strong>{contributor.factor}</strong>
                  <p>{contributor.explanation}</p>
                </div>
              </div>
            )) : <p className="muted-copy">No contributing signals are available.</p>}
          </div>
        </div>
      </div>

      <div className="legend" aria-label="Risk level color legend">
        <span className="legend-title">Risk levels</span>
        <span><i className="legend-dot risk-low" />Low</span>
        <span><i className="legend-dot risk-moderate" />Moderate</span>
        <span><i className="legend-dot risk-high" />High</span>
        <span><i className="legend-dot risk-critical" />Critical</span>
      </div>

      <div className="conditions-section">
        <div className="section-heading">
          <div>
            <p className="section-kicker">Right now</p>
            <h3>Current Conditions</h3>
          </div>
          <span className="conditions-note">Real-time weather</span>
        </div>

        {conditions ? (
          <div className="conditions-grid">
            <div className="condition-card condition-primary">
              <span>Temperature</span>
              <strong>{conditions.temperature_c}°</strong>
              <small>Celsius</small>
            </div>
            <div className="condition-card">
              <span>Feels Like</span>
              <strong>{conditions.feels_like_utci_c}°</strong>
              <small>Human comfort temperature</small>
            </div>
            <div className="condition-card">
              <span>Thermal Stress</span>
              <strong>{conditions.stress_category}</strong>
              <small>UTCI assessment</small>
            </div>
            <div className="condition-card">
              <span>Humidity</span>
              <strong>{conditions.humidity_pct}%</strong>
              <small>Relative humidity</small>
            </div>
            <div className="condition-card">
              <span>Wind Speed</span>
              <strong>{conditions.wind_speed_ms} m/s</strong>
              <small>At 10 metres</small>
            </div>
          </div>
        ) : (
          <p className="muted-copy">Current conditions are unavailable.</p>
        )}
      </div>

      <div className="forecast-section">
        <div className="section-heading">
          <div>
            <p className="section-kicker">Look ahead</p>
            <h3>5-Day Heat Forecast</h3>
          </div>
          <span className="conditions-note">Heat conditions expected over the next five days.</span>
        </div>

        <div className="forecast-grid">
          {forecast.map((day, index) => {
            const dayRisk = day.risk_level.toLowerCase()
            const isDangerous = dayRisk === 'high' || dayRisk === 'critical'

            return (
              <article className={`forecast-card risk-${dayRisk} ${isDangerous ? 'forecast-card-danger' : ''}`} key={day.date}>
                <div className="forecast-card-topline">
                  <span className="forecast-date">{formatForecastDate(day.date, index)}</span>
                  <span className="forecast-risk-dot" aria-label={`${day.risk_level} risk`} />
                </div>
                {isDangerous && <span className="attention-label">High attention</span>}
                <div className="forecast-temperatures">
                  <div>
                    <span>High Temperature</span>
                    <strong>{day.max_temp_c}°</strong>
                  </div>
                  <div>
                    <span>Low Temperature</span>
                    <strong>{day.min_temp_c}°</strong>
                  </div>
                </div>
                <div className="forecast-feels-like">
                  <span>Feels Like</span>
                  <strong>{day.utci_prediction_c}°</strong>
                </div>
                <div className="forecast-stress">
                  <span>Heat Stress</span>
                  <strong>{formatStressCategory(day.stress_category)}</strong>
                </div>
                <div className="forecast-risk-label">
                  <span>Risk Level</span>
                  <strong>{day.risk_level}</strong>
                </div>
              </article>
            )
          })}
        </div>
      </div>

      {anomaly ? (
        <div className={`anomaly-section ${anomaly.is_anomalous ? 'anomaly-warm' : 'anomaly-neutral'}`}>
          <div className="section-heading">
            <div>
              <p className="section-kicker">Historical context</p>
              <h3>Historical Weather Comparison</h3>
            </div>
            <span className="conditions-note">{anomaly.date}</span>
          </div>
          <p className="anomaly-subtitle">See how today's conditions compare with the historical climate pattern for this location.</p>

          <div className="anomaly-comparison">
            <div className="comparison-temperature">
              <span>Today's High Temperature</span>
              <strong>{anomaly.today_max_temp_c}°C</strong>
              <small>Current daily high</small>
            </div>
            <div className="comparison-divider" aria-hidden="true">vs</div>
            <div className="comparison-temperature">
              <span>Historical Average</span>
              <strong>{anomaly.historical_avg_max_temp_c}°C</strong>
              <small>For this date</small>
            </div>
            <div className="anomaly-result">
              <strong>{anomalyLabel(anomaly.deviation_c)}</strong>
              <span>{anomaly.anomaly_category}</span>
            </div>
          </div>

          <div className="anomaly-explanation">
            <span className="anomaly-icon" aria-hidden="true">{anomaly.is_anomalous ? '!' : 'i'}</span>
            <div>
              <strong>{anomaly.is_anomalous ? anomaly.anomaly_category : 'Near Historical Normal'}</strong>
              <p>{anomalyMessage(anomaly.deviation_c)}</p>
            </div>
          </div>

          <div className="baseline-panel">
            <p className="section-kicker">Historical baseline</p>
            <div className="baseline-grid">
              <div><span>Average High</span><strong>{anomaly.historical_baseline.average_max_temperature_c}°C</strong></div>
              <div><span>Average Temperature</span><strong>{anomaly.historical_baseline.average_mean_temperature_c}°C</strong></div>
              <div><span>Average Humidity</span><strong>{anomaly.historical_baseline.average_humidity_pct}%</strong></div>
              <div><span>Based on</span><strong>{anomaly.years_used} years</strong></div>
            </div>
          </div>
        </div>
      ) : (
        <div className="anomaly-section anomaly-neutral">
          <p className="section-kicker">Historical context</p>
          <h3>Historical Weather Comparison</h3>
          <p className="muted-copy">Historical comparison is unavailable for this location.</p>
        </div>
      )}

      <div className="heat-map-section">
        <div className="section-heading">
          <div>
            <p className="section-kicker">Local intelligence</p>
            <h3>Hyperlocal Heat Risk Map</h3>
          </div>
          <span className="conditions-note">{data.location}</span>
        </div>
        <p className="heat-map-subtitle">Explore how heat risk varies across sampled locations.</p>
        <HeatMap location={data.location} />
      </div>

      <div className="vulnerability-section">
        <div className="section-heading">
          <div>
            <p className="section-kicker">Impact profiles</p>
            <h3>Who Is Most at Risk?</h3>
          </div>
          <span className="conditions-note">Population-level assessment</span>
        </div>
        <p className="vulnerability-subtitle">Different groups experience the same environmental conditions differently.</p>

        {highestImpactProfile && (
          <div className="vulnerability-insight">
            <span className="insight-icon" aria-hidden="true">↗</span>
            <p><strong>{profileMeta[highestImpactProfile.profile]?.name || highestImpactProfile.profile}</strong> currently face the highest impact risk at <strong>{highestImpactProfile.impact_score}/100</strong>.</p>
          </div>
        )}

        {vulnerabilityProfiles.length > 0 ? (
          <div className="vulnerability-grid">
            {vulnerabilityProfiles.map((profile) => {
              const meta = profileMeta[profile.profile] || { name: profile.profile, icon: '◉' }
              const impactLevel = profile.impact_level.toLowerCase()

              return (
                <article className={`vulnerability-card risk-${impactLevel}`} key={profile.profile}>
                  <div className="vulnerability-card-header">
                    <span className="profile-icon" aria-hidden="true">{meta.icon}</span>
                    <div>
                      <h4>{meta.name}</h4>
                      <span className="profile-risk-label">{profile.impact_level} impact</span>
                    </div>
                  </div>

                  <div className="impact-score-row">
                    <div>
                      <span>Impact Score</span>
                      <strong>{profile.impact_score}</strong><small>/ 100</small>
                    </div>
                    <span className="impact-level-pill">{profile.impact_level}</span>
                  </div>
                  <div className="impact-progress" aria-label={`${meta.name} impact score ${profile.impact_score} out of 100`}>
                    <span style={{ width: `${Math.min(100, Math.max(0, profile.impact_score))}%` }} />
                  </div>

                  <div className="profile-metrics">
                    <div><span>Environmental Risk</span><strong>{profile.base_environmental_risk}/100</strong></div>
                    <div><span>Vulnerability Factor</span><strong>{profile.vulnerability_multiplier}×</strong></div>
                  </div>

                  <p className="profile-explanation">{profileExplanation(profile.explanation)}</p>

                  <details className="profile-details">
                    <summary>Why are they at risk?</summary>
                    <ul>
                      {profile.risk_factors.map((factor) => <li key={factor}>{factor}</li>)}
                    </ul>
                  </details>

                  <div className="recommended-actions">
                    <span>Recommended Actions</span>
                    <ul>
                      {profile.recommended_actions.map((action) => <li key={action}>{action}</li>)}
                    </ul>
                  </div>
                </article>
              )
            })}
          </div>
        ) : (
          <div className="vulnerability-empty">
            <strong>Vulnerability profiles unavailable</strong>
            <p>Population impact details are not available for this location right now.</p>
          </div>
        )}
      </div>

      <div className="interventions-section" id="smart-interventions">
        <div className="section-heading">
          <div>
            <p className="section-kicker">Actionable intelligence</p>
            <h3>What Should I Do? — Smart Interventions</h3>
          </div>
          {smartInterventions.overall_recommendation_level && (
            <span className={`recommendation-badge risk-${smartInterventions.overall_recommendation_level.toLowerCase()}`}>
              Level: {smartInterventions.overall_recommendation_level}
            </span>
          )}
        </div>
        <p className="interventions-subtitle">
          {smartInterventions.summary || 'Decision-support interventions tailored to current and forecasted heat risk.'}
        </p>

        {interventionsList.length > 0 && (
          <div className="interventions-filter-bar" role="tablist" aria-label="Filter interventions by category">
            <button
              type="button"
              className={`filter-chip ${filterCategory === 'ALL' ? 'active' : ''}`}
              onClick={() => setFilterCategory('ALL')}
            >
              All Actions ({interventionsList.length})
            </button>
            {Object.keys(categoryMeta).map((catKey) => {
              const count = interventionsList.filter((i) => i.category === catKey).length
              if (count === 0) return null
              const meta = categoryMeta[catKey]
              return (
                <button
                  key={catKey}
                  type="button"
                  className={`filter-chip ${filterCategory === catKey ? 'active' : ''}`}
                  onClick={() => setFilterCategory(catKey)}
                >
                  <span aria-hidden="true">{meta.icon}</span> {meta.name} ({count})
                </button>
              )
            })}
          </div>
        )}

        {interventionsList.length > 0 ? (
          <div className="interventions-grid">
            {(filterCategory === 'ALL'
              ? interventionsList
              : interventionsList.filter((i) => i.category === filterCategory)
            ).map((item, index) => {
              const meta = categoryMeta[item.category] || { name: item.category, icon: '💡', badgeClass: 'cat-default' }
              const priorityLower = (item.priority || 'low').toLowerCase()
              return (
                <article
                  className={`intervention-card priority-${priorityLower}`}
                  key={`${item.category}-${item.target}-${index}`}
                >
                  <div className="intervention-card-header">
                    <div className="intervention-category-tag">
                      <span className="cat-icon" aria-hidden="true">{meta.icon}</span>
                      <span className="cat-name">{meta.name}</span>
                    </div>
                    <span className={`priority-pill priority-${priorityLower}`}>
                      {item.priority} Priority
                    </span>
                  </div>

                  <div className="intervention-target-box">
                    <span className="target-label">Target Group</span>
                    <strong className="target-name">{item.target}</strong>
                  </div>

                  <div className="intervention-action-box">
                    <span className="action-kicker">Recommended Action</span>
                    <p className="action-text">{item.action}</p>
                  </div>

                  <div className="intervention-reason-box">
                    <span className="reason-label">Context & Rationale</span>
                    <p className="reason-text">{item.reason}</p>
                  </div>

                  {item.triggers && item.triggers.length > 0 && (
                    <div className="intervention-triggers">
                      <span className="triggers-heading">Supporting Signals</span>
                      <div className="trigger-chips">
                        {item.triggers.map((trigger, tIdx) => (
                          <span className="trigger-chip" key={tIdx}>
                            <span className="trigger-bullet" aria-hidden="true">⚡</span>
                            {trigger}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </article>
              )
            })}
          </div>
        ) : (
          <div className="interventions-empty">
            <strong>No active intervention alerts</strong>
            <p>Standard heat-safety awareness should be maintained.</p>
          </div>
        )}
      </div>

      <div className="dashboard-footnote">
        <span className="footnote-dot" />
        Risk colors show the current combined environmental heat assessment.
      </div>
    </section>
  )
}
