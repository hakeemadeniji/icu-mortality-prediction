# ICU Mortality Prediction System - Full-Stack AI Application

## Overview
A production-ready full-stack AI application for ICU mortality prediction featuring 21 specialized AI agents, real-time analysis, and a Matrix-inspired black and green holographic interface with circular navigation layout.

## Current State
This project has been transformed from a research-focused multimodal deep learning study into a comprehensive production-ready application with:
- **Backend**: FastAPI server with AI agent orchestration
- **Frontend**: Next.js application with 3D holographic black & green interface
- **AI Agents**: 21 specialized agents powered by Anthropic Claude Opus/Haiku and GLM
- **Interface**: Circular clock-like layout with large, bold, readable text
- **Ports**: Frontend (3054), Backend (8054)

## Architecture

### Backend (FastAPI)
```
┌─────────────────────────────────────────────────────┐
│              FastAPI Backend Server               │
│              Port: 8054                           │
│                                                     │
│  ┌──────────────┐        ┌───────────────────┐      │
│  │  API Routes  │        │  AI Agent System  │      │
│  │              │        │   (21 Agents)    │      │
│  │  /prediction │        │                   │      │
│  │  /agents     │        │  - Data Ingestion  │      │
│  │  /data       │        │  - Clinical NLP   │      │
│  │  /monitoring │        │  - Model Ensemble  │      │
│  └──────┬───────┘        │  - Labs Analysis  │      │
│         │                 │  - Medication     │      │
│         └─────────────────┴  - Risk Assessment │      │
│                  │         │  - Explainability  │      │
│         ┌───────────────────────────────┐     │
│         │  Anthropic + GLM Integration  │     │
│         └───────────────────────────────┘     │
│                                                     │
│  ┌───────────────────────────────────────┐     │
│  │  RAG System + Vector Database        │     │
│  │  + ONNX Model Optimization          │     │
│  └───────────────────────────────────────┘     │
└─────────────────────────────────────────────┘
```

### Frontend (Next.js)
```
┌─────────────────────────────────────────────┐
│         Next.js Frontend Interface         │
│              Port: 3054                           │
│                                                     │
│  ┌───────────────────────────────────────┐     │
│  │  Header: System Status & Time        │     │
│  └───────────────────────────────────────┘     │
│                                                     │
│  ┌───────────────────────────────────────┐     │
│  │  Hero: "NEURAL INTERFACE" Title       │     │
│  └───────────────────────────────────────┘     │
│                                                     │
│  ┌───────────────────────────────────────┐     │
│  │      Circular Clock Layout           │     │
│  │  ┌─────┐                             │     │
│  │  │ CORE │  6 Sections in Circle       │     │
│  │  └─────┘  - Active Agents (21)        │     │
│  │           - Prediction Accuracy       │     │
│  │           - Data Sources (6)          │     │
│  │           - System Status           │     │
│  │           - Neural Interface         │     │
│  │           - Processing Power         │     │
│  └───────────────────────────────────────┘     │
│                                                     │
│  ┌───────────────────────────────────────┐     │
│  │      Navigation Buttons             │     │
│  │  [PREDICTION DASHBOARD] [AGENTS]      │     │
│  │  [SYSTEM ANALYTICS]                 │     │
│  └───────────────────────────────────────┘     │
│                                                     │
│  ┌───────────────────────────────────────┐     │
│  │  Footer: Copyright & Version         │     │
│  └───────────────────────────────────────┘     │
└─────────────────────────────────────────────┘
```

## Project Structure
```
icu-mortality-piration/
├── README.md (Updated)
├── CONTEXT.md (New)
├── STARTUP_GUIDE.md (Updated)
├── SYSTEM_README.md (Updated)
├── TRANSFORMATION_SUMMARY.md (Updated)
├── .vscode/
│   ├── settings.json
│   └── launch.json
├── backend/
│   ├── main.py
│   ├── core/
│   │   └── config.py (Updated)
│   ├── api/
│   │   ├── prediction.py
│   │   ├── agents.py
│   │   ├── data.py
│   │   ├── monitoring.py
│   │   └── evaluation.py
│   ├── agents/
│   │   ├── orchestration/
│   │   │   └── agent_service.py (Updated)
│   │   ├── specialized_agents/ (17 new agents)
│   │   │   ├── labs_analysis_agent.py
│   │   │   ├── medication_analysis_agent.py
│   │   │   ├── comorbidity_analysis_agent.py
│   │   │   ├── demographics_analysis_agent.py
│   │   │   ├── confidence_estimation_agent.py
│   │   │   ├── explainability_agent.py
│   │   │   ├── fairness_agent.py
│   │   │   ├── alert_generation_agent.py
│   │   │   ├── evaluation_monitoring_agent.py
│   │   │   ├── correction_trigger_agent.py
│   │   │   ├── knowledge_retrieval_agent.py
│   │   │   ├── clinical_guidelines_agent.py
│   │   │   ├── patient_context_agent.py
│   │   │   ├── data_quality_agent.py
│   │   │   ├── feature_engineering_agent.py
│   │   │   ├── time_series_analysis_agent.py
│   │   │   └── risk_assessment_agent.py
│   │   └── clinical_decision_support_agent.py
│   ├── .env (Updated with API keys)
│   ├── venv/
│   └── requirements.txt
├── frontend/
│   ├── pages/
│   │   ├── _app.tsx (Updated)
│   │   ├── index.tsx (Complete redesign)
│   │   ├── dashboard.tsx (Updated)
│   │   ├── agents.tsx (Updated)
│   │   └── analytics.tsx (Updated)
│   ├── styles/
│   │   └── globals.css (Complete redesign)
│   ├── package.json
│   ├── next.config.js (Updated)
│   └── .env.local
├── start_system.bat
├── startup_system.ps1
├── START_FRONTEND.bat
└── START_BACKEND_MANUAL.bat
```

