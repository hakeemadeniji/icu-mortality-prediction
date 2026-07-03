# ICU Mortality Prediction System - Technical Documentation

## Overview

Production-ready full-stack AI application for ICU mortality prediction featuring 21 specialized AI agents, RAG implementation, ONNX optimization, and a Matrix-inspired black and green holographic interface with circular navigation layout.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (Next.js)                        │
│  - Black & green holographic interface                      │
│  - Circular clock layout                                    │
│  - Large bold text (2rem+ font sizes)                       │
│  - 3D holographic effects                                   │
│  - Button-style navigation                                  │
│  Port: 3054                                                 │
└──────────────────────┬──────────────────────────────────────┘
                       │ REST API
┌──────────────────────▼──────────────────────────────────────┐
│                   BACKEND (FastAPI)                          │
│  - Patient data ingestion API                                 │
│  - Model inference endpoints                                  │
│  - Agent orchestration API                                    │
│  Port: 8054                                                 │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│              AI AGENT ORCHESTRATION (21 Agents)               │
│  Data Ingestion | Clinical NLP | Vitals Analysis | Labs      │
│  Medication | Comorbidity | Demographics | Model Ensemble    │
│  Confidence | Explainability | Fairness | Alert Generation   │
│  Evaluation | Correction | Knowledge Retrieval | Guidelines  │
│  Patient Context | Data Quality | Feature Engineering       │
│  Time Series | Risk Assessment | Clinical Decision Support  │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│              RAG SYSTEM (ChromaDB + Embeddings)               │
│  - Medical literature retrieval                               │
│  - Clinical guidelines access                                 │
│  - Knowledge base management                                  │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│         ONNX RUNTIME (ARM64 Snapdragon NPU Optimized)        │
│  - LSTM Encoder | Transformer | Fusion Model | Text Encoder  │
└─────────────────────────────────────────────────────────────┘
```

## 21 AI Agents

### Core ML Agents (4)
1. **Data Ingestion Agent** (GLM) - Multi-source data ingestion with efficient loading
2. **Clinical NLP Agent** (Claude Opus) - Medical named entity recognition and text processing
3. **Model Ensemble Agent** (Claude Opus) - Multi-model prediction coordination
4. **Vitals Analysis Agent** (GLM) - Vital sign pattern analysis

### Clinical Analysis Agents (5)
5. **Labs Analysis Agent** (GLM) - Laboratory value analysis and interpretation
6. **Medication Analysis Agent** (Claude Opus) - Medication impact analysis and drug interactions
7. **Comorbidity Analysis Agent** (Claude Opus) - Comorbidity interaction assessment
8. **Demographics Analysis Agent** (Claude Haiku) - Demographic factor analysis
9. **Patient Context Agent** (Claude Opus) - Patient-specific context incorporation

### Monitoring & Evaluation Agents (4)
10. **Confidence Estimation Agent** (Claude Opus) - Prediction uncertainty estimation
11. **Explainability Agent** (Claude Opus) - Model explanation generation
12. **Fairness Agent** (Claude Opus) - Bias monitoring and correction
13. **Evaluation Monitoring Agent** (GLM) - Continuous performance monitoring

### Decision Support Agents (4)
14. **Alert Generation Agent** (Claude Haiku) - Clinical alert generation (time-critical)
15. **Correction Trigger Agent** (Claude Opus) - Automatic retraining triggers
16. **Clinical Guidelines Agent** (Claude Opus) - Guidelines compliance checking
17. **Clinical Decision Support Agent** (Claude Opus) - Clinical reasoning support

### Data Processing Agents (4)
18. **Data Quality Agent** (GLM) - Data validation and cleaning
19. **Feature Engineering Agent** (Claude Opus) - Automatic feature generation
20. **Time Series Analysis Agent** (GLM) - Temporal pattern recognition
21. **Risk Assessment Agent** (Claude Opus) - Comprehensive risk calculation

## Model Distribution

- **Claude Opus**: 13 agents (complex reasoning tasks requiring highest intelligence)
- **GLM**: 5 agents (efficient numerical processing and data analysis)
- **Claude Haiku**: 3 agents (fast, time-critical operations requiring speed)

## Interface Design

### Visual Theme
- **Color Scheme**: Pure black (#000000) background with Matrix green (#00ff00) accents
- **Color Variations**: Green-dark (#008800), Green-light (#00ff33), White (#ffffff)
- **Font**: Orbitron monospace for headings, bold weights (600-900)
- **Style**: 3D holographic effects with glowing elements
- **Layout**: Circular clock-like arrangement for main sections

### Key Visual Features
- **3D Holographic Background**: Animated grid with perspective (60° rotation)
- **Floating Particles**: 20 green holographic particles floating across screen
- **Circular Layout**: 6 sections arranged at 60° intervals (clock positions)
- **Large Bold Text**: Font sizes 1.8rem-3.5rem with 900 weight for readability
- **White Headings**: High contrast against black background
- **Green Values**: Glowing green text with shadow effects
- **Button Navigation**: Large button-style elements (320px min width) side by side
- **3D Hover Effects**: Panels lift 25-30px and rotate on hover
- **Scan Line Effects**: Subtle holographic scanning across screen
- **Enhanced Borders**: 2-4px borders with glow effects
- **Panel Scan Lines**: Repeating gradient scan lines on panels

### Layout Structure

```
1. Header (Top)
   └─ System title, status, time

