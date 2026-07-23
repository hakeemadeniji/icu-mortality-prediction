import { useState } from 'react'
import { motion } from 'framer-motion'
import { Activity, AlertTriangle, HeartPulse, Stethoscope, FlaskConical } from 'lucide-react'
import TopNav from '@/components/TopNav'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8054'

// Field names match the backend ClinicalSnapshot exactly (no mapping needed).
const defaultForm: Record<string, any> = {
  age: 72, sex: 'M', admission_type: 'medical',
  heart_rate: 118, resp_rate: 26, sbp: 96, dbp: 58, temperature: 38.6,
  spo2: 91, fio2: 0.4, on_supplemental_o2: true, gcs: 14, confusion: false,
  mechanical_ventilation: false, vasopressors: false,
  wbc: 15.5, platelets: 110, bilirubin: 1.8, creatinine: 2.2,
  baseline_creatinine: 1.0, bun: 32, lactate: 3.1, pao2: 72,
  // Blood gas & chemistry (APACHE II / SAPS II)
  arterial_ph: 7.32, paco2: 42, sodium: 134, potassium: 4.6, bicarbonate: 19,
  hematocrit: 34, urine_output_ml: 900,
  severe_comorbidity: false, postop_elective: false,
  metastatic_cancer: false, hematologic_malignancy: false, aids: false,
}

const bandClass = (band: string): string =>
  ({
    low: 'text-cyber-green border-cyber-green/40',
    'low-medium': 'text-cyber-green border-cyber-green/40',
    medium: 'text-cyber-yellow border-cyber-yellow/50',
    high: 'text-cyber-red border-cyber-red/50',
    critical: 'text-cyber-red border-cyber-red/70',
    unknown: 'text-cyber-white/40 border-cyber-white/20',
  }[band] || 'text-cyber-white/40 border-cyber-white/20')

const overallClass = (band: string): string =>
  ({
    low: 'text-cyber-green', 'low-medium': 'text-cyber-green',
    medium: 'text-cyber-yellow', high: 'text-cyber-red', critical: 'text-cyber-red',
  }[band] || 'text-cyber-white')

type FieldDef = { key: string; label: string; unit?: string; step?: number }

const VITALS: FieldDef[] = [
  { key: 'heart_rate', label: 'Heart rate', unit: 'bpm' },
  { key: 'resp_rate', label: 'Resp. rate', unit: '/min' },
  { key: 'sbp', label: 'Systolic BP', unit: 'mmHg' },
  { key: 'dbp', label: 'Diastolic BP', unit: 'mmHg' },
  { key: 'temperature', label: 'Temperature', unit: '°C', step: 0.1 },
  { key: 'spo2', label: 'SpO₂', unit: '%' },
  { key: 'fio2', label: 'FiO₂', unit: 'frac', step: 0.01 },
  { key: 'gcs', label: 'GCS', unit: '3–15' },
]
const LABS: FieldDef[] = [
  { key: 'wbc', label: 'WBC', unit: '×10³' },
  { key: 'platelets', label: 'Platelets', unit: '×10³' },
  { key: 'bilirubin', label: 'Bilirubin', unit: 'mg/dL', step: 0.1 },
  { key: 'creatinine', label: 'Creatinine', unit: 'mg/dL', step: 0.1 },
  { key: 'baseline_creatinine', label: 'Baseline creat.', unit: 'mg/dL', step: 0.1 },
  { key: 'bun', label: 'BUN', unit: 'mg/dL' },
  { key: 'lactate', label: 'Lactate', unit: 'mmol/L', step: 0.1 },
  { key: 'pao2', label: 'PaO₂', unit: 'mmHg' },
]
const CHEM: FieldDef[] = [
  { key: 'arterial_ph', label: 'Arterial pH', unit: 'pH', step: 0.01 },
  { key: 'paco2', label: 'PaCO₂', unit: 'mmHg' },
  { key: 'sodium', label: 'Sodium', unit: 'mmol/L' },
  { key: 'potassium', label: 'Potassium', unit: 'mmol/L', step: 0.1 },
  { key: 'bicarbonate', label: 'Bicarbonate', unit: 'mEq/L' },
  { key: 'hematocrit', label: 'Hematocrit', unit: '%' },
  { key: 'urine_output_ml', label: 'Urine output', unit: 'mL/24h' },
]
const FLAGS: FieldDef[] = [
  { key: 'on_supplemental_o2', label: 'Supplemental O₂' },
  { key: 'confusion', label: 'New confusion' },
  { key: 'mechanical_ventilation', label: 'Mech. ventilation' },
  { key: 'vasopressors', label: 'Vasopressors' },
  { key: 'severe_comorbidity', label: 'Severe comorbidity' },
  { key: 'postop_elective', label: 'Elective post-op' },
  { key: 'metastatic_cancer', label: 'Metastatic cancer' },
  { key: 'hematologic_malignancy', label: 'Heme malignancy' },
  { key: 'aids', label: 'AIDS' },
]

