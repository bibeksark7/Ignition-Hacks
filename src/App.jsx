import { useState } from 'react'
import { mockAnalysis } from './mockAnalysis'
import './App.css'

const PERIL_LABELS = {
  fire: 'Fire',
  water: 'Water',
  wind_hail: 'Wind & Hail',
}

function formatMoney(n) {
  return n.toLocaleString('en-CA', { style: 'currency', currency: 'CAD', maximumFractionDigits: 0 })
}

function AddressEntry({ onAnalyze, loading }) {
  const [address, setAddress] = useState('')

  return (
    <form
      className="address-entry"
      onSubmit={(e) => {
        e.preventDefault()
        onAnalyze(address || mockAnalysis.address)
      }}
    >
      <input
        type="text"
        placeholder="Enter a home address..."
        value={address}
        onChange={(e) => setAddress(e.target.value)}
      />
      <button type="submit" disabled={loading}>
        {loading ? 'Analyzing...' : 'Check my risk'}
      </button>
    </form>
  )
}

function LoadingSteps() {
  const steps = ['Fetching imagery', 'Segmenting roof', 'Measuring canopy & pavement', 'Scoring risk', 'Pricing']
  return (
    <ul className="loading-steps">
      {steps.map((s) => (
        <li key={s}>{s}...</li>
      ))}
    </ul>
  )
}

function ImageryPanel({ data }) {
  const [layers, setLayers] = useState({ roof: true, canopy: true, impervious: true })

  const toggle = (key) => setLayers((prev) => ({ ...prev, [key]: !prev[key] }))

  return (
    <section className="imagery-panel">
      <div className="imagery-tile">
        <div className="imagery-placeholder">
          Satellite tile for {data.address}
          {layers.roof && <div className="mask mask-roof" />}
          {layers.canopy && <div className="mask mask-canopy" />}
          {layers.impervious && <div className="mask mask-impervious" />}
        </div>
        <div className="capture-date">Imagery captured {data.imagery_date}</div>
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

function RiskAndValue({ data }) {
  return (
    <section className="risk-and-value">
      <div className="headline-card risk-card">
        <div className="headline-label">Your annual risk cost</div>
        <div className="headline-figure">{formatMoney(data.annual_premium)}/yr</div>
        <div className="headline-sub">
          Risk score <strong>{data.risk_score}/100</strong> — driven mostly by{' '}
          {data.risk_score_breakdown[0].top_driver.replaceAll('_', ' ')}
        </div>
      </div>
      <div className="headline-card value-card">
        <div className="headline-label">Estimated home value</div>
        <div className="headline-figure">{formatMoney(data.estimated_value)}</div>
        <div className="headline-sub">
          Rough estimate, not an appraisal ({data.value_confidence} confidence)
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
      {perils.map((p) => (
        <div className="peril-row" key={p.name}>
          <div className="peril-name">{PERIL_LABELS[p.name] ?? p.name}</div>
          <div className="peril-bar-track">
            <div className="peril-bar" style={{ width: `${(p.premium / max) * 100}%` }} />
          </div>
          <div className="peril-amount">{formatMoney(p.premium)}</div>
        </div>
      ))}
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
                <span className="stat-value">{m.payback_years.toFixed(1)} yrs</span>
              </div>
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

  return (
    <section className="before-after">
      <label className="toggle-row">
        <input type="checkbox" checked={showAfter} onChange={(e) => setShowAfter(e.target.checked)} />
        If I did every recommended fix
      </label>
      <div className="before-after-figure">{formatMoney(premium)}/yr</div>
    </section>
  )
}

function App() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)

  const handleAnalyze = (address) => {
    setLoading(true)
    // Placeholder for the real GET /analyze?address=... call.
    setTimeout(() => {
      setData({ ...mockAnalysis, address })
      setLoading(false)
    }, 900)
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>Sightline</h1>
        <p>See what your home's risk is actually costing you — and how to fix it.</p>
      </header>

      <AddressEntry onAnalyze={handleAnalyze} loading={loading} />

      {loading && <LoadingSteps />}

      {data && !loading && (
        <>
          <ImageryPanel data={data} />
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
