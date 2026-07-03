/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Single source of truth — kept in sync with the CSS variables in
        // styles/globals.css. Black + matrix-green primary with a small,
        // purposeful set of semantic accents used across the sub-pages.
        cyber: {
          black: '#000000',
          dark: '#0a0f0c',
          green: '#2bff88',
          'green-dark': '#12b866',
          'green-light': '#7dffb0',
          white: '#eafff2',
          blue: '#38bdf8', // info / secondary accent
          purple: '#a78bfa', // tertiary accent
          yellow: '#fbbf24', // warning
          red: '#fb7185', // danger
          pink: '#fb7185',
        },
      },
      fontFamily: {
        mono: ['"Orbitron"', 'monospace'],
        sans: ['"Rajdhani"', 'sans-serif'],
      },
      animation: {
        'pulse-glow': 'pulse-glow 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'scan-line': 'scan-line 8s linear infinite',
        'flicker': 'flicker 0.15s infinite',
        'data-stream': 'data-stream 20s linear infinite',
      },
      keyframes: {
        'pulse-glow': {
          '0%, 100%': { opacity: 1, boxShadow: '0 0 20px #2bff88' },
          '50%': { opacity: 0.7, boxShadow: '0 0 10px #2bff88' },
        },
        'scan-line': {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100vh)' },
        },
        'flicker': {
          '0%, 100%': { opacity: 1 },
          '50%': { opacity: 0.8 },
        },
        'data-stream': {
          '0%': { backgroundPosition: '0% 0%' },
          '100%': { backgroundPosition: '0% 100%' },
        },
      },
    },
  },
  // Some components build color classes dynamically (e.g. `bg-${color}`),
  // which Tailwind's static scanner cannot see. Safelist them so they render.
  safelist: [
    'text-cyber-blue', 'text-cyber-green', 'text-cyber-green-light',
    'text-cyber-purple', 'text-cyber-yellow', 'text-cyber-red', 'text-cyber-white',
    'bg-cyber-blue', 'bg-cyber-green', 'bg-cyber-green-light',
    'bg-cyber-purple', 'bg-cyber-yellow', 'bg-cyber-red',
    'border-cyber-blue', 'border-cyber-green', 'border-cyber-purple',
  ],
  plugins: [],
}
