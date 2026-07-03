import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Activity, Cpu, Database, Shield, Zap, Brain } from 'lucide-react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8054'

export default function Home() {
  const [currentTime, setCurrentTime] = useState<Date | null>(null)
  const [mounted, setMounted] = useState(false)
  const [accuracy, setAccuracy] = useState<string | null>(null)
  const [accuracyModel, setAccuracyModel] = useState<string | null>(null)
  const [activeAgents, setActiveAgents] = useState<string | null>(null)
  const [dataSources, setDataSources] = useState<string | null>(null)

  useEffect(() => {
    setMounted(true)
    setCurrentTime(new Date())
    const timer = setInterval(() => setCurrentTime(new Date()), 1000)

    // Pull live values from the backend (each stat falls back to '—' if offline).
    const controller = new AbortController()
    const opts = { signal: controller.signal }

    // Real accuracy (computed AUROC) + connected data sources
    fetch(`${API_URL}/api/v1/monitoring/analytics-summary`, opts)
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then((d) => {
        const m = d.metrics || {}
        if (typeof m.accuracy_rate === 'number') setAccuracy(`${(m.accuracy_rate * 100).toFixed(1)}%`)
        if (m.accuracy_model) setAccuracyModel(m.accuracy_model)
        if (typeof m.active_data_sources === 'number') setDataSources(String(m.active_data_sources))
      })
      .catch(() => {/* backend offline — leave placeholders */})

    // Live active-agent count
    fetch(`${API_URL}/api/v1/agents/orchestration/status`, opts)
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then((d) => {
        if (typeof d.active_agents === 'number') setActiveAgents(String(d.active_agents))
      })
      .catch(() => {/* backend offline — leave placeholder */})

    return () => {
      clearInterval(timer)
      controller.abort()
    }
  }, [])

  // A handful of faint drifting particles (kept low for performance + calm UI)
  const particles = Array.from({ length: 12 }, (_, i) => ({
    id: i,
    style: {
      left: `${Math.random() * 100}%`,
      animationDelay: `${Math.random() * 22}s`,
      animationDuration: `${18 + Math.random() * 10}s`,
    },
  }))

  const stats = [
    { icon: Cpu, title: 'ACTIVE AGENTS', value: activeAgents ?? '—', subtitle: 'AI systems online' },
    { icon: Activity, title: 'PREDICTION ACCURACY', value: accuracy ?? '—', subtitle: accuracyModel ? `${accuracyModel} AUROC` : 'Validation AUROC' },
    { icon: Database, title: 'DATA SOURCES', value: dataSources ?? '—', subtitle: 'Integrated streams' },
    { icon: Shield, title: 'SYSTEM STATUS', value: 'OPTIMAL', subtitle: 'All systems nominal' },
    { icon: Zap, title: 'NEURAL INTERFACE', value: 'ACTIVE', subtitle: 'Ready for input' },
    { icon: Brain, title: 'PROCESSING', value: 'REAL-TIME', subtitle: 'Low-latency inference' },
  ]

  const navItems = [
    {
      title: 'PREDICTION DASHBOARD',
      description: 'Real-time mortality risk assessment with AI-powered analysis.',
      icon: Zap,
      href: '/dashboard',
    },
    {
      title: 'AGENT MONITORING',
      description: 'Live status and performance metrics for all 21 AI agents.',
      icon: Brain,
      href: '/agents',
    },
    {
      title: 'SYSTEM ANALYTICS',
      description: 'System monitoring, data sources and evaluation metrics.',
      icon: Activity,
      href: '/analytics',
    },
  ]

  return (
    <div className="min-h-screen relative flex flex-col">
      {/* Ambient effects */}
      <div className="holo-particles">
        {particles.map((p) => (
          <div key={p.id} className="holo-particle" style={p.style} />
        ))}
      </div>
      <div className="scan-line" />

      {/* Header */}
      <header className="relative z-10 border-b border-cyber-green/25 bg-cyber-black/85 backdrop-blur-md">
        <div className="container mx-auto px-6 py-5">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center space-x-4">
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 24, repeat: Infinity, ease: 'linear' }}
                className="w-12 h-12 border border-cyber-green rounded-full flex items-center justify-center shrink-0"
              >
                <Brain className="w-6 h-6 text-cyber-green" />
              </motion.div>
              <div>
                <h1 className="text-xl md:text-2xl font-bold font-mono glow-text tracking-wider text-cyber-white">
                  ICU PREDICTION SYSTEM
                </h1>
                <p className="text-xs md:text-sm text-cyber-green/80 tracking-[0.2em] font-semibold">
                  ADVANCED AI INTERFACE v2.0.0
                </p>
              </div>
            </div>

            <div className="flex items-center gap-8">
              <div className="text-right">
                <div className="text-[11px] text-cyber-green/70 font-semibold tracking-widest">STATUS</div>
                <div className="text-sm font-bold font-mono text-cyber-green flex items-center justify-end gap-2">
                  <span className="w-2 h-2 rounded-full bg-cyber-green animate-pulse" />
                  ONLINE
                </div>
              </div>
              <div className="text-right">
                <div className="text-[11px] text-cyber-green/70 font-semibold tracking-widest">LOCAL TIME</div>
                <div className="text-sm font-bold font-mono text-cyber-white tabular-nums">
                  {mounted ? currentTime?.toLocaleTimeString() : '--:--:--'}
                </div>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main */}
      <main className="relative z-10 container mx-auto px-6 py-14 flex-1">
        {/* Hero */}
        <motion.section
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="text-center max-w-3xl mx-auto mb-16"
        >
          <div className="inline-flex items-center gap-2 px-4 py-1.5 mb-6 rounded-full border border-cyber-green/40 text-cyber-green text-xs font-semibold tracking-widest">
            <span className="w-2 h-2 rounded-full bg-cyber-green animate-pulse" />
            SYSTEM CORE ONLINE
          </div>
          <h2 className="text-4xl md:text-6xl font-black font-mono mb-5 glow-text text-cyber-white">
            NEURAL INTERFACE
          </h2>
          <p className="text-base md:text-lg text-cyber-green/80 leading-relaxed">
            AI-powered ICU mortality prediction featuring 21 specialized agents,
            real-time analysis, and multimodal clinical intelligence.
          </p>
        </motion.section>

        {/* Stat grid — clean, evenly spaced, no overlap */}
        <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 mb-16">
          {stats.map((stat, i) => {
            const Icon = stat.icon
            return (
              <motion.div
                key={stat.title}
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, delay: i * 0.06 }}
                className="holo-card hud-corner p-6"
              >
                <div className="flex items-center justify-between mb-4">
                  <div className="w-11 h-11 rounded-lg border border-cyber-green/30 flex items-center justify-center text-cyber-green">
                    <Icon className="w-6 h-6" />
                  </div>
                </div>
                <div className="text-3xl font-black font-mono text-cyber-green glow-text-green mb-1">
                  {stat.value}
                </div>
                <div className="text-sm font-bold text-cyber-white tracking-wide">{stat.title}</div>
                <div className="text-xs text-cyber-green/60 uppercase tracking-widest mt-1">
                  {stat.subtitle}
                </div>
              </motion.div>
            )
          })}
        </section>

        {/* Navigation */}
        <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {navItems.map((item, i) => {
            const Icon = item.icon
            return (
              <motion.a
                key={item.href}
                href={item.href}
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, delay: 0.2 + i * 0.1 }}
                className="cyber-button hud-corner flex flex-col items-center text-center p-8 no-underline"
              >
                <div className="w-14 h-14 rounded-xl border border-cyber-green/40 flex items-center justify-center mb-4 text-cyber-green">
                  <Icon className="w-7 h-7" />
                </div>
                <h3 className="text-lg font-bold font-mono mb-2 text-cyber-white tracking-wide">
                  {item.title}
                </h3>
                <p className="text-sm text-cyber-green/70 font-medium normal-case tracking-normal leading-relaxed">
                  {item.description}
                </p>
                <span className="mt-4 text-xs font-bold font-mono text-cyber-green-light tracking-widest">
                  ACCESS →
                </span>
              </motion.a>
            )
          })}
        </section>
      </main>

      {/* Footer */}
      <footer className="relative z-10 border-t border-cyber-green/25 bg-cyber-black/85 backdrop-blur-md">
        <div className="container mx-auto px-6 py-6">
          <div className="flex flex-wrap items-center justify-between gap-3 text-xs">
            <div className="text-cyber-green/70 font-semibold tracking-wide">
              © 2026 ICU MORTALITY PREDICTION SYSTEM
            </div>
            <div className="flex items-center gap-3 text-cyber-green/60 font-mono">
              <span>v2.0.0</span>
              <span className="w-2 h-2 rounded-full bg-cyber-green animate-pulse" />
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
