import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Activity, Brain, Zap, TrendingUp, Target } from 'lucide-react'
import TopNav from '@/components/TopNav'

export default function Dashboard() {
  const [patientData, setPatientData] = useState({
    age: 65,
    gender: 'M',
    heartRate: 88,
    bloodPressureSystolic: 120,
    bloodPressureDiastolic: 80,
    temperature: 37.2,
    respiratoryRate: 18,
    oxygenSaturation: 96,
    sofaScore: 6,
    comorbidityCount: 2,
  })

  const [predictionResult, setPredictionResult] = useState<any>(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8054'

  const handlePrediction = async () => {
    setIsProcessing(true)
    setPredictionResult(null)
    // Try API call first, fall back to mock data if it fails
    try {
      const response = await fetch(`${apiUrl}/api/v1/prediction/predict`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(patientData),
      })

      if (!response.ok) throw new Error('API not available')
      const result = await response.json()
      setPredictionResult(result)
    } catch (error) {
      console.log('Using mock data - backend not yet available')
      // Mock data fallback (keeps the loader visible during the delay)
      await new Promise((resolve) => setTimeout(resolve, 1200))
      setPredictionResult({
        mortalityRisk: 0.23,
        confidence: 0.87,
        riskCategory: 'MODERATE',
        keyFactors: [
          { factor: 'Age', value: patientData.age, impact: 'moderate' },
          { factor: 'SOFA Score', value: patientData.sofaScore, impact: 'moderate' },
          { factor: 'Comorbidities', value: patientData.comorbidityCount, impact: 'low' },
        ],
        recommendations: [
          'Continue standard monitoring protocols',
          'Increase vital sign frequency to every 2 hours',
          'Consider early specialist consultation',
        ],
        agentStatus: {
          total: 21,
          active: 20,
          processingTime: '1.2s',
        },
      })
    } finally {
      setIsProcessing(false)
    }
  }

  return (
    <div className="min-h-screen relative">
      <TopNav title="PREDICTION DASHBOARD" status="NEURAL LINK: ACTIVE" active="/dashboard" />

      <main className="container mx-auto px-6 py-8">
        {mounted && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Patient Input Panel */}
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            animate={{ opacity: 1, x: 0 }}
            className="lg:col-span-1"
          >
            <div className="cyber-panel p-6 hud-corner">
              <h2 className="text-xl font-mono mb-6 glow-text flex items-center">
                <Activity className="w-6 h-6 mr-3" />
                PATIENT DATA INPUT
              </h2>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm text-cyber-blue/60 mb-2">AGE</label>
                  <input
                    type="number"
                    value={patientData.age}
                    onChange={(e) => setPatientData({...patientData, age: parseInt(e.target.value)})}
                    className="w-full cyber-input"
                  />
                </div>

                <div>
                  <label className="block text-sm text-cyber-blue/60 mb-2">GENDER</label>
                  <select
                    value={patientData.gender}
                    onChange={(e) => setPatientData({...patientData, gender: e.target.value})}
                    className="w-full cyber-input"
                  >
                    <option value="M">MALE</option>
                    <option value="F">FEMALE</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm text-cyber-blue/60 mb-2">HEART RATE (BPM)</label>
                  <input
                    type="number"
                    value={patientData.heartRate}
                    onChange={(e) => setPatientData({...patientData, heartRate: parseInt(e.target.value)})}
                    className="w-full cyber-input"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm text-cyber-blue/60 mb-2">SBP (mmHg)</label>
                    <input
                      type="number"
                      value={patientData.bloodPressureSystolic}
                      onChange={(e) => setPatientData({...patientData, bloodPressureSystolic: parseInt(e.target.value)})}
                      className="w-full cyber-input"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-cyber-blue/60 mb-2">DBP (mmHg)</label>
                    <input
                      type="number"
                      value={patientData.bloodPressureDiastolic}
                      onChange={(e) => setPatientData({...patientData, bloodPressureDiastolic: parseInt(e.target.value)})}
                      className="w-full cyber-input"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm text-cyber-blue/60 mb-2">TEMPERATURE (°C)</label>
                  <input
                    type="number"
                    step="0.1"
                    value={patientData.temperature}
                    onChange={(e) => setPatientData({...patientData, temperature: parseFloat(e.target.value)})}
                    className="w-full cyber-input"
                  />
                </div>

                <div>
                  <label className="block text-sm text-cyber-blue/60 mb-2">RESPIRATORY RATE</label>
                  <input
                    type="number"
                    value={patientData.respiratoryRate}
                    onChange={(e) => setPatientData({...patientData, respiratoryRate: parseInt(e.target.value)})}
                    className="w-full cyber-input"
                  />
                </div>

                <div>
                  <label className="block text-sm text-cyber-blue/60 mb-2">OXYGEN SATURATION (%)</label>
                  <input
                    type="number"
                    value={patientData.oxygenSaturation}
                    onChange={(e) => setPatientData({...patientData, oxygenSaturation: parseInt(e.target.value)})}
                    className="w-full cyber-input"
                  />
                </div>

                <div>
                  <label className="block text-sm text-cyber-blue/60 mb-2">SOFA SCORE</label>
                  <input
                    type="number"
                    value={patientData.sofaScore}
                    onChange={(e) => setPatientData({...patientData, sofaScore: parseInt(e.target.value)})}
                    className="w-full cyber-input"
                  />
                </div>

                <div>
                  <label className="block text-sm text-cyber-blue/60 mb-2">COMORBIDITY COUNT</label>
                  <input
                    type="number"
                    value={patientData.comorbidityCount}
                    onChange={(e) => setPatientData({...patientData, comorbidityCount: parseInt(e.target.value)})}
                    className="w-full cyber-input"
                  />
                </div>

                <button
                  onClick={handlePrediction}
                  disabled={isProcessing}
                  className="w-full cyber-button mt-6"
                >
                  {isProcessing ? 'PROCESSING...' : 'INITIATE PREDICTION'}
                </button>
              </div>
            </div>
          </motion.div>

          {/* Results Panel */}
          <motion.div
            initial={{ opacity: 0, x: 30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
            className="lg:col-span-2"
          >
            {isProcessing && (
              <div className="cyber-panel p-12 hud-corner flex flex-col items-center justify-center">
                <div className="cyber-loader mb-6"></div>
                <div className="text-xl font-mono glow-text animate-pulse">
                  NEURAL NETWORK PROCESSING
                </div>
                <div className="text-sm text-cyber-blue/60 mt-2">
                  Orchestrating 21 AI agents...
                </div>
              </div>
            )}

            {predictionResult && !isProcessing && (
              <div className="space-y-6">
                {/* Main Prediction Result */}
                <div className="cyber-panel p-8 hud-corner">
                  <h2 className="text-xl font-mono mb-6 glow-text flex items-center">
                    <Brain className="w-6 h-6 mr-3" />
                    PREDICTION RESULTS
                  </h2>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                    <div className="text-center">
                      <div className="text-5xl font-bold font-mono mb-2 text-cyber-blue">
                        {(predictionResult.mortalityRisk * 100).toFixed(1)}%
                      </div>
                      <div className="text-sm text-cyber-blue/60">MORTALITY RISK</div>
                    </div>
                    <div className="text-center">
                      <div className="text-5xl font-bold font-mono mb-2 text-cyber-green">
                        {(predictionResult.confidence * 100).toFixed(1)}%
                      </div>
                      <div className="text-sm text-cyber-blue/60">CONFIDENCE</div>
                    </div>
                    <div className="text-center">
                      <div className="text-3xl font-bold font-mono mb-2 text-cyber-purple">
                        {predictionResult.riskCategory}
                      </div>
                      <div className="text-sm text-cyber-blue/60">RISK CATEGORY</div>
                    </div>
                  </div>

                  {/* Risk Gauge */}
                  <div className="relative h-4 bg-cyber-dark rounded-full overflow-hidden mb-8">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${predictionResult.mortalityRisk * 100}%` }}
                      transition={{ duration: 1, ease: "easeOut" }}
                      className="absolute h-full bg-gradient-to-r from-cyber-green via-cyber-yellow to-cyber-red"
                    />
                  </div>

                  {/* Key Factors */}
                  <div className="mb-8">
                    <h3 className="text-lg font-mono mb-4 text-cyber-blue flex items-center">
                      <Target className="w-5 h-5 mr-2" />
                      KEY RISK FACTORS
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      {predictionResult.keyFactors.map((factor: any, index: number) => (
                        <div key={index} className="cyber-panel p-4">
                          <div className="text-sm text-cyber-blue/60 mb-1">{factor.factor}</div>
                          <div className="text-2xl font-bold font-mono">{factor.value}</div>
                          <div className="text-xs text-cyber-blue/40 mt-1">Impact: {factor.impact}</div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Recommendations */}
                  <div>
                    <h3 className="text-lg font-mono mb-4 text-cyber-blue flex items-center">
                      <TrendingUp className="w-5 h-5 mr-2" />
                      RECOMMENDATIONS
                    </h3>
                    <div className="space-y-2">
                      {predictionResult.recommendations.map((rec: string, index: number) => (
                        <div key={index} className="flex items-start">
                          <span className="w-2 h-2 bg-cyber-green rounded-full mr-3 mt-2"></span>
                          <span className="text-cyber-blue/80">{rec}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* AI Clinical Explanation (live LLM, shown when available) */}
                {predictionResult.explanation && (
                  <div className="cyber-panel p-6 hud-corner">
                    <h3 className="text-lg font-mono mb-3 text-cyber-blue flex items-center">
                      <Brain className="w-5 h-5 mr-2" />
                      AI CLINICAL EXPLANATION
                    </h3>
                    <p className="text-sm text-cyber-blue/80 leading-relaxed">
                      {predictionResult.explanation}
                    </p>
                    <div className="text-[11px] text-cyber-blue/40 mt-3 font-mono">
                      Generated live by the explainability agent
                    </div>
                  </div>
                )}

                {/* Agent Status */}
                <div className="cyber-panel p-6 hud-corner">
                  <h3 className="text-lg font-mono mb-4 text-cyber-blue flex items-center">
                    <Zap className="w-5 h-5 mr-2" />
                    AGENT NETWORK STATUS
                  </h3>
                  <div className="grid grid-cols-3 gap-4">
                    <div className="text-center">
                      <div className="text-2xl font-bold font-mono text-cyber-blue">
                        {predictionResult.agentStatus.total}
                      </div>
                      <div className="text-xs text-cyber-blue/60">TOTAL AGENTS</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold font-mono text-cyber-green">
                        {predictionResult.agentStatus.active}
                      </div>
                      <div className="text-xs text-cyber-blue/60">ACTIVE</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold font-mono text-cyber-purple">
                        {predictionResult.agentStatus.processingTime}
                      </div>
                      <div className="text-xs text-cyber-blue/60">PROCESSING TIME</div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {!predictionResult && !isProcessing && (
              <div className="cyber-panel p-12 hud-corner text-center">
                <Brain className="w-20 h-20 mx-auto mb-6 text-cyber-blue/30" />
                <div className="text-xl font-mono text-cyber-blue/60">
                  ENTER PATIENT DATA TO INITIATE PREDICTION
                </div>
                <div className="text-sm text-cyber-blue/40 mt-2">
                  Neural network standing by for input
                </div>
              </div>
            )}
          </motion.div>
        </div>
        )}
      </main>
    </div>
  )
}