import { useState } from 'react'
import AddressMap from './AddressMap'
import { fetchAnalysis } from './api'
import './App.css'

const PERIL_LABELS = {
  fire: 'Fire',
  water: 'Water',
  wind_hail: 'Wind & Hail',
}

function formatMoney(n) {
  return n.toLocaleString('en-CA', { style: 'currency', currency: 'CAD', maximumFractionDigits: 0 })
}

// Settled shape (workstream-02): risk_score: { overall, grade, perils: {...} }.
function getOverallRiskScore(data) {
  return data.risk_score.overall
}

// The single biggest driver across all perils, for the headline sub-line.
function getTopDriver(perils) {
  const allDrivers = perils.flatMap((p) => p.drivers ?? [])
  if (!allDrivers.length) return null
  return allDrivers.reduce((a, b) => (b.effect > a.effect ? b : a))
}

function LoadingSteps({ slow }) {
  const steps = ['Fetching imagery', 'Segmenting roof', 'Measuring canopy & pavement', 'Scoring risk', 'Pricing']
  return (
    <>
      <ul className="loading-steps">
        {steps.map((s) => (
          <li key={s}>{s}...</li>
        ))}
      </ul>
      {slow && <p className="map-hint">First look at a new address takes 10–20s (cold model). Cached addresses are instant.</p>}
    </>
  )
}

function ImageryPanel({ data }) {
  const [layers, setLayers] = useState({ roof: true, canopy: true, impervious: true })
  const toggle = (key) => setLayers((prev) => ({ ...prev, [key]: !prev[key] }))

  const hasRealImagery = Boolean(data.imagery_png)

  return (
    <section className="imagery-panel">
      <div className="imagery-tile">
        {hasRealImagery ? (
          <div className="imagery-real" style={{ backgroundImage: `url(${data.imagery_png})` }}>
            {layers.roof && data.roof_mask_png && (
              <div className="mask-layer mask-layer-roof" style={{ maskImage: `url(${data.roof_mask_png})`, WebkitMaskImage: `url(${data.roof_mask_png})` }} />
            )}
            {layers.canopy && data.canopy_mask_png && (
              <div className="mask-layer mask-layer-canopy" style={{ maskImage: `url(${data.canopy_mask_png})`, WebkitMaskImage: `url(${data.canopy_mask_png})` }} />
            )}
            {layers.impervious && data.impervious_mask_png && (
              <div className="mask-layer mask-layer-impervious" style={{ maskImage: `url(${data.impervious_mask_png})`, WebkitMaskImage: `url(${data.impervious_mask_png})` }} />
            )}
          </div>
        ) : (
          <div className="imagery-placeholder">
            Satellite tile for {data.address}
            {layers.roof && <div className="mask mask-roof" />}
            {layers.canopy && <div className="mask mask-canopy" />}
            {layers.impervious && <div className="mask mask-impervious" />}
          </div>
        )}
        <div className="capture-date">
          {data.imagery_date_known === false || !data.imagery_date
            ? 'Imagery capture date unknown — may be stale'
            : `Imagery captured ${data.imagery_date}`}
        </div>
      </div>
      <div className="layer-toggles">
        <label>
          <input type="checkbox" checked={layers.roof} onChange={() => toggle('roof')} />
          <span className="swatch swatch-roof" /> Roof
        </label>
        <label>
          <input type="checkbox" checked={layers.canopy} onChange={() => toggle('canopy')} />
          <span className="swatch swatch-canopy" /> Canopy
        </label>
        <label>
          <input type="checkbox" checked={layers.impervious} onChange={() => toggle('impervious')} />
          <span className="swatch swatch-impervious" /> Impervious surface
        </label>
      </div>
    </section>
  )
}

// Real field names from workstream-01's live output (not the low_confidence_warning/
// low_confidence_reason fields workstream-02 described — those don't exist on the
// actual response, this reads what's really there instead).
function LowConfidenceBanner({ data }) {
  const implausible = data.roof_segmentation_plausible === false
  const lowConfidence = typeof data.confidence === 'number' && data.confidence < 0.5
  if (!implausible && !lowConfidence) return null

  const reasons = []
  if (data.address_precision && data.address_precision !== 'exact') {
    reasons.push(`address only resolved to ${data.address_precision}-level precision`)
  }
  if (implausible) reasons.push('roof segmentation looked implausible')

  return (
    <div className="callout-warning">
      Low-confidence measurement{reasons.length ? `: ${reasons.join(', ')}` : ''} — try dragging the pin
      directly onto the roof for a better result. Numbers below may be unreliable.
    </div>
  )
}

