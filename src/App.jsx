import { useEffect, useRef, useState } from 'react'
import AddressMap from './AddressMap'
import Cursor from './Cursor'
import RiskGauge from './RiskGauge'
import { gradeTone, gradeWord } from './grade'
import { fetchAnalysis } from './api'
import { isDemoMode } from './demoData'
import './App.css'

const PERIL_LABELS = {
  fire: 'Fire',
  water: 'Water',
  wind_hail: 'Wind and hail',
}

const PERIL_TONE = {
  fire: 'roof',
  water: 'water',
  wind_hail: 'wind',
}

/* -------------------------------------------------------------------------- */
/* formatting                                                                  */
/* -------------------------------------------------------------------------- */

function money(n) {
  if (n == null || Number.isNaN(n)) return '-'
  return n.toLocaleString('en-CA', {
    style: 'currency',
    currency: 'CAD',
    maximumFractionDigits: 0,
  })
}

// Past a century the exact figure stops meaning anything, and "1269 years"
// reads as a broken number rather than an honest one.
const PAYBACK_CEILING = 100

function years(y) {
  if (y == null) return null
  if (y < 1) return 'Under a year'
  if (y < 10) return `${y.toFixed(1)} years`
  if (y > PAYBACK_CEILING) return `Over ${PAYBACK_CEILING} years`
  return `${Math.round(y)} years`
}

function pct(n, digits = 0) {
  if (n == null) return '-'
  return `${n.toFixed(digits)}%`
}

// Backend strings arrive with em dashes. The page uses plain hyphens
// throughout, so normalise on the way to the screen rather than letting one
// stray character break the typography.
function plain(text) {
  return typeof text === 'string' ? text.replace(/[—–]/g, '-') : text
}

function titleCase(slug) {
  if (!slug) return null
  const s = slug.replace(/_/g, ' ')
  return s.charAt(0).toUpperCase() + s.slice(1)
}

function topDriverOf(peril) {
  const drivers = peril?.drivers ?? []
  if (!drivers.length) return null
  return drivers.reduce((a, b) => ((b?.effect ?? 0) > (a?.effect ?? 0) ? b : a))
}

function biggestDriver(perils) {
  const all = (perils ?? []).flatMap((p) => p.drivers ?? [])
  if (!all.length) return null
  return all.reduce((a, b) => (b.effect > a.effect ? b : a))
}

/* -------------------------------------------------------------------------- */
/* loading                                                                     */
/* -------------------------------------------------------------------------- */

const PIPELINE_STEPS = [
  'Locating the property',
  'Fetching the aerial photo',
  'Tracing the roof outline',
  'Measuring tree cover and paving',
  'Checking regional flood and fire exposure',
  'Pricing the risk',
]

// The pipeline genuinely takes 10-20s on a cold model. Naming each stage as it
// runs is the difference between "is this broken" and "something hard is
// happening", which is the whole reason this screen exists.
function Pipeline() {
  const [active, setActive] = useState(0)

  useEffect(() => {
    const id = setInterval(() => {
      setActive((i) => Math.min(i + 1, PIPELINE_STEPS.length - 1))
    }, 1800)
    return () => clearInterval(id)
  }, [])

  return (
    <section className="panel pipeline" aria-live="polite">
      <h2 className="pipeline-title">Measuring this home</h2>
      <ol className="pipeline-steps">
        {PIPELINE_STEPS.map((step, i) => (
          <li
            key={step}
            className={i < active ? 'is-done' : i === active ? 'is-active' : 'is-waiting'}
          >
            <span className="pipeline-mark" aria-hidden="true" />
            <span className="pipeline-label">{step}</span>
          </li>
        ))}
      </ol>
      <p className="pipeline-note">
        A first look at a new address takes 10 to 20 seconds while the segmentation model warms up.
        Addresses we have already seen come back instantly.
      </p>
    </section>
  )
}

/* -------------------------------------------------------------------------- */
/* evidence: imagery + what the camera measured                                */
/* -------------------------------------------------------------------------- */

const LAYERS = [
  { key: 'roof', label: 'Roof', tone: 'roof' },
  { key: 'canopy', label: 'Tree cover', tone: 'canopy' },
  { key: 'impervious', label: 'Paved surface', tone: 'water' },
]

