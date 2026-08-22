import { useEffect, useRef, useState } from 'react'
import AddressMap from './AddressMap'
import Rail from './Rail'
import TitlePage from './TitlePage'
import RiskGauge from './RiskGauge'
import { gradeTone, gradeWord } from './grade'
import { fetchAnalysis } from './api'
import { isDemoMode } from './demoData'
import { useCountUp, useReveal } from './motion'
import { useTheme } from './theme'
import './App.css'
// Loaded last on purpose. The sheet treatment restates surfaces that App.css
// styles as soft cards, and at equal specificity the later stylesheet wins -
// so ordering, not !important, is what makes it hold.
import './sheet.css'

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

/* Headline words rise in sequence. Split on spaces rather than characters:
   per-letter animation on a full sentence reads as a gimmick and, more
   practically, hands a screen reader a pile of single letters. Each word keeps
   its trailing space so the line still wraps normally. */
function StaggeredWords({ text, step = 55 }) {
  const words = text.split(' ')
  return (
    <>
      {words.map((word, i) => (
        <span
          key={`${word}-${i}`}
          className="stagger-word"
          style={{ animationDelay: `${i * step}ms` }}
        >
          {word}
          {i < words.length - 1 ? ' ' : ''}
        </span>
      ))}
    </>
  )
}

/* Headline figures are entry points, not endpoints. Clicking one takes you to
   the section that explains it, which is the question a person actually has
   when they read a number they did not expect. */