## AI Agents (21 Total)

### Core ML Agents (4)
1. **Data Ingestion Agent** (GLM) - Efficient data loading
2. **Clinical NLP Agent** (Claude Opus) - Medical text processing
3. **Model Ensemble Agent** (Claude Opus) - Multi-model coordination
4. **Vitals Analysis Agent** (GLM) - Vital signs processing

### Clinical Analysis Agents (5)
5. **Labs Analysis Agent** (GLM) - Laboratory data analysis
6. **Medication Analysis Agent** (Claude Opus) - Drug interaction reasoning
7. **Comorbidity Analysis Agent** (Claude Opus) - Comorbidity impact assessment
8. **Demographics Analysis Agent** (Claude Haiku) - Demographic processing
9. **Patient Context Agent** (Claude Opus) - Patient information integration

### Monitoring & Evaluation Agents (4)
10. **Confidence Estimation Agent** (Claude Opus) - Uncertainty quantification
11. **Explainability Agent** (Claude Opus) - Prediction explanation generation
12. **Fairness Agent** (Claude Opus) - Bias analysis and mitigation
13. **Evaluation Monitoring Agent** (GLM) - Performance monitoring

### Decision Support Agents (4)
14. **Alert Generation Agent** (Claude Haiku) - Time-critical alerts
15. **Correction Trigger Agent** (Claude Opus) - Retraining decision making
16. **Clinical Guidelines Agent** (Claude Opus) - Guideline compliance
17. **Clinical Decision Support Agent** (Claude Opus) - Clinical reasoning

### Data Processing Agents (4)
18. **Data Quality Agent** (GLM) - Data validation
19. **Feature Engineering Agent** (Claude Opus) - Feature generation
20. **Time Series Analysis Agent** (GLM) - Temporal data analysis
21. **Risk Assessment Agent** (Claude Opus) - Comprehensive risk calculation

## Model Distribution
- **Claude Opus**: 13 agents (complex reasoning tasks)
- **GLM**: 5 agents (efficient numerical processing)
- **Claude Haiku**: 3 agents (fast, time-critical operations)

## Interface Design

### Visual Theme
- **Color Scheme**: Black background (#000000) with Matrix green (#00ff00) accents
- **Font**: Orbitron monospace for headings, bold weights
- **Style**: 3D holographic effects with glowing elements
- **Layout**: Circular clock-like arrangement for main sections

### Key Features
- **3D Holographic Background**: Animated grid with perspective
- **Floating Particles**: Green holographic particles
- **Circular Layout**: 6 sections arranged like clock positions
- **Large Bold Text**: Font sizes 2rem+ with 900 weight for readability
- **White Headings**: High contrast against black background
- **Green Values**: Glowing green text for emphasis
- **Button Navigation**: Large button-style elements side by side
- **3D Hover Effects**: Panels lift and rotate on hover
- **Scan Line Effects**: Subtle holographic scanning

### Pages
1. **Homepage** - Circular layout with system stats
2. **Dashboard** - Patient data input with prediction results
3. **Agents** - Live monitoring of all 21 AI agents
4. **Analytics** - System metrics and data source management

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Anthropic API Key
- GLM API Key

### Configuration
1. **Edit backend/.env** - Add your API keys:
```bash
ANTHROPIC_API_KEY=your_anthropic_key_here
GLM_API_KEY=your_glm_key_here
```

### Start the System

**Option 1: Automated (Windows)**
```bash
start_system.bat
```

**Option 2: Manual Startup**

**Backend (Terminal 1):**
```cmd
cd backend
venv\Scripts\activate
python main.py
```

**Frontend (Terminal 2):**
```cmd
cd frontend
npm run dev
```

### Access Points
- **Frontend Interface**: http://localhost:3054
- **Backend API**: http://localhost:8054
- **API Documentation**: http://localhost:8054/docs

## Ports Configuration
- **Frontend**: 3054
- **Backend**: 8054
- **API Proxy**: Frontend rewrites /api/* to backend

## Technology Stack

### Backend
- FastAPI (Web Framework)
- Python 3.11+
- Anthropic Claude API (Opus, Haiku)
- GLM API
- ONNX Runtime
- SQLAlchemy (Database)
- Vector Database (ChromaDB)

### Frontend
- Next.js 14 (React Framework)
- React 18+
- Framer Motion (Animations)
- Tailwind CSS (Styling)
- Lucide React (Icons)
- TypeScript

## Development

### VSCode Configuration
- python.terminal.useEnvFile: Enabled
- Auto-activation of Python virtual environments
- Auto-formatting on save

### Regular Maintenance
```powershell
# Weekly cleanup
Remove-Item -Path "$env:TEMP\*" -Recurse -Force

# Monthly cleanup
cleanmgr
npm cache clean --force
```

## Documentation
- **CONTEXT.md**: Detailed session context and changes
- **STARTUP_GUIDE.md**: Complete startup instructions
- **SYSTEM_README.md**: Technical architecture details
- **TRANSFORMATION_SUMMARY.md**: Project transformation history

## Contributors
- **[Hakeem Adeniji](https://github.com/hakeemadeniji)** — project owner & lead
- **Claude (Anthropic)** — AI pair programmer: interface rebuild, backend bring-up, and live Claude/GLM agent integration
- **Devin AI** — AI agent: initial full-stack scaffolding and interface iteration

## License
© 2026 ICU Mortality Prediction System. All rights reserved.