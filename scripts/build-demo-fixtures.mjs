/* Rebuilds src/demoData.generated.js from pricing/demo_cache/*.json.
 *
 * The offline demo mode (?demo=1) must never show hand-written numbers. Every
 * figure it displays comes out of the pricing engine and lands here verbatim.
 * Re-run this after regenerating the fixtures:
 *
 *   npm run build:demo
 */
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')

// Labels match the sample locations offered in AddressMap.jsx.
const FIXTURES = [
  { file: 'high_risk_wildfire_house.json', key: 'jasper', label: 'Jasper, Alberta' },
  { file: 'moderate_flood_house.json', key: 'toronto', label: 'Downtown Toronto, Ontario' },
  { file: 'low_risk_house.json', key: 'northyork', label: 'North York, Toronto, Ontario' },
]

const merged = FIXTURES.map(({ file, key, label }) => {
  const raw = JSON.parse(fs.readFileSync(path.join(root, 'pricing', 'demo_cache', file), 'utf8'))
  return {
    key,
    address: label,
    displayAddress: label,
    source: file,
    ...raw.contract_a,
    ...raw.contract_b,
  }
})

const body = `// GENERATED FILE. Do not hand-edit.
// Rebuilt from pricing/demo_cache/*.json, which the pricing engine itself
// produced. Every figure below came out of engine.py, none of it is invented.
// Regenerate after changing the fixtures:  npm run build:demo

export const DEMO_FIXTURES = ${JSON.stringify(merged, null, 2)}
`

const out = path.join(root, 'src', 'demoData.generated.js')
fs.writeFileSync(out, body)
console.log(`wrote ${path.relative(root, out)} (${merged.length} fixtures)`)