function Evidence({ data }) {
  const [layers, setLayers] = useState({ roof: true, canopy: true, impervious: true })
  const toggle = (key) => setLayers((prev) => ({ ...prev, [key]: !prev[key] }))

  const hasImagery = Boolean(data.imagery_png)
  const dateKnown = data.imagery_date_known !== false && Boolean(data.imagery_date)

  const measurements = [
    {
      label: 'Roof footprint',
      value: data.roof_area_m2 != null ? `${Math.round(data.roof_area_m2)} m²` : '-',
      tone: 'roof',
      sub: titleCase(data.roof_material),
    },
    {
      label: 'Tree cover over roof',
      value: pct(data.canopy_overlap_pct),
      tone: 'canopy',
      sub: data.canopy_within_5m_pct != null ? `${pct(data.canopy_within_5m_pct)} within 5 m` : null,
    },
    {
      label: 'Lot paved over',
      value: pct(data.impervious_pct),
      tone: 'water',
      sub: data.lot_area_m2 != null ? `${Math.round(data.lot_area_m2)} m² lot` : null,
    },
    {
      label: 'Nearest building',
      value: data.nearest_structure_m != null ? `${data.nearest_structure_m.toFixed(1)} m` : '-',
      tone: 'wind',
      sub: 'Fire spread distance',
    },
  ]

  return (
    <section className="section">
      <div className="section-head">
        <h2>{hasImagery ? 'What the photo shows' : 'What we measured'}</h2>
        <p className="section-lede">
          {hasImagery
            ? 'Every number on this page traces back to these four measurements, taken from the pixels in the picture below.'
            : 'Every number on this page traces back to these four measurements.'}
        </p>
      </div>

      <figure className="evidence">
        <div className="evidence-image">
          {hasImagery ? (
            <div className="imagery" style={{ backgroundImage: `url(${data.imagery_png})` }}>
              {LAYERS.map(({ key, tone }) => {
                const src = data[`${key}_mask_png`]
                if (!layers[key] || !src) return null
                return (
                  <div
                    key={key}
                    className={`mask mask-${tone}`}
                    style={{ maskImage: `url(${src})`, WebkitMaskImage: `url(${src})` }}
                  />
                )
              })}
            </div>
          ) : (
            <div className="imagery imagery-missing">
              <p>No aerial photo came back for this location.</p>
              <p className="imagery-missing-sub">
                The measurements below could not be taken from imagery.
              </p>
            </div>
          )}
        </div>

        {/* Layer switches and a capture date only mean something when there is
            actually a photo. Claiming a capture date under a missing-imagery
            placeholder would be the exact overclaim this project avoids. */}
        {hasImagery && (
          <figcaption className="evidence-caption">
            <div className="layer-toggles" role="group" aria-label="Show or hide measured layers">
              {LAYERS.map(({ key, label, tone }) => (
                <button
                  key={key}
                  type="button"
                  className={`layer-toggle tone-${tone} ${layers[key] ? 'is-on' : ''}`}
                  aria-pressed={layers[key]}
                  onClick={() => toggle(key)}
                >
                  <span className="layer-swatch" aria-hidden="true" />
                  {label}
                </button>
              ))}
            </div>
            <p className={`capture-date ${dateKnown ? '' : 'is-flagged'}`}>
              {dateKnown
                ? `Photo taken ${data.imagery_date}`
                : 'Capture date unknown. This photo may be several years old.'}
            </p>
          </figcaption>
        )}
      </figure>

      <div className="measures">
        {measurements.map((m) => (
          <div className={`measure tone-${m.tone}`} key={m.label}>
            <div className="measure-label">{m.label}</div>
            <div className="measure-value tnum">{m.value}</div>
            {m.sub && <div className="measure-sub">{m.sub}</div>}
          </div>
        ))}
      </div>
    </section>
  )
}

/* -------------------------------------------------------------------------- */
/* verdict                                                                     */
/* -------------------------------------------------------------------------- */

function ConfidenceNote({ data }) {
  const implausible = data.roof_segmentation_plausible === false
  const lowConfidence = typeof data.confidence === 'number' && data.confidence < 0.5
  if (!implausible && !lowConfidence) return null

  const reasons = []
  if (data.address_precision && data.address_precision !== 'exact') {
    reasons.push(`the address only resolved to ${data.address_precision} level`)
  }
  if (implausible) reasons.push('the traced roof does not match the building footprint on record')

  return (
    <div className="notice notice-warn" role="status">
      <strong>These measurements are low confidence.</strong>{' '}
      {reasons.length > 0 && <>We flagged this because {reasons.join(', and ')}. </>}
      Try placing the pin directly on the centre of the roof and measuring again.
    </div>
  )
}

