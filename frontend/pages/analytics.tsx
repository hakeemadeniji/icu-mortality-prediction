import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Database, Activity, TrendingUp, AlertTriangle, BarChart3, PieChart } from 'lucide-react'
import TopNav from '@/components/TopNav'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8054'

function fmtTime(t: string): string {
  if (!t) return ''
  const d = new Date(t)
  return isNaN(d.getTime()) ? t : d.toLocaleTimeString()
}

export default function AnalyticsPage() {
  const [activeTab, setActiveTab] = useState('overview')
  const [data, setData] = useState<any>(null)
  const [live, setLive] = useState(false)

  useEffect(() => {
    const controller = new AbortController()
    const load = () =>
      fetch(`${API_URL}/api/v1/monitoring/analytics-summary`, { signal: controller.signal })
        .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
        .then((d) => {
          setData(d)
          setLive(true)
        })
        .catch(() => {/* keep placeholder values — backend unavailable */})
    load()
    const timer = setInterval(load, 10000) // refresh live metrics
    return () => {
      controller.abort()
      clearInterval(timer)
    }
  }, [])

  return (
    <div className="min-h-screen relative">
      <TopNav
        title="SYSTEM ANALYTICS"
        status={live ? 'LIVE • BACKEND CONNECTED' : 'DEMO DATA • BACKEND OFFLINE'}
        active="/analytics"
      />

      <main className="container mx-auto px-6 py-8">
        {/* Tabs */}
        <div className="flex space-x-4 mb-8">
          {['overview', 'data_sources', 'performance', 'alerts'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-6 py-2 font-mono text-sm transition-all ${
                activeTab === tab
                  ? 'bg-cyber-blue/20 border-cyber-blue text-cyber-blue'
                  : 'border-cyber-blue/30 text-cyber-blue/60 hover:border-cyber-blue'
              } border`}
            >
              {tab.replace('_', ' ').toUpperCase()}
            </button>
          ))}
        </div>

        {activeTab === 'overview' && <OverviewTab data={data} />}
        {activeTab === 'data_sources' && <DataSourcesTab data={data} />}
        {activeTab === 'performance' && <PerformanceTab data={data} />}
        {activeTab === 'alerts' && <AlertsTab data={data} />}
      </main>
    </div>
  )
}

function OverviewTab({ data }: any) {
  const m = data?.metrics
  const rd = data?.risk_distribution
  return (
    <div className="space-y-8">
      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <MetricCard
          title="TOTAL PREDICTIONS"
          value={m ? m.total_predictions.toLocaleString() : '—'}
          change="session"
          icon={<Activity className="w-6 h-6" />}
          color="cyber-blue"
        />
        <MetricCard
          title="ACCURACY RATE"
          value={m ? `${(m.accuracy_rate * 100).toFixed(1)}%` : '94.7%'}
          change="AUROC"
          icon={<TrendingUp className="w-6 h-6" />}
          color="cyber-green"
        />
        <MetricCard
          title="ACTIVE DATA SOURCES"
          value={m ? String(m.active_data_sources) : '6'}
          change="live"
          icon={<Database className="w-6 h-6" />}
          color="cyber-purple"
        />
        <MetricCard
          title="SYSTEM ALERTS"
          value={m ? String(m.active_alerts) : '0'}
          change="active"
          icon={<AlertTriangle className="w-6 h-6" />}
          color="cyber-yellow"
        />
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="cyber-panel p-6 hud-corner">
          <h3 className="text-lg font-mono mb-4 text-cyber-blue flex items-center">
            <BarChart3 className="w-5 h-5 mr-2" />
            PREDICTION VOLUME
          </h3>
          <div className="h-64 flex items-end justify-between space-x-2">
            {[65, 45, 78, 52, 83, 61, 91, 74, 56, 82, 69, 88].map((height, index) => (
              <motion.div
                key={index}
                initial={{ height: 0 }}
                animate={{ height: `${height}%` }}
                transition={{ delay: index * 0.1 }}
                className="flex-1 bg-gradient-to-t from-cyber-blue/20 to-cyber-blue/60 rounded-t"
              />
            ))}
          </div>
          <div className="flex justify-between mt-2 text-xs text-cyber-blue/40">
            <span>JAN</span><span>FEB</span><span>MAR</span><span>APR</span><span>MAY</span><span>JUN</span>
            <span>JUL</span><span>AUG</span><span>SEP</span><span>OCT</span><span>NOV</span><span>DEC</span>
          </div>
        </div>

        <div className="cyber-panel p-6 hud-corner">
          <h3 className="text-lg font-mono mb-4 text-cyber-blue flex items-center">
            <PieChart className="w-5 h-5 mr-2" />
            RISK DISTRIBUTION
          </h3>
          <div className="h-64 flex items-center justify-center">
            <div className="relative w-48 h-48">
              <svg viewBox="0 0 100 100" className="transform -rotate-90">
                <circle cx="50" cy="50" r="40" fill="none" stroke="#1a1a2e" strokeWidth="20" />
                <circle cx="50" cy="50" r="40" fill="none" stroke="#00f0ff" strokeWidth="20"
                  strokeDasharray="100 151" strokeLinecap="round" />
                <circle cx="50" cy="50" r="40" fill="none" stroke="#00ff9f" strokeWidth="20"
                  strokeDasharray="60 191" strokeDashoffset="-100" strokeLinecap="round" />
                <circle cx="50" cy="50" r="40" fill="none" stroke="#ff2a6d" strokeWidth="20"
                  strokeDasharray="40 211" strokeDashoffset="-160" strokeLinecap="round" />
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="text-center">
                  <div className="text-2xl font-bold font-mono text-cyber-blue">
                    {m ? m.total_predictions.toLocaleString() : '24.5K'}
                  </div>
                  <div className="text-xs text-cyber-blue/60">TOTAL</div>
                </div>
              </div>
            </div>
          </div>
          <div className="flex justify-center space-x-6 mt-4">
            <LegendItem color="cyber-blue" label="Low Risk" value={rd ? `${rd.low}%` : '40%'} />
            <LegendItem color="cyber-green" label="Moderate" value={rd ? `${rd.moderate}%` : '24%'} />
            <LegendItem color="cyber-red" label="High/Crit" value={rd ? `${(rd.high + rd.critical).toFixed(1)}%` : '16%'} />
          </div>
        </div>
      </div>
    </div>
  )
}

function DataSourcesTab({ data }: any) {
  const dataSources = data?.data_sources?.length
    ? data.data_sources
    : [
        { name: 'PhysioNet Challenge 2012', status: 'connected', records: '45,234', lastUpdate: '2 min ago' },
        { name: 'SICdb', status: 'connected', records: '27,891', lastUpdate: '5 min ago' },
        { name: 'HiRID', status: 'connected', records: '34,567', lastUpdate: '1 min ago' },
        { name: 'NWICU Database', status: 'connected', records: '12,345', lastUpdate: '10 min ago' },
        { name: 'WHO Mortality Database', status: 'connected', records: '156,789', lastUpdate: '1 hour ago' },
        { name: 'CDC Mortality Data', status: 'connected', records: '89,012', lastUpdate: '30 min ago' },
      ]

  return (
    <div className="cyber-panel p-6 hud-corner">
      <h3 className="text-xl font-mono mb-6 glow-text flex items-center">
        <Database className="w-6 h-6 mr-3" />
        DATA SOURCE MANAGEMENT
      </h3>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-cyber-blue/30">
              <th className="text-left text-sm font-mono text-cyber-blue/60 py-3 px-4">SOURCE</th>
              <th className="text-left text-sm font-mono text-cyber-blue/60 py-3 px-4">STATUS</th>
              <th className="text-left text-sm font-mono text-cyber-blue/60 py-3 px-4">RECORDS</th>
              <th className="text-left text-sm font-mono text-cyber-blue/60 py-3 px-4">LAST UPDATE</th>
              <th className="text-left text-sm font-mono text-cyber-blue/60 py-3 px-4">ACTIONS</th>
            </tr>
          </thead>
          <tbody>
            {dataSources.map((source: any, index: number) => (
              <tr key={index} className="border-b border-cyber-blue/10 hover:bg-cyber-blue/5">
                <td className="py-3 px-4 text-cyber-blue">{source.name}</td>
                <td className="py-3 px-4">
                  <span className={`flex items-center ${source.status === 'connected' ? 'text-cyber-green' : 'text-cyber-blue/40'}`}>
                    <span className={`w-2 h-2 rounded-full mr-2 ${source.status === 'connected' ? 'bg-cyber-green' : 'bg-cyber-blue/40'}`}></span>
                    {source.status}
                  </span>
                </td>
                <td className="py-3 px-4 text-cyber-blue/80 font-mono">{source.records}</td>
                <td className="py-3 px-4 text-cyber-blue/60">{source.lastUpdate}</td>
                <td className="py-3 px-4">
                  <button className="text-xs cyber-button px-3 py-1">MANAGE</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function PerformanceTab({ data }: any) {
  const cards = data?.performance?.length
    ? data.performance
    : [
        { title: 'API Response Time', value: '45ms', target: '< 100ms', status: 'optimal', history: [65, 58, 52, 48, 45, 47, 45] },
        { title: 'Memory Usage', value: '2.4GB / 8GB', target: '< 6GB', status: 'optimal', history: [2.1, 2.2, 2.3, 2.4, 2.3, 2.4, 2.4] },
        { title: 'CPU Utilization', value: '34%', target: '< 70%', status: 'optimal', history: [45, 42, 38, 35, 34, 36, 34] },
        { title: 'Disk I/O', value: '125 MB/s', target: '< 200 MB/s', status: 'optimal', history: [180, 165, 150, 140, 130, 125, 128] },
      ]
  return (
    <div className="cyber-panel p-6 hud-corner">
      <h3 className="text-xl font-mono mb-6 glow-text flex items-center">
        <Activity className="w-6 h-6 mr-3" />
        SYSTEM PERFORMANCE METRICS
      </h3>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {cards.map((c: any, i: number) => (
          <PerformanceCard
            key={i}
            title={c.title}
            value={c.value}
            target={c.target}
            status={c.status}
            history={c.history && c.history.length ? c.history : [0]}
          />
        ))}
      </div>
    </div>
  )
}

function AlertsTab({ data }: any) {
  const alerts = data?.alerts
    ? data.alerts
    : [
        { id: 1, severity: 'warning', message: 'Data drift detected in PhysioNet source', time: '10 min ago', status: 'investigating' },
        { id: 2, severity: 'info', message: 'Scheduled maintenance completed successfully', time: '1 hour ago', status: 'resolved' },
        { id: 3, severity: 'warning', message: 'High memory usage on Agent #7', time: '2 hours ago', status: 'resolved' },
      ]

  if (alerts.length === 0) {
    return (
      <div className="cyber-panel p-6 hud-corner">
        <h3 className="text-xl font-mono mb-6 glow-text flex items-center">
          <AlertTriangle className="w-6 h-6 mr-3" />
          SYSTEM ALERTS
        </h3>
        <div className="text-cyber-green/70 font-mono text-sm">No active alerts — all systems nominal.</div>
      </div>
    )
  }

  return (
    <div className="cyber-panel p-6 hud-corner">
      <h3 className="text-xl font-mono mb-6 glow-text flex items-center">
        <AlertTriangle className="w-6 h-6 mr-3" />
        SYSTEM ALERTS
      </h3>

      <div className="space-y-4">
        {alerts.map((alert: any) => (
          <div key={alert.id} className="cyber-panel p-4 flex items-start justify-between">
            <div className="flex items-start">
              <span className={`w-3 h-3 rounded-full mt-1 mr-3 ${
                alert.severity === 'warning' ? 'bg-cyber-yellow' : 'bg-cyber-blue'
              }`}></span>
              <div>
                <div className="text-cyber-blue">{alert.message}</div>
                <div className="text-xs text-cyber-blue/40 mt-1">{fmtTime(alert.time)}</div>
              </div>
            </div>
            <span className={`text-xs px-2 py-1 ${
              alert.status === 'resolved' ? 'bg-cyber-green/20 text-cyber-green' : 'bg-cyber-yellow/20 text-cyber-yellow'
            }`}>
              {alert.status.toUpperCase()}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

function MetricCard({ title, value, change, icon, color }: any) {
  return (
    <div className="cyber-panel p-6 hud-corner">
      <div className="flex items-start justify-between mb-4">
        <div className={`text-${color}`}>{icon}</div>
        <span className={`text-xs ${change.startsWith('+') ? 'text-cyber-green' : 'text-cyber-red'}`}>
          {change}
        </span>
      </div>
      <div className="text-3xl font-bold font-mono text-cyber-blue mb-1">{value}</div>
      <div className="text-sm text-cyber-blue/60">{title}</div>
    </div>
  )
}

function LegendItem({ color, label, value }: any) {
  return (
    <div className="flex items-center">
      <span className={`w-3 h-3 rounded-full bg-${color} mr-2`}></span>
      <span className="text-xs text-cyber-blue/60">{label}: {value}</span>
    </div>
  )
}

function PerformanceCard({ title, value, target, status, history }: any) {
  return (
    <div className="cyber-panel p-4">
      <div className="flex justify-between items-start mb-4">
        <h4 className="font-mono text-cyber-blue">{title}</h4>
        <span className={`text-xs px-2 py-1 ${
          status === 'optimal' ? 'bg-cyber-green/20 text-cyber-green' : 'bg-cyber-yellow/20 text-cyber-yellow'
        }`}>
          {status.toUpperCase()}
        </span>
      </div>
      <div className="text-2xl font-bold font-mono text-cyber-blue mb-2">{value}</div>
      <div className="text-xs text-cyber-blue/40 mb-4">Target: {target}</div>
      <div className="h-16 flex items-end space-x-1">
        {history.map((h: number, i: number) => (
          <div key={i} className="flex-1 bg-cyber-blue/30" style={{ height: `${(h / Math.max(...history)) * 100}%` }}></div>
        ))}
      </div>
    </div>
  )
}