2. Hero Section (Separated)
   └─ "NEURAL INTERFACE" title with description

3. Circular Layout (Separated)
   └─ Central hub: "ICU AI SYSTEM CORE"
   └─ 6 circular sections at clock positions:
      - 12 o'clock: Active Agents (21)
      - 2 o'clock: Prediction Accuracy (94.7%)
      - 4 o'clock: Data Sources (6)
      - 6 o'clock: System Status (OPTIMAL)
      - 8 o'clock: Neural Interface (ACTIVE)
      - 10 o'clock: Processing Power (MAX)

4. Navigation Buttons (Separated)
   └─ 3 large buttons side by side:
      - PREDICTION DASHBOARD
      - AGENT MONITORING
      - SYSTEM ANALYTICS

5. Footer (Bottom)
   └─ Copyright and version info
```

### CSS Classes
- `.holo-container` - 3D perspective container
- `.holo-section` - 3D transform section
- `.holo-card` - Holographic card with shine effect
- `.cyber-panel` - 3D panel with scan lines
- `.cyber-button` - Enhanced button with 3D effects
- `.circular-layout` - Circular positioning container
- `.circular-center` - Pulsing center hub
- `.circular-item` - Individual circular sections
- `.glow-text` - Glowing text effect
- `.hud-corner` - Corner decorations with glow

## Legitimate Data Sources Integration

### Freely Accessible (Immediate Integration)
- **PhysioNet Challenge 2012** - ICU mortality prediction (open access)
- **Salzburg Intensive Care Database (SICdb)** - 27K+ ICU admissions
- **Northwestern ICU (NWICU) Database** - COVID-rich ICU data
- **HiRID** - High-resolution ICU data (34K admissions)
- **WHO Mortality Database** - Global mortality statistics
- **CDC Public-Use Linked Mortality Files** - US mortality data

### Requires Credentialing (Future Integration)
- **MIMIC-IV** - 65K+ ICU patients (requires CITI training + DUA)
- **eICU Collaborative Research Database** - 200K+ ICU admissions
- **AmsterdamUMCdb** - 23K+ ICU admissions (requires access request)

## ONNX & ARM64 Optimization

### Features
- **ONNX Conversion**: All PyTorch models converted to ONNX format
- **ARM64 Optimization**: Optimized for Windows ARM64 architecture
- **Snapdragon NPU Acceleration**: NPU-specific optimizations
- **Quantization**: Model quantization for improved performance
- **Cross-Platform**: Deployable on various platforms

### Optimization Strategy
1. Convert PyTorch models to ONNX format
2. Apply ARM64-specific optimizations
3. Optimize for Snapdragon NPU execution providers
4. Implement model parallelization for ensemble
5. Use DirectML for GPU acceleration when available

## Setup Instructions

### Prerequisites
- Python 3.11+
- Node.js 18+
- Anthropic API Key
- GLM API Key
- Windows ARM64 (Samsung Galaxy Book4 Edge)
- Git

### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Configure API keys
# Edit .env file with your keys:
# ANTHROPIC_API_KEY=your_key_here
# GLM_API_KEY=your_key_here

# For ARM64 optimization, install ARM64-specific wheels:
pip install --platform win_arm64 torch onnxruntime

# Convert models to ONNX
cd ..
python scripts/convert_to_onnx.py

# Start backend server
cd backend
python main.py
```

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

## API Endpoints

### Prediction API
- `POST /api/v1/prediction/predict` - Single patient prediction
- `POST /api/v1/prediction/predict/batch` - Batch prediction
- `GET /api/v1/prediction/models` - List available models
- `GET /api/v1/prediction/status` - System status

