import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Brain, Activity, Zap, Clock, CheckCircle, AlertCircle, Cpu } from 'lucide-react'
import TopNav from '@/components/TopNav'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8054'

function formatLastRun(iso: string | null): string {
  if (!iso) return '—'
  const secs = Math.max(0, (Date.now() - new Date(iso).getTime()) / 1000)
  if (secs < 60) return `${Math.round(secs)}s ago`
  if (secs < 3600) return `${Math.round(secs / 60)}m ago`
  return `${Math.round(secs / 3600)}h ago`
}

export default function AgentsPage() {
  const [agents, setAgents] = useState([
    { id: 'data_ingestion', name: 'Data Ingestion', status: 'active', model: 'GLM', executions: 1523, lastExecution: '2s ago' },
    { id: 'clinical_nlp', name: 'Clinical NLP', status: 'active', model: 'Claude Opus', executions: 847, lastExecution: '5s ago' },
    { id: 'model_ensemble', name: 'Model Ensemble', status: 'active', model: 'Claude Opus', executions: 1523, lastExecution: '2s ago' },
    { id: 'vitals_analysis', name: 'Vitals Analysis', status: 'active', model: 'GLM', executions: 1523, lastExecution: '2s ago' },
    { id: 'labs_analysis', name: 'Labs Analysis', status: 'active', model: 'GLM', executions: 1489, lastExecution: '3s ago' },
    { id: 'medication_analysis', name: 'Medication Analysis', status: 'active', model: 'Claude Opus', executions: 1245, lastExecution: '4s ago' },
    { id: 'comorbidity_analysis', name: 'Comorbidity Analysis', status: 'active', model: 'Claude Opus', executions: 1523, lastExecution: '2s ago' },
    { id: 'demographics_analysis', name: 'Demographics Analysis', status: 'active', model: 'Claude Haiku', executions: 1523, lastExecution: '2s ago' },
    { id: 'confidence_estimation', name: 'Confidence Estimation', status: 'active', model: 'Claude Opus', executions: 1523, lastExecution: '2s ago' },
    { id: 'explainability', name: 'Explainability', status: 'active', model: 'Claude Opus', executions: 1523, lastExecution: '2s ago' },
    { id: 'fairness_monitoring', name: 'Fairness Monitoring', status: 'active', model: 'Claude Opus', executions: 456, lastExecution: '1m ago' },
    { id: 'alert_generation', name: 'Alert Generation', status: 'active', model: 'Claude Haiku', executions: 234, lastExecution: '30s ago' },
    { id: 'evaluation_monitoring', name: 'Evaluation Monitoring', status: 'active', model: 'GLM', executions: 89, lastExecution: '5m ago' },
    { id: 'correction_trigger', name: 'Correction Trigger', status: 'idle', model: 'Claude Opus', executions: 12, lastExecution: '1h ago' },
    { id: 'knowledge_retrieval', name: 'Knowledge Retrieval', status: 'active', model: 'Claude Haiku', executions: 567, lastExecution: '10s ago' },
    { id: 'clinical_guidelines', name: 'Clinical Guidelines', status: 'active', model: 'Claude Opus', executions: 345, lastExecution: '45s ago' },
    { id: 'patient_context', name: 'Patient Context', status: 'active', model: 'Claude Opus', executions: 1523, lastExecution: '2s ago' },
    { id: 'data_quality', name: 'Data Quality', status: 'active', model: 'GLM', executions: 1523, lastExecution: '2s ago' },
    { id: 'feature_engineering', name: 'Feature Engineering', status: 'active', model: 'Claude Opus', executions: 1523, lastExecution: '2s ago' },
    { id: 'time_series_analysis', name: 'Time Series Analysis', status: 'active', model: 'GLM', executions: 1102, lastExecution: '6s ago' },
    { id: 'risk_assessment', name: 'Risk Assessment', status: 'active', model: 'Claude Opus', executions: 1523, lastExecution: '2s ago' },
    { id: 'clinical_decision_support', name: 'Clinical Decision Support', status: 'active', model: 'Claude Opus', executions: 789, lastExecution: '15s ago' },
  ])
  const [live, setLive] = useState(false)

  useEffect(() => {
    const controller = new AbortController()
    fetch(`${API_URL}/api/v1/agents/list`, { signal: controller.signal })
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then((data: any[]) => {
        setAgents(
          data.map((a) => ({
            id: a.agent_id,
            name: a.name,
            status: a.status,
            model: a.model || 'Claude Opus',
            executions: a.execution_count ?? 0,
            lastExecution: formatLastRun(a.last_execution),
          }))
        )
        setLive(true)
      })
      .catch(() => {/* keep mock data — backend unavailable */})
    return () => controller.abort()
  }, [])

  // Derived stats (live once fetched, otherwise from the mock seed)
  const totalAgents = agents.length
  const activeAgents = agents.filter((a) => a.status === 'active').length
  const idleAgents = agents.filter((a) => a.status === 'idle').length
  const totalExecutions = agents.reduce((sum, a) => sum + (a.executions || 0), 0)

  const modelCounts = agents.reduce((acc: Record<string, number>, a) => {
    acc[a.model] = (acc[a.model] || 0) + 1
    return acc
  }, {})

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'text-cyber-green'
      case 'idle': return 'text-cyber-yellow'
      case 'error': return 'text-cyber-red'
      default: return 'text-cyber-blue'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active': return <CheckCircle className="w-4 h-4" />
      case 'idle': return <Clock className="w-4 h-4" />
      case 'error': return <AlertCircle className="w-4 h-4" />
      default: return <Activity className="w-4 h-4" />
    }
  }

  return (
    <div className="min-h-screen relative">
      <TopNav
        title="AGENT MONITORING"
        status={live ? 'LIVE • BACKEND CONNECTED' : 'MOCK DATA • BACKEND OFFLINE'}
        active="/agents"
      />

      <main className="container mx-auto px-6 py-8">
        {/* Overview Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <StatCard title="TOTAL AGENTS" value={String(totalAgents)} subtitle="AI SYSTEMS" color="cyber-blue" />
          <StatCard title="ACTIVE AGENTS" value={String(activeAgents)} subtitle="ONLINE" color="cyber-green" />
          <StatCard title="IDLE AGENTS" value={String(idleAgents)} subtitle="STANDBY" color="cyber-yellow" />
          <StatCard title="TOTAL EXECUTIONS" value={totalExecutions.toLocaleString()} subtitle="PROCESSED" color="cyber-purple" />
        </div>

        {/* Agent Grid */}
        <div className="cyber-panel p-6 hud-corner">
          <h2 className="text-xl font-mono mb-6 glow-text flex items-center">
            <Brain className="w-6 h-6 mr-3" />
            AGENT NETWORK STATUS
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {agents.map((agent, index) => (
              <motion.div
                key={agent.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
                className="cyber-panel p-4 hud-corner"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className={`flex items-center ${getStatusColor(agent.status)}`}>
                    {getStatusIcon(agent.status)}
                    <span className="ml-2 text-xs font-mono">{agent.status.toUpperCase()}</span>
                  </div>
                  <div className="text-xs text-cyber-blue/40">#{index + 1}</div>
                </div>

                <h3 className="font-mono text-sm text-cyber-blue mb-2">{agent.name}</h3>

                <div className="space-y-2">
                  <div className="flex justify-between text-xs">
                    <span className="text-cyber-blue/60">Model</span>
                    <span className="text-cyber-blue/80">{agent.model}</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-cyber-blue/60">Executions</span>
                    <span className="text-cyber-blue/80">{agent.executions.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-cyber-blue/60">Last Run</span>
                    <span className="text-cyber-blue/80">{agent.lastExecution}</span>
                  </div>
                </div>

                <div className="mt-3 pt-3 border-t border-cyber-blue/20">
                  <div className="flex items-center text-xs text-cyber-blue/40">
                    <Cpu className="w-3 h-3 mr-1" />
                    <span>AGENT ID: {agent.id}</span>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>

        {/* Agent Performance */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mt-8">
          <div className="cyber-panel p-6 hud-corner">
            <h3 className="text-lg font-mono mb-4 text-cyber-blue flex items-center">
              <Zap className="w-5 h-5 mr-2" />
              MODEL DISTRIBUTION
            </h3>
            <div className="space-y-4">
              <ModelBar name="Claude Opus" count={modelCounts['Claude Opus'] || 0} total={totalAgents} color="cyber-purple" />
              <ModelBar name="GLM" count={modelCounts['GLM'] || 0} total={totalAgents} color="cyber-blue" />
              <ModelBar name="Claude Haiku" count={modelCounts['Claude Haiku'] || 0} total={totalAgents} color="cyber-green" />
            </div>
          </div>

          <div className="cyber-panel p-6 hud-corner">
            <h3 className="text-lg font-mono mb-4 text-cyber-blue flex items-center">
              <Activity className="w-5 h-5 mr-2" />
              SYSTEM PERFORMANCE
            </h3>
            <div className="space-y-4">
              <PerformanceMetric name="Avg Response Time" value="1.2s" target="< 2s" status="optimal" />
              <PerformanceMetric name="Agent Uptime" value="99.8%" target="> 99%" status="optimal" />
              <PerformanceMetric name="Error Rate" value="0.02%" target="< 0.1%" status="optimal" />
              <PerformanceMetric name="Memory Usage" value="2.4GB" target="< 4GB" status="optimal" />
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

function StatCard({ title, value, subtitle, color }: any) {
  return (
    <div className="cyber-panel p-6 hud-corner">
      <div className={`text-3xl font-bold font-mono mb-1 text-${color} glow-text-green`}>{value}</div>
      <div className="text-sm text-cyber-white/70 mb-1">{title}</div>
      <div className="text-xs text-cyber-green/50">{subtitle}</div>
    </div>
  )
}

function ModelBar({ name, count, total, color }: any) {
  const percentage = (count / total) * 100
  const colorClasses: Record<string, string> = {
    'cyber-purple': 'bg-cyber-purple',
    'cyber-blue': 'bg-cyber-blue',
    'cyber-green': 'bg-cyber-green',
    'cyber-yellow': 'bg-cyber-yellow',
  }

  return (
    <div>
      <div className="flex justify-between text-xs mb-1">
        <span className="text-cyber-blue/80">{name}</span>
        <span className="text-cyber-blue/60">{count} agents ({percentage.toFixed(1)}%)</span>
      </div>
      <div className="h-2 bg-cyber-dark rounded-full overflow-hidden">
        <div className={`h-full ${colorClasses[color]} transition-all duration-1000`} style={{ width: `${percentage}%` }}></div>
      </div>
    </div>
  )
}

function PerformanceMetric({ name, value, target, status }: any) {
  const statusColor = status === 'optimal' ? 'text-cyber-green' : 'text-cyber-yellow'

  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center">
        <span className="w-2 h-2 bg-cyber-green rounded-full mr-3"></span>
        <span className="text-sm text-cyber-blue/80">{name}</span>
      </div>
      <div className="text-right">
        <div className={`text-sm font-mono ${statusColor}`}>{value}</div>
        <div className="text-xs text-cyber-blue/40">Target: {target}</div>
      </div>
    </div>
  )
}