# ICU Mortality Prediction System - Startup Guide

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Anthropic API Key
- GLM API Key

### Configuration

1. **Set your API Keys:**
   Edit `backend/.env` and add your actual API keys:
   ```bash
   ANTHROPIC_API_KEY=your_actual_anthropic_api_key_here
   GLM_API_KEY=your_actual_glm_api_key_here
   ```

2. **VSCode Configuration:**
   The `.vscode/settings.json` file is configured to:
   - Enable `python.terminal.useEnvFile` to automatically load environment variables from `.env` files
   - Activate Python virtual environments automatically
   - Enable auto-formatting on save

### Starting the System

#### Option 1: Automated Startup (Windows)

**Using Batch File:**
```bash
START_FRONTEND.bat
START_BACKEND_MANUAL.bat
```

**Using PowerShell:**
```bash
powershell -ExecutionPolicy Bypass -File startup_system.ps1
```

#### Option 2: Manual Startup

**Start Backend (Port 8054):**
```bash
cd backend
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
python main.py
```

**Start Frontend (Port 3054):**
```bash
cd frontend
npm install
npm run dev
```

### Access Points

- **Frontend Interface:** http://localhost:3054
- **Backend API:** http://localhost:8054
- **API Documentation:** http://localhost:8054/docs
- **Interactive API Console:** http://localhost:8054/docs

### Port Configuration

The system is configured to use:
- **Frontend:** Port 3054
- **Backend API:** Port 8054

These ports can be changed in:
- `backend/.env` (PORT)
- `frontend/package.json` (dev script)
- `frontend/next.config.js` (API proxy)

### Environment Variables

The system automatically loads environment variables from:
- `backend/.env` (for Python backend)
- `frontend/.env.local` (for Next.js frontend)

Key environment variables:
```bash
# Backend (.env)
ANTHROPIC_API_KEY=your_key_here
GLM_API_KEY=your_key_here
PORT=8054
FRONTEND_URL=http://localhost:3054

# Frontend (.env.local)
NEXT_PUBLIC_API_URL=http://localhost:8054
NEXT_PUBLIC_FRONTEND_URL=http://localhost:3054
```

### Interface Overview

The interface features:
- **Black & Green Matrix Theme**: Pure black background with green holographic effects
- **Circular Clock Layout**: 6 sections arranged like clock positions
- **Large Bold Text**: 2rem+ font sizes with 900 weight for readability
- **3D Holographic Effects**: Floating particles, animated grid, glowing elements
- **Button Navigation**: Large button-style elements lined up side by side

### Pages

1. **Homepage** (http://localhost:3054)
   - Circular layout with system stats
   - Central hub: "ICU AI SYSTEM CORE"
   - 6 circular sections: Active Agents, Prediction Accuracy, Data Sources, System Status, Neural Interface, Processing Power
   - Navigation buttons: Prediction Dashboard, Agent Monitoring, System Analytics

2. **Dashboard** (http://localhost:3054/dashboard)
   - Patient data input interface
   - Real-time prediction results
   - Model explanation interface

3. **Agents** (http://localhost:3054/agents)
   - Live monitoring of all 21 AI agents
   - Agent status indicators
   - Performance metrics

4. **Analytics** (http://localhost:3054/analytics)
   - System monitoring dashboard
   - Data source management
   - Performance analytics

### Troubleshooting

**Backend won't start:**
- Check if port 8054 is already in use
- Verify Python dependencies are installed
- Check `.env` file configuration (both API keys)
- Ensure API keys are valid

**Frontend won't start:**
- Check if port 3054 is already in use
- Verify Node.js dependencies are installed
- Clear Next.js cache: `rm -rf .next`

**Environment variables not loading:**
- Ensure `.vscode/settings.json` has `python.terminal.useEnvFile` set to `true`
- Restart VSCode after changing settings
- Check that `.env` files are in the correct directories

**API Integration Issues:**
- Verify API keys are correct in `backend/.env`
- Check Anthropic and GLM API quotas
- Review backend logs for specific error messages

### Development

**VSCode Debugging:**
- Press F5 to debug the backend
- Use the integrated terminal with automatic environment variable loading

**Hot Reload:**
- Frontend changes auto-reload
- Backend changes require manual restart

### Monitoring

- Check agent status at http://localhost:3054/agents
- View system analytics at http://localhost:3054/analytics
- Monitor API performance at http://localhost:8054/docs

### Stopping the System

**Manual Stop:**
- Press Ctrl+C in both terminal windows
- Or close the terminal windows

**Automated Stop (PowerShell):**
- Press Ctrl+C in the PowerShell window running the startup script

## 🎯 Next Steps

1. Configure your Anthropic and GLM API keys in `backend/.env`
2. Run `START_FRONTEND.bat` and `START_BACKEND_MANUAL.bat`
3. Access the interface at http://localhost:3054
4. Explore the dashboard, agent monitoring, and analytics pages

## 📚 Documentation

- **Full system documentation:** SYSTEM_README.md
- **Session context and changes:** CONTEXT.md
- **Transformation summary:** TRANSFORMATION_SUMMARY.md
- **Project overview:** README.md

## 💡 Tips

- The interface uses a black background with green text for maximum contrast
- All text is large and bold for easy reading
- Navigation buttons are lined up side by side at the bottom
- Circular layout prevents overlapping of sections
- 3D hover effects enhance the holographic feel