function Verdict({ data }) {
  const grade = data.risk_score?.grade
  const score = data.risk_score?.overall
  const tone = gradeTone(grade)
  const driver = biggestDriver(data.perils)
  const homeValue = data.home_value_estimate ?? data.estimated_value
  const valueConfidence = data.home_value_confidence ?? data.value_confidence

  return (
    <section className="section verdict">
      <div className={`panel score-panel tone-${tone}`}>
        <div className="score-copy">
          <p className="score-eyebrow">Safety score</p>
          <h2 className="score-word">
            {gradeWord(grade)}
            {grade && <span className={`grade-pill tone-${tone}`}>Grade {grade}</span>}
          </h2>
          <p className="score-sub">
            {driver
              ? `Mostly because ${plain(driver.plain_language).toLowerCase()}.`
              : 'Scored from the four measurements above and regional hazard data.'}
          </p>
        </div>
        <RiskGauge score={score} grade={grade} />
      </div>

      <div className="stack">
        <div className="panel stat-panel">
          <p className="stat-label">Yearly cost of this risk</p>
          <p className="stat-figure tnum">{money(data.annual_premium)}</p>
          <p className="stat-sub">
            What a full year of coverage on this home prices out to in our model.
          </p>
        </div>

        <div className="panel stat-panel">
          <p className="stat-label">Estimated home value</p>
          <p className="stat-figure tnum">{money(homeValue)}</p>
          <p className="stat-sub">
            A rough estimate, not an appraisal ({valueConfidence ?? 'low'} confidence)
            {data.premium_pct_of_value != null && (
              <>
                . Risk costs {(data.premium_pct_of_value * 100).toFixed(2)}% of that value each year
              </>
            )}
            .
          </p>
        </div>
      </div>
    </section>
  )
}

/* -------------------------------------------------------------------------- */
/* cost breakdown                                                              */
/* -------------------------------------------------------------------------- */

function CostBreakdown({ perils, total }) {
  const sum = perils.reduce((acc, p) => acc + p.premium, 0) || 1

  return (
    <section className="section">
      <div className="section-head">
        <h2>Where that cost comes from</h2>
        <p className="section-lede">
          Every dollar is attached to something we measured or looked up. No postal code averages.
        </p>
      </div>

      <div className="composition" role="img" aria-label="Share of yearly cost by peril">
        {perils.map((p) => (
          <div
            key={p.name}
            className={`composition-seg tone-${PERIL_TONE[p.name] ?? 'roof'}`}
            style={{ flexGrow: p.premium / sum }}
          />
        ))}
      </div>

      <ul className="peril-list">
        {perils.map((p) => {
          const driver = topDriverOf(p)
          return (
            <li className="peril" key={p.name}>
              <span className={`peril-key tone-${PERIL_TONE[p.name] ?? 'roof'}`} aria-hidden="true" />
              <div className="peril-body">
                <div className="peril-name">{PERIL_LABELS[p.name] ?? titleCase(p.name)}</div>
                {driver?.plain_language && (
                  <p className="peril-driver">{plain(driver.plain_language)}</p>
                )}
              </div>
              <div className="peril-amount tnum">
                {money(p.premium)}
                <span className="peril-share tnum">{Math.round((p.premium / sum) * 100)}%</span>
              </div>
            </li>
          )
        })}
      </ul>

      {total != null && (
        <div className="peril-total">
          <span>Total each year</span>
          <span className="tnum">{money(total)}</span>
        </div>
      )}
    </section>
  )
}

/* -------------------------------------------------------------------------- */
/* actions: the screen that wins                                               */
/* -------------------------------------------------------------------------- */

function MitigationCard({ m, best }) {
  const payback = years(m.payback_years)
  const tone = PERIL_TONE[m.peril] ?? 'roof'

  return (
    <li className={`action ${best ? 'is-best' : ''}`}>
      <div className="action-head">
        <span className={`tag tone-${tone}`}>{PERIL_LABELS[m.peril] ?? titleCase(m.peril)}</span>
        {best && <span className="tag tag-best">Pays back soonest</span>}
      </div>

      <h3 className="action-title">{plain(m.action)}</h3>

      <dl className="action-stats">
        <div>
          <dt>Costs once</dt>
          <dd className="tnum">{money(m.cost)}</dd>
        </div>
        <div>
          <dt>Saves each year</dt>
          <dd className="tnum">{money(m.annual_saving)}</dd>
        </div>
        <div>
          <dt>Pays for itself in</dt>
          <dd className="tnum">{payback ?? 'Not from savings alone'}</dd>
        </div>
        {m.risk_score_delta != null && m.risk_score_delta > 0 && (
          <div>
            <dt>Safety score</dt>
            <dd className="tnum">+{m.risk_score_delta.toFixed(1)}</dd>
          </div>
        )}
      </dl>

      {m.co_benefit && <p className="action-benefit">{plain(m.co_benefit)}</p>}
    </li>
  )
}

