const BANNER_CONTENT = {
  low: {
    icon: '✅',
    title: 'No Significant Heat Threat',
    message: 'Current heat-health risk is low. No special precautions are needed at this time.',
  },
  moderate: {
    icon: '⚠️',
    title: 'Heat Advisory',
    message: 'Heat-health risk is elevated. Preventive action is advised, especially for sensitive groups.',
  },
  high: {
    icon: '🔥',
    title: 'Heat Alert',
    message: 'High heat-health risk detected. Preventive action is strongly recommended for all groups.',
  },
  critical: {
    icon: '🚨',
    title: 'Critical Heat Warning',
    message: 'Critical heat-health conditions. Immediate preventive and heat-action measures are recommended.',
  },
}

export default function EarlyWarningBanner({ level, score }) {
  const key = (level || '').toLowerCase()
  const content = BANNER_CONTENT[key] || BANNER_CONTENT.low

  return (
    <div className={`early-warning-banner warning-${key}`} role="status" aria-live="polite">
      <span className="warning-icon" aria-hidden="true">{content.icon}</span>
      <div className="warning-body">
        <div className="warning-title-row">
          <strong className="warning-title">{content.title}</strong>
          <span className="warning-level-tag">{level} · {score}/100</span>
        </div>
        <p className="warning-message">{content.message}</p>
      </div>
    </div>
  )
}
