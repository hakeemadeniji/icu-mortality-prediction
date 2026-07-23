import { Brain } from 'lucide-react'

const links = [
  { href: '/', label: 'HOME' },
  { href: '/dashboard', label: 'DASHBOARD' },
  { href: '/risk', label: 'RISK' },
  { href: '/agents', label: 'AGENTS' },
  { href: '/analytics', label: 'ANALYTICS' },
]

interface TopNavProps {
  /** Page title shown next to the logo */
  title: string
  /** Short status text shown on the right (e.g. "NEURAL LINK: ACTIVE") */
  status?: string
  /** href of the current page so it can be highlighted */
  active?: string
}

export default function TopNav({ title, status, active }: TopNavProps) {
  return (
    <header className="sticky top-0 z-20 border-b border-cyber-green/25 bg-cyber-black/85 backdrop-blur-md">
      <div className="container mx-auto px-6 py-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          {/* Left: logo + title */}
          <div className="flex items-center gap-3">
            <a
              href="/"
              className="w-9 h-9 rounded-full border border-cyber-green flex items-center justify-center text-cyber-green shrink-0 hover:bg-cyber-green/10 transition-colors"
              aria-label="Back to home"
            >
              <Brain className="w-5 h-5" />
            </a>
            <h1 className="text-lg md:text-xl font-bold font-mono glow-text tracking-wider text-cyber-white">
              {title}
            </h1>
          </div>

          {/* Center: page nav */}
          <nav className="flex items-center gap-1 order-last w-full md:order-none md:w-auto">
            {links.map((link) => {
              const isActive = active === link.href
              return (
                <a
                  key={link.href}
                  href={link.href}
                  className={`px-3 py-1.5 rounded-md text-xs font-semibold font-mono tracking-widest transition-colors ${
                    isActive
                      ? 'bg-cyber-green/15 text-cyber-green border border-cyber-green/40'
                      : 'text-cyber-green/60 hover:text-cyber-green hover:bg-cyber-green/5 border border-transparent'
                  }`}
                >
                  {link.label}
                </a>
              )
            })}
          </nav>

          {/* Right: status */}
          {status && (
            <div className="flex items-center gap-2 text-xs">
              <span className="text-cyber-green/70 font-semibold tracking-wide hidden sm:inline">
                {status}
              </span>
              <span className="w-2.5 h-2.5 rounded-full bg-cyber-green animate-pulse" />
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