function jumpTo(id) {
  const el = document.getElementById(id)
  if (!el) return
  el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  el.classList.add('is-targeted')
  window.setTimeout(() => el.classList.remove('is-targeted'), 1400)
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
  'Measuring vegetation and paving',
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
  { key: 'canopy', label: 'Vegetation', tone: 'canopy' },
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
      label: 'Vegetation over roof',
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
    <section className="section" id="measurements">
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

  // The two headline figures count up once they scroll into view. They are the
  // numbers the whole page exists to deliver, so they get the one flourish.
  const [premiumRef, premiumCount] = useCountUp(data.annual_premium)
  const [valueRef, valueCount] = useCountUp(homeValue)

  return (
    <section className="section verdict" id="verdict">
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
        <button
          type="button"
          className="gauge-link"
          onClick={() => jumpTo('measurements')}
          aria-label={`Safety score ${score ?? ''} out of 100. See the measurements behind it.`}
        >
          <RiskGauge score={score} grade={grade} />
          <span className="gauge-link-hint">Why this score?</span>
        </button>
      </div>

      <div className="stack">
        <div className="panel stat-panel">
          <p className="stat-label">Yearly cost of this risk</p>
          <button
            type="button"
            className="stat-figure stat-figure-link tnum"
            ref={premiumRef}
            onClick={() => jumpTo('cost-breakdown')}
          >
            {money(premiumCount)}
            <span className="stat-figure-hint">See where it comes from</span>
          </button>
          <p className="stat-sub">
            What a full year of coverage on this home prices out to in our model.
          </p>
        </div>

        <div className="panel stat-panel value-panel">
          <p className="stat-label">Estimated home value</p>
          <p className="stat-figure tnum" ref={valueRef}>{money(valueCount)}</p>
          {/* Showing the working, because this figure is the least certain
              number on the page and a bare total invites more trust than it
              has earned. Every input here is one we actually measured. */}
          <div className="value-source">
            {data.roof_area_m2 != null && (
              <p className="value-source-row">
                <span>Measured roof footprint</span>
                <span>{Math.round(data.roof_area_m2)} m²</span>
              </p>
            )}
            <p className="value-source-row">
              <span>Assumed floor area</span>
              <span>
                {data.roof_area_m2 != null ? `${Math.round(data.roof_area_m2 * 1.6)} m²` : '-'}
              </span>
            </p>
            <p className="value-source-row">
              <span>Regional price per m²</span>
              <span>
                {data.roof_area_m2 && homeValue
                  ? money(homeValue / (data.roof_area_m2 * 1.6))
                  : '-'}
              </span>
            </p>
            {data.premium_pct_of_value != null && (
              <p className="value-source-row">
                <span>Risk cost as share of value</span>
                <span>{(data.premium_pct_of_value * 100).toFixed(2)}% a year</span>
              </p>
            )}
          </div>
          <p className="value-caveat">
            Derived from the roof we measured and a regional price per square metre. It is
            not an appraisal and has not been checked against a sale or a listing, so treat
            it as a rough scale rather than a valuation ({valueConfidence ?? 'low'} confidence).
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
  // Pointing at a band names it and prices it right there, so the bar answers
  // "what is that red part costing me" without a trip to the legend.
  const [held, setHeld] = useState(null)

  return (
    <section className="section" id="cost-breakdown">
      <div className="section-head">
        <h2>Where that cost comes from</h2>
        <p className="section-lede">
          Every dollar is attached to something we measured. Point at a band to price it.
        </p>
      </div>

      <div className="composition" aria-label="Share of yearly cost by peril">
        {perils.map((p) => (
          <button
            type="button"
            key={p.name}
            className={`composition-seg tone-${PERIL_TONE[p.name] ?? 'roof'}${held === p.name ? ' is-held' : ''}${held && held !== p.name ? ' is-muted' : ''}`}
            style={{ flexGrow: p.premium / sum }}
            onMouseEnter={() => setHeld(p.name)}
            onMouseLeave={() => setHeld(null)}
            onFocus={() => setHeld(p.name)}
            onBlur={() => setHeld(null)}
            aria-label={`${PERIL_LABELS[p.name] ?? p.name}: ${money(p.premium)} a year, ${Math.round((p.premium / sum) * 100)} percent of the total`}
          />
        ))}
      </div>

      <div className={`composition-readout${held ? ' is-shown' : ''}`} aria-live="polite">
        {(() => {
          const p = perils.find((x) => x.name === held)
          if (!p) return <span className="composition-readout-idle">Point at a band to see what it costs</span>
          return (
            <>
              <span className={`composition-readout-key tone-${PERIL_TONE[p.name] ?? 'roof'}`} aria-hidden="true" />
              <span className="composition-readout-name">{PERIL_LABELS[p.name] ?? titleCase(p.name)}</span>
              <span className="composition-readout-value tnum">{money(p.premium)}</span>
              <span className="composition-readout-share tnum">
                {Math.round((p.premium / sum) * 100)}% of the total
              </span>
            </>
          )
        })()}
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
    <section className="section actions-section" id="what-to-do">
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

/* Wrapper so a section lifts in the first time it is scrolled to. Kept as a
   wrapper rather than a prop on each section so the sections themselves stay
   unaware of animation entirely. */
function Reveal({ children }) {
  const [ref, shown] = useReveal()
  return (
    <div ref={ref} className={`reveal${shown ? ' is-in' : ''}`}>
      {children}
    </div>
  )
}

function Report({ data }) {
  return (
    <>
      <div className="report-head">
        <p className="report-label">Report for</p>
        <h1 className="report-address">{data.displayAddress || data.address}</h1>
      </div>

      <ConfidenceNote data={data} />
      <Reveal><Verdict data={data} /></Reveal>
      <Reveal><Evidence data={data} /></Reveal>
      {data.perils?.length > 0 && (
        <Reveal>
          <CostBreakdown perils={data.perils} total={data.annual_premium} />
        </Reveal>
      )}
      {data.mitigations?.length > 0 && (
        <Reveal><Actions data={data} /></Reveal>
      )}

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
  const [theme, toggleTheme] = useTheme()
  // The title page is the entry point; the tool proper is behind the CTA.
  const [entered, setEntered] = useState(false)

  if (!entered) {
    return (
      <>
        <TitlePage onEnter={() => setEntered(true)} />
      </>
    )
  }

  return (
    <div className="page">
      {demo && (
        <div className="demo-banner" role="status">
          Offline demo. These are cached results from an earlier pipeline run, not a live
          measurement.
        </div>
      )}

      <header className="masthead">
        <div className="masthead-inner">
          <button type="button" className="wordmark" onClick={() => setEntered(false)}>
            Sightline
          </button>
          {data && (
            <button type="button" className="btn btn-quiet" onClick={reset}>
              New address
            </button>
          )}
          <button
            type="button"
            className="theme-toggle"
            onClick={toggleTheme}
            aria-pressed={theme === 'dark'}
            title={theme === 'light' ? 'Switch to dark' : 'Switch to light'}
          >
            <span className="theme-toggle-track" aria-hidden="true">
              <span className="theme-toggle-knob" />
            </span>
            {theme === 'light' ? 'Light' : 'Dark'}
          </button>
        </div>
      </header>

      <main className="shell">
        {!data && !loading && (
          <section className="intro">
            <h1 className="intro-title">
              <StaggeredWords text="See what your home’s risk is really costing you." />
            </h1>
            <p className="intro-lede">
              We measure your roof, vegetation and paving from the aerial photo, then show which
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
        {data && !loading && <Rail />}
      </main>

    </div>
  )
}

export default App