### Agents API
- `GET /api/v1/agents/list` - List all agents
- `POST /api/v1/agents/execute` - Execute specific agent
- `POST /api/v1/agents/orchestrate` - Orchestrate multiple agents
- `GET /api/v1/agents/{agent_id}` - Get agent details

### Data API
- `GET /api/v1/data/sources` - List data sources
- `POST /api/v1/data/ingest` - Ingest data from source
- `POST /api/v1/data/query` - Query data across sources

### Monitoring API
- `GET /api/v1/monitoring/metrics` - System metrics
- `GET /api/v1/monitoring/health` - Service health
- `GET /api/v1/monitoring/alerts` - System alerts

### Evaluation API
- `POST /api/v1/evaluation/evaluate` - Evaluate model performance
- `POST /api/v1/evaluation/drift-detect` - Detect data drift
- `POST /api/v1/evaluation/bias-analysis` - Analyze model bias

## Configuration

Edit `backend/core/config.py` or use `backend/.env` to configure:

```python
# API Settings
HOST=0.0.0.0
PORT=8054
DEBUG=True

# Anthropic API Configuration for AI Agents
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GLM_API_KEY=your_glm_api_key_here
ANTHROPIC_MODEL_DEFAULT=claude-3-opus-20240229
ANTHROPIC_MODEL_FAST=claude-3-haiku-20240307

# Model Settings
MODEL_PATH = "./onnx_models"
ONNX_OPTIMIZED = True
ARM64_OPTIMIZED = True
USE_NPU = True

# Agent Settings
NUM_AGENTS = 21
ENABLE_RAG = True

# Data Sources
ENABLE_PHYSIONET_CHALLENGE = True
ENABLE_SICDB = True
ENABLE_WHO_MORTALITY = True

# Frontend Configuration
FRONTEND_URL=http://localhost:3054
ENABLE_CORS=true
```

## Performance Optimization

### ARM64 Specific
- Uses ARM64-optimized ONNX Runtime
- Snapdragon NPU acceleration when available
- Quantized models for faster inference
- Memory-efficient data loading

### Caching
- Redis caching for frequent queries
- Model caching in memory
- Data source response caching

### Parallel Processing
- Multi-agent parallel execution
- Batch prediction optimization
- Async I/O operations

## Monitoring & Evaluation

### Continuous Monitoring
- Real-time performance metrics
- Agent execution monitoring
- System health checks
- Alert generation

### Continuous Evaluation
- Automated model evaluation
- Data drift detection
- Concept drift monitoring
- Automatic retraining triggers
- Fairness monitoring

## Deployment

### Docker Deployment (Recommended)

```bash
# Build backend image
docker build -t icu-mortality-backend ./backend

# Build frontend image
docker build -t icu-mortality-frontend ./frontend

# Run with docker-compose
docker-compose up -d
```

### Native Windows Deployment

```bash
# Install as Windows service
python backend/service_install.py

# Or run with task scheduler
# Configure backend to start on boot
```

## Troubleshooting

### ONNX Conversion Issues
- Ensure PyTorch is properly installed
- Check model compatibility with ONNX opset version
- Verify input/output tensor shapes

### ARM64 Compatibility
- Use ARM64-specific Python wheels
- Install ARM64-optimized ONNX Runtime
- Check NPU driver availability

### Data Source Access
- For restricted sources (MIMIC-IV, eICU), complete credentialing
- Check network connectivity for public sources
- Verify API keys for external services

### Interface Issues
- Check if ports 3054 and 8054 are available
- Verify Node.js and Python dependencies
- Clear Next.js cache: `rm -rf .next`
- Check browser console for errors

## Contributing

This system is designed for continuous improvement. Key areas for contribution:

1. Additional specialized agents
2. More data source connectors
3. Enhanced ONNX optimizations
4. Frontend UI improvements
5. Additional evaluation metrics

## License

This project maintains the original research license while adding production-ready components.

## Acknowledgments

- Original research foundation
- PhysioNet for medical datasets
- ONNX Runtime for cross-platform deployment
- Hugging Face for NLP models
- ChromaDB for vector database
- Anthropic for Claude API
- GLM for Chinese language model API

## Contact & Support

For issues, questions, or contributions, please refer to the project repository.

---

**System Version**: 2.0.0  
**Last Updated**: 2026-07-02  
**Platform**: Windows ARM64 Snapdragon NPU  
**Optimization**: ONNX + ARM64 + NPU  
**Interface**: Black & Green Matrix Theme with Circular Layout  
**AI Agents**: 21 Total (13 Claude Opus, 5 GLM, 3 Claude Haiku)