function Actions({ data }) {
  const [allDone, setAllDone] = useState(false)

  // Unmeasurable payback (null) sorts last, not first. `null - n` coerces to 0
  // and would otherwise rank it as if it paid back instantly.
  const sorted = [...(data.mitigations ?? [])].sort((a, b) => {
    if (a.payback_years == null) return 1
    if (b.payback_years == null) return -1
    return a.payback_years - b.payback_years
  })

  // Rank relatively, not against a fixed year threshold. An already-low-risk
  // house has less risk left to remove, so all of its paybacks are long: an
  // absolute cutoff left that property showing a single card while seven
  // collapsed out of sight. Take the best few that pay back at all, and let
  // the genuinely hopeless ones fall into the disclosure.
  const HEADLINE_COUNT = 4
  const payingBack = sorted.filter((m) => m.payback_years != null)
  const worthwhile = payingBack
    .slice(0, HEADLINE_COUNT)
    .filter((m) => m.payback_years <= PAYBACK_CEILING)
  const longTerm = sorted.filter((m) => !worthwhile.includes(m))

  const premiumNow = data.annual_premium
  const premiumAfter = data.premium_if_all_actions
  const scoreNow = data.risk_score?.overall
  const scoreAfter = data.risk_score_if_all_actions?.overall
  const saving = premiumNow != null && premiumAfter != null ? premiumNow - premiumAfter : null
  const upfront = sorted.reduce((acc, m) => acc + (m.cost ?? 0), 0)

  const shownPremium = allDone && premiumAfter != null ? premiumAfter : premiumNow
  const shownScore = allDone && scoreAfter != null ? scoreAfter : scoreNow
  const shownGrade = allDone ? data.risk_score_if_all_actions?.grade : data.risk_score?.grade

  return (
    <section className="section actions-section">
      <div className="section-head">
        <h2>What you can do about it</h2>
        <p className="section-lede">
          Ranked by how fast each fix pays for itself. Every one of them is also a climate adaptation
          measure.
        </p>
      </div>

      {saving != null && (
        <div className="panel summary">
          <div className="summary-toggle">
            <label className="switch">
              <input
                type="checkbox"
                checked={allDone}
                onChange={(e) => setAllDone(e.target.checked)}
              />
              <span className="switch-track" aria-hidden="true">
                <span className="switch-thumb" />
              </span>
              <span className="switch-label">Show my numbers with every fix done</span>
            </label>
          </div>

          <div className="summary-figures">
            <div className="summary-figure">
              <span className="summary-label">Yearly cost</span>
              <span className={`summary-value tnum ${allDone ? 'is-improved' : ''}`}>
                {money(shownPremium)}
              </span>
              {allDone && saving > 0 && (
                <span className="summary-delta tnum">{money(saving)} less each year</span>
              )}
            </div>
            <div className="summary-figure">
              <span className="summary-label">Safety score</span>
              {/* Whole numbers, matching the gauge. The same score showing as
                  48 in one place and 47.7 in another just looks like a bug. */}
              <span className={`summary-value tnum ${allDone ? 'is-improved' : ''}`}>
                {shownScore != null ? Math.round(shownScore) : '-'}
                {shownGrade && <span className="summary-grade">grade {shownGrade}</span>}
              </span>
            </div>
            <div className="summary-figure">
              <span className="summary-label">Total upfront</span>
              <span className="summary-value tnum">{money(upfront)}</span>
              <span className="summary-delta">for all {sorted.length} fixes</span>
            </div>
          </div>
        </div>
      )}

      <ol className="action-list">
        {worthwhile.map((m, i) => (
          <MitigationCard key={m.action} m={m} best={i === 0} />
        ))}
      </ol>

      {longTerm.length > 0 && (
        <details className="disclosure">
          <summary>Fixes that take much longer to pay back ({longTerm.length})</summary>
          <ol className="action-list action-list-quiet">
            {longTerm.map((m) => (
              <MitigationCard key={m.action} m={m} best={false} />
            ))}
          </ol>
        </details>
      )}
    </section>
  )
}