function RiskAndValue({ data }) {
  const topDriver = getTopDriver(data.perils)
  const homeValue = data.home_value_estimate ?? data.estimated_value
  const valueConfidence = data.home_value_confidence ?? data.value_confidence

  return (
    <section className="risk-and-value">
      <div className="headline-card risk-card">
        <div className="headline-label">Your annual risk cost</div>
        <div className="headline-figure">{formatMoney(data.annual_premium)}/yr</div>
        <div className="headline-sub">
          Risk score <strong>{getOverallRiskScore(data)}/100</strong>
          {data.risk_score?.grade && ` (${data.risk_score.grade})`}
          {topDriver && <> — driven mostly by {topDriver.plain_language.toLowerCase()}</>}
        </div>
      </div>
      <div className="headline-card value-card">
        <div className="headline-label">Estimated home value</div>
        <div className="headline-figure">{formatMoney(homeValue)}</div>
        <div className="headline-sub">
          Rough estimate, not an appraisal ({valueConfidence} confidence)
          {data.premium_pct_of_value != null && (
            <> — risk costs {(data.premium_pct_of_value * 100).toFixed(2)}% of home value/yr</>
          )}
        </div>
      </div>
    </section>
  )
}

function PerilBreakdown({ perils }) {
  const max = Math.max(...perils.map((p) => p.premium))
  return (
    <section className="peril-breakdown">
      <h2>Where the cost comes from</h2>
      {perils.map((p) => {
        const top = (p.drivers ?? []).reduce((a, b) => ((b?.effect ?? 0) > (a?.effect ?? 0) ? b : a), null)
        return (
          <div className="peril-row-block" key={p.name}>
            <div className="peril-row">
              <div className="peril-name">{PERIL_LABELS[p.name] ?? p.name}</div>
              <div className="peril-bar-track">
                <div className="peril-bar" style={{ width: `${(p.premium / max) * 100}%` }} />
              </div>
              <div className="peril-amount">{formatMoney(p.premium)}</div>
            </div>
            {top?.plain_language && <div className="peril-driver">{top.plain_language}</div>}
          </div>
        )
      })}
    </section>
  )
}

function MitigationCards({ mitigations }) {
  const sorted = [...mitigations].sort((a, b) => a.payback_years - b.payback_years)
  return (
    <section className="mitigations">
      <h2>What you can do about it</h2>
      <div className="mitigation-grid">
        {sorted.map((m) => (
          <div className="mitigation-card" key={m.action}>
            <div className="mitigation-action">{m.action}</div>
            <div className="mitigation-stats">
              <div>
                <span className="stat-label">Cost</span>
                <span className="stat-value">{formatMoney(m.cost)}</span>
              </div>
              <div>
                <span className="stat-label">Saves</span>
                <span className="stat-value">{formatMoney(m.annual_saving)}/yr</span>
              </div>
              <div>
                <span className="stat-label">Payback</span>
                <span className="stat-value">
                  {m.payback_years == null ? '—' : `${m.payback_years.toFixed(1)} yrs`}
                </span>
              </div>
              {m.risk_score_delta != null && (
                <div>
                  <span className="stat-label">Risk score</span>
                  <span className="stat-value">+{m.risk_score_delta.toFixed(1)}</span>
                </div>
              )}
            </div>
            <div className="mitigation-cobenefit">{m.co_benefit}</div>
          </div>
        ))}
      </div>
    </section>
  )
}

function BeforeAfter({ data }) {
  const [showAfter, setShowAfter] = useState(false)
  const premium = showAfter ? data.premium_if_all_actions : data.annual_premium
  const riskScore = showAfter ? data.risk_score_if_all_actions?.overall : getOverallRiskScore(data)

  return (
    <section className="before-after">
      <label className="toggle-row">
        <input type="checkbox" checked={showAfter} onChange={(e) => setShowAfter(e.target.checked)} />
        If I did every recommended fix
      </label>
      <div className="before-after-figures">
        <div className="before-after-figure">{formatMoney(premium)}/yr</div>
        {riskScore != null && <div className="before-after-score">Risk score {riskScore}/100</div>}
      </div>
    </section>
  )
}

function App() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleAnalyze = async ({ address, lat, lon }) => {
    setLoading(true)
    setError(null)
    try {
      const result = await fetchAnalysis({ address, lat, lon })
      setData({ ...result, address: address || result.address })
    } catch (err) {
      setError(err.message || 'Could not reach the analysis servers.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>Sightline</h1>
        <p>See what your home's risk is actually costing you — and how to fix it.</p>
      </header>

      <AddressMap onConfirm={handleAnalyze} loading={loading} />

      {loading && <LoadingSteps slow />}

      {error && !loading && (
        <p className="map-hint map-hint-error">
          {error} — check that both the vision and pricing servers are reachable (see CONTEXT.md).
        </p>
      )}

      {data && !loading && (
        <>
          <ImageryPanel data={data} />
          <LowConfidenceBanner data={data} />
          <RiskAndValue data={data} />
          <PerilBreakdown perils={data.perils} />
          <BeforeAfter data={data} />
          <MitigationCards mitigations={data.mitigations} />
          <p className="disclaimer">{data.disclaimer}</p>
        </>
      )}
    </div>
  )
}

export default App