export default function RiskPage() {
  const [form, setForm] = useState<Record<string, any>>(defaultForm)
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const setField = (k: string, v: any) => setForm((f) => ({ ...f, [k]: v }))

  const assess = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${API_URL}/api/v1/risk/assess`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      setResult(await res.json())
    } catch {
      setError('Backend unavailable — start the API on :8054 to compute scores.')
      setResult(null)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen relative">
      <TopNav title="CLINICAL RISK PANEL" status="MULTI-SCORE ASSESSMENT" active="/risk" />

      {/* Persistent safety banner (intended use) */}
      <div className="bg-cyber-yellow/5 border-b border-cyber-yellow/20">
        <div className="container mx-auto px-6 py-2 text-[11px] text-cyber-yellow/80 flex items-start gap-2">
          <AlertTriangle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
          <span>
            Decision support only — <strong>not a validated medical device</strong>. For qualified
            adult-ICU clinicians; not for autonomous diagnosis or treatment. See docs/VALIDATION.md.
          </span>
        </div>
      </div>

      <main className="container mx-auto px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Input form */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="lg:col-span-1"
          >
            <div className="cyber-panel p-6 hud-corner">
              <h2 className="text-lg font-mono mb-1 glow-text flex items-center text-cyber-white">
                <Stethoscope className="w-5 h-5 mr-2 text-cyber-green" />
                PATIENT SNAPSHOT
              </h2>
              <p className="text-xs text-cyber-green/60 mb-5">
                Enter what you have — each score uses the subset it needs.
              </p>

              <div className="grid grid-cols-2 gap-3 mb-4">
                <NumberField label="Age" unit="yr" value={form.age} onChange={(v: any) => setField('age', v)} />
                <div>
                  <label className="block text-[11px] text-cyber-green/70 mb-1 uppercase tracking-wider">Sex</label>
                  <select
                    value={form.sex}
                    onChange={(e) => setField('sex', e.target.value)}
                    className="cyber-input"
                  >
                    <option value="M">Male</option>
                    <option value="F">Female</option>
                  </select>
                </div>
              </div>

              <div className="mb-4">
                <label className="block text-[11px] text-cyber-green/70 mb-1 uppercase tracking-wider">Admission type</label>
                <select
                  value={form.admission_type}
                  onChange={(e) => setField('admission_type', e.target.value)}
                  className="cyber-input"
                >
                  <option value="medical">Medical</option>
                  <option value="unscheduled_surgical">Unscheduled surgical</option>
                  <option value="scheduled_surgical">Scheduled surgical</option>
                </select>
              </div>

              <SectionLabel icon={<HeartPulse className="w-4 h-4" />} text="Vitals" />
              <div className="grid grid-cols-2 gap-3 mb-4">
                {VITALS.map((f) => (
                  <NumberField key={f.key} label={f.label} unit={f.unit} step={f.step}
                    value={form[f.key]} onChange={(v: any) => setField(f.key, v)} />
                ))}
              </div>

              <SectionLabel icon={<FlaskConical className="w-4 h-4" />} text="Labs" />
              <div className="grid grid-cols-2 gap-3 mb-4">
                {LABS.map((f) => (
                  <NumberField key={f.key} label={f.label} unit={f.unit} step={f.step}
                    value={form[f.key]} onChange={(v: any) => setField(f.key, v)} />
                ))}
              </div>

              <SectionLabel icon={<FlaskConical className="w-4 h-4" />} text="Blood gas & chemistry" />
              <div className="grid grid-cols-2 gap-3 mb-4">
                {CHEM.map((f) => (
                  <NumberField key={f.key} label={f.label} unit={f.unit} step={f.step}
                    value={form[f.key]} onChange={(v: any) => setField(f.key, v)} />
                ))}
              </div>

              <SectionLabel icon={<Activity className="w-4 h-4" />} text="Support / flags" />
              <div className="grid grid-cols-2 gap-2 mb-6">
                {FLAGS.map((f) => (
                  <label key={f.key} className="flex items-center gap-2 text-xs text-cyber-white/80 cursor-pointer">
                    <input type="checkbox" checked={!!form[f.key]}
                      onChange={(e) => setField(f.key, e.target.checked)}
                      className="accent-[#2bff88] w-4 h-4" />
                    {f.label}
                  </label>
                ))}
              </div>

              <button onClick={assess} disabled={loading} className="w-full cyber-button py-3">
                {loading ? 'ASSESSING…' : 'ASSESS RISK'}
              </button>
            </div>
          </motion.div>

          {/* Results */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 }}
            className="lg:col-span-2"
          >
            {error && (
              <div className="cyber-panel p-6 hud-corner border-cyber-red/40">
                <div className="flex items-center text-cyber-red">
                  <AlertTriangle className="w-5 h-5 mr-2" /> {error}
                </div>
              </div>
            )}

            {!result && !error && (
              <div className="cyber-panel p-12 hud-corner text-center">
                <Stethoscope className="w-16 h-16 mx-auto mb-4 text-cyber-green/30" />
                <div className="text-lg font-mono text-cyber-green/60">
                  Enter a patient snapshot and run the assessment
                </div>
                <div className="text-sm text-cyber-green/40 mt-2">
                  11 validated scores across deterioration, sepsis, pneumonia, shock, respiratory, renal & ICU mortality
                </div>
              </div>
            )}

            {result && (
              <div className="space-y-6">
                {/* Input-data validation warnings */}
                {result.input_warnings?.length > 0 && (
                  <div className="cyber-panel p-4 hud-corner border-cyber-yellow/40">
                    <div className="text-cyber-yellow text-xs font-mono font-bold mb-2 flex items-center">
                      <AlertTriangle className="w-4 h-4 mr-2" />
                      INPUT DATA WARNINGS ({result.input_warnings.length})
                    </div>
                    <ul className="space-y-1">
                      {result.input_warnings.map((w: any, i: number) => (
                        <li key={i} className="text-[11px] text-cyber-yellow/80">• {w.message}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Overall + alerts */}
                <div className="cyber-panel p-6 hud-corner">
                  <div className="flex items-baseline justify-between mb-4">
                    <span className="text-sm text-cyber-green/70 uppercase tracking-widest">Overall risk</span>
                    <span className={`text-3xl font-black font-mono ${overallClass(result.overall_risk)}`}>
                      {String(result.overall_risk).toUpperCase()}
                    </span>
                  </div>
                  <div className="text-xs text-cyber-green/50 mb-4">
                    {result.computed_count}/{result.total_scores} scores computed from the snapshot
                  </div>
                  {result.alerts?.length > 0 ? (
                    <div className="space-y-2">
                      {result.alerts.map((a: any) => (
                        <div key={a.key} className={`flex items-start gap-3 border-l-2 pl-3 py-1 ${bandClass(a.band)}`}>
                          <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" />
                          <div>
                            <span className="font-mono text-sm font-bold">{a.name} = {String(a.score)}</span>
                            <span className="text-xs text-cyber-white/70 ml-2">{a.message}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-sm text-cyber-green/70">No medium+ alerts from computed scores.</div>
                  )}
                </div>

                {/* Score cards */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {result.scores.map((s: any) => (
                    <div key={s.key} className={`cyber-panel p-4 hud-corner ${!s.computable ? 'opacity-50' : ''}`}>
                      <div className="flex items-start justify-between mb-1">
                        <h3 className="font-mono text-sm text-cyber-white">{s.name}</h3>
                        <span className={`text-xs font-mono px-2 py-0.5 border rounded ${bandClass(s.band)}`}>
                          {s.computable ? `${s.score}${s.max_score ? '/' + s.max_score : ''} · ${s.band}` : 'n/a'}
                        </span>
                      </div>
                      <div className="text-[11px] text-cyber-green/50 mb-2">{s.target}</div>
                      <p className="text-xs text-cyber-white/75 leading-relaxed mb-2">{s.interpretation}</p>
                      {s.computable && s.components?.length > 0 && (
                        <div className="flex flex-wrap gap-1.5 mb-2">
                          {s.components.map((c: any, i: number) => (
                            <span key={i} className="text-[10px] font-mono text-cyber-green/70 bg-cyber-green/5 border border-cyber-green/15 rounded px-1.5 py-0.5">
                              {c.name}: {String(c.value)}{c.points != null ? ` (+${c.points})` : ''}
                            </span>
                          ))}
                        </div>
                      )}
                      {!s.computable && s.missing?.length > 0 && (
                        <div className="text-[10px] text-cyber-white/40">needs: {s.missing.join(', ')}</div>
                      )}
                      <div className="text-[10px] text-cyber-green/30 mt-1 truncate" title={s.reference}>{s.reference}</div>
                    </div>
                  ))}
                </div>

                <div className="text-[11px] text-cyber-white/40 leading-relaxed border-t border-cyber-green/15 pt-3">
                  {result.disclaimer}
                  {result.engine_version && (
                    <div className="mt-2 font-mono text-cyber-white/30">
                      engine v{result.engine_version}
                      {result.assessment_id ? ` · assessment ${String(result.assessment_id).slice(0, 8)}` : ''}
                      {result.input_hash ? ` · hash ${result.input_hash}` : ''}
                    </div>
                  )}
                </div>
              </div>
            )}
          </motion.div>
        </div>
      </main>
    </div>
  )
}

function SectionLabel({ icon, text }: { icon: any; text: string }) {
  return (
    <div className="flex items-center gap-2 text-cyber-green text-xs font-semibold uppercase tracking-widest mb-2 mt-1">
      {icon}
      {text}
    </div>
  )
}

function NumberField({ label, unit, value, onChange, step }: any) {
  return (
    <div>
      <label className="block text-[11px] text-cyber-green/70 mb-1 uppercase tracking-wider">
        {label} {unit && <span className="text-cyber-green/40">({unit})</span>}
      </label>
      <input
        type="number"
        step={step ?? 1}
        value={value ?? ''}
        onChange={(e) => onChange(e.target.value === '' ? null : parseFloat(e.target.value))}
        className="cyber-input"
      />
    </div>
  )
}