/* -------------------------------------------------------------------------- */
/* report                                                                      */
/* -------------------------------------------------------------------------- */

function Report({ data }) {
  return (
    <>
      <div className="report-head">
        <p className="report-label">Report for</p>
        <h1 className="report-address">{data.displayAddress || data.address}</h1>
      </div>

      <ConfidenceNote data={data} />
      <Verdict data={data} />
      <Evidence data={data} />
      {data.perils?.length > 0 && (
        <CostBreakdown perils={data.perils} total={data.annual_premium} />
      )}
      {data.mitigations?.length > 0 && <Actions data={data} />}

      <section className="section footnotes">
        <h2 className="footnotes-title">Read this before you quote any of it</h2>
        <div className="footnote-grid">
          <div className="footnote">
            <h3>These are modelled numbers</h3>
            <p>
              {plain(data.disclaimer) ||
                'Demonstration model, not an actuarial quote or a property appraisal.'}{' '}
              Rates are calibrated against published Canadian average premiums so the figures are
              plausible, not authoritative.
            </p>
          </div>
          <div className="footnote">
            <h3>The photo may be out of date</h3>
            <p>
              Aerial coverage varies enormously by address. Some are crisp and recent, others are
              years old at an oblique angle with half the roof in shadow. We show what we know about
              the capture rather than hiding it.
            </p>
          </div>
          <div className="footnote">
            <h3>Is this surveillance?</h3>
            <p>
              Fair question. The imagery is already public and already used commercially. What
              matters is who the output serves: this shows a homeowner their own risk and how to
              lower it, rather than handing an insurer a new reason to decline them.
            </p>
          </div>
        </div>
      </section>
    </>
  )
}

/* -------------------------------------------------------------------------- */

function App() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const reportRef = useRef(null)

  const handleAnalyze = async ({ address, displayAddress, lat, lon }) => {
    setLoading(true)
    setError(null)
    setData(null)
    try {
      const result = await fetchAnalysis({ address, lat, lon })
      setData({
        ...result,
        address: address || result.address,
        displayAddress: displayAddress || address || result.address,
      })
    } catch (err) {
      setError(err.message || 'Could not reach the analysis servers.')
    } finally {
      setLoading(false)
    }
  }

  const reset = () => {
    setData(null)
    setError(null)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  // Bring the report into view the moment it lands, so the demo does not need
  // a scroll to reach the result.
  useEffect(() => {
    if (data && reportRef.current) {
      reportRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }, [data])

  const demo = isDemoMode()

  return (
    <div className="page">
      <Cursor />
      {demo && (
        <div className="demo-banner" role="status">
          Offline demo. These are cached results from an earlier pipeline run, not a live
          measurement.
        </div>
      )}

      <header className="masthead">
        <div className="masthead-inner">
          <span className="wordmark">Sightline</span>
          {data && (
            <button type="button" className="btn btn-quiet" onClick={reset}>
              New address
            </button>
          )}
        </div>
      </header>

      <main className="shell">
        {!data && !loading && (
          <section className="intro">
            <h1 className="intro-title">
              See what your home&rsquo;s risk is really costing you.
            </h1>
            <p className="intro-lede">
              We measure your roof, tree cover and paving from the aerial photo, then show which
              fixes pay for themselves.
            </p>
            <AddressMap onConfirm={handleAnalyze} loading={loading} />
          </section>
        )}

        {loading && <Pipeline />}

        {error && !loading && (
          <div className="notice notice-error" role="alert">
            <strong>We could not finish that measurement.</strong>
            <p>{plain(error)}</p>
            <p className="notice-sub">
              Check that the vision service and the pricing service are both running. Setup steps
              are in CONTEXT.md.
            </p>
          </div>
        )}

        <div ref={reportRef}>{data && !loading && <Report data={data} />}</div>
      </main>

      <footer className="colophon">
        <p>
          Sightline automates a practice the insurance industry abandoned for cost reasons. From
          1875, Charles E. Goad hand-drew colour-coded fire insurance plans of Canadian cities so
          underwriters could price a block without visiting it. The colours on this page are his.
        </p>
      </footer>
    </div>
  )
}

export default App
