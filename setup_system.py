"""
Setup Script for ICU Mortality Prediction System
Automated setup for the full-stack AI application
"""

import subprocess
import sys
import os
from pathlib import Path
import logging
import platform


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SystemSetup:
    """Automated setup for the ICU Mortality Prediction System."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.is_arm64 = platform.machine().lower() in ('arm64', 'aarch64')
        self.is_windows = platform.system().lower() == 'windows'
        
    def check_prerequisites(self):
        """Check system prerequisites."""
        logger.info("Checking prerequisites...")
        
        # Check Python version
        python_version = sys.version_info
        if python_version < (3, 11):
            logger.error(f"Python 3.11+ required, found {python_version}")
            return False
        
        logger.info(f"✓ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
        
        # Check platform
        logger.info(f"✓ Platform: {platform.system()} {platform.machine()}")
        
        if self.is_arm64:
            logger.info("✓ ARM64 architecture detected - NPU optimization available")
        
        return True
    
    def setup_backend(self):
        """Setup backend environment."""
        logger.info("\n" + "="*60)
        logger.info("Setting up Backend...")
        logger.info("="*60)
        
        backend_dir = self.project_root / "backend"
        
        # Create virtual environment
        logger.info("Creating virtual environment...")
        venv_path = backend_dir / "venv"
        
        try:
            subprocess.run(
                [sys.executable, "-m", "venv", str(venv_path)],
                check=True,
                capture_output=True
            )
            logger.info(f"✓ Virtual environment created at {venv_path}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create virtual environment: {e}")
            return False
        
        # Determine pip path
        if self.is_windows:
            pip_path = venv_path / "Scripts" / "pip.exe"
            python_path = venv_path / "Scripts" / "python.exe"
        else:
            pip_path = venv_path / "bin" / "pip"
            python_path = venv_path / "bin" / "python"
        
        # Install requirements
        logger.info("Installing backend dependencies...")
        requirements_file = backend_dir / "requirements.txt"
        
        if not requirements_file.exists():
            logger.error(f"Requirements file not found: {requirements_file}")
            return False
        
        try:
            # Install standard requirements
            subprocess.run(
                [str(pip_path), "install", "-r", str(requirements_file)],
                check=True,
                capture_output=True
            )
            logger.info("✓ Backend dependencies installed")
            
            # Install ARM64-specific packages if applicable
            if self.is_arm64:
                logger.info("Installing ARM64-optimized packages...")
                try:
                    subprocess.run(
                        [str(pip_path), "install", "--platform", "win_arm64", 
                         "torch", "onnxruntime"],
                        check=True,
                        capture_output=True
                    )
                    logger.info("✓ ARM64-optimized packages installed")
                except subprocess.CalledProcessError:
                    logger.warning("Could not install ARM64-specific packages, using standard versions")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install dependencies: {e}")
            return False
        
        # Create necessary directories
        logger.info("Creating necessary directories...")
        directories = [
            backend_dir / "logs",
            backend_dir / "data",
            self.project_root / "onnx_models",
            self.project_root / "rag_system" / "vector_db" / "chroma",
            self.project_root / "data_sources" / "cache"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
        
        logger.info("✓ Directories created")
        
        return True
    
    def convert_models(self):
        """Convert PyTorch models to ONNX format."""
        logger.info("\n" + "="*60)
        logger.info("Converting Models to ONNX Format...")
        logger.info("="*60)
        
        backend_dir = self.project_root / "backend"
        venv_python = backend_dir / "venv" / "Scripts" / "python.exe" if self.is_windows else backend_dir / "venv" / "bin" / "python"
        
        if not venv_python.exists():
            logger.warning("Backend virtual environment not found, skipping model conversion")
            return True
        
        convert_script = self.project_root / "scripts" / "convert_to_onnx.py"
        
        if not convert_script.exists():
            logger.warning("Model conversion script not found, skipping")
            return True
        
        try:
            subprocess.run(
                [str(venv_python), str(convert_script)],
                check=True,
                capture_output=True
            )
            logger.info("✓ Models converted to ONNX format")
        except subprocess.CalledProcessError as e:
            logger.warning(f"Model conversion failed: {e}")
            logger.warning("You can run this manually later with: python scripts/convert_to_onnx.py")
        
        return True
    
    def setup_frontend(self):
        """Setup frontend environment."""
        logger.info("\n" + "="*60)
        logger.info("Setting up Frontend...")
        logger.info("="*60)
        
        frontend_dir = self.project_root / "frontend"
        
        if not frontend_dir.exists():
            logger.warning("Frontend directory not found, skipping frontend setup")
            logger.info("Frontend is optional - backend can run independently")
            return True
        
        # Check if Node.js is installed
        try:
            subprocess.run(
                ["node", "--version"],
                check=True,
                capture_output=True
            )
            logger.info("✓ Node.js is installed")
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.warning("Node.js not found, skipping frontend setup")
            logger.info("Install Node.js from https://nodejs.org/ to use the frontend")
            return True
        
        # Install npm dependencies
        logger.info("Installing frontend dependencies...")
        
        try:
            subprocess.run(
                ["npm", "install"],
                cwd=str(frontend_dir),
                check=True,
                capture_output=True
            )
            logger.info("✓ Frontend dependencies installed")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install frontend dependencies: {e}")
            return False
        
        return True
    
    def download_sample_data(self):
        """Download sample medical data."""
        logger.info("\n" + "="*60)
        logger.info("Setting up Data Sources...")
        logger.info("="*60)
        
        logger.info("Data source setup instructions:")
        logger.info("\nFreely accessible datasets (can be downloaded now):")
        logger.info("1. PhysioNet Challenge 2012: https://physionet.org/files/challenge-2012/1.0.0/")
        logger.info("2. SICdb: https://physionet.org/content/sicdb/")
        logger.info("3. HiRID: https://physionet.org/content/hirid/1.0/")
        logger.info("4. NWICU: https://physionet.org/content/nwicu-northwestern-icu/0.1.0/")
        
        logger.info("\nRestricted datasets (require credentialing):")
        logger.info("1. MIMIC-IV: Complete CITI training at https://physionet.org/")
        logger.info("2. eICU-CRD: Complete CITI training at https://physionet.org/")
        
        logger.info("\nPublic health data:")
        logger.info("1. WHO Mortality Database: https://www.who.int/data/data-collection-tools/who-mortality-database")
        logger.info("2. CDC Mortality Data: https://data.cdc.gov/")
        
        logger.info("\n✓ Data source information provided")
        logger.info("Note: The system includes sample synthetic data for immediate testing")
        
        return True
    
    def create_env_file(self):
        """Create environment configuration file."""
        logger.info("\n" + "="*60)
        logger.info("Creating Configuration Files...")
        logger.info("="*60)
        
        env_file = self.project_root / "backend" / ".env"
        
        env_content = f"""# ICU Mortality Prediction System Configuration

# API Settings
HOST=0.0.0.0
PORT=8054
DEBUG=True

# Anthropic API Configuration for AI Agents
ANTHROPIC_API_KEY=your_anthropic_api_key_here
ANTHROPIC_MODEL_DEFAULT=claude-3-opus-20240229
ANTHROPIC_MODEL_FAST=claude-3-haiku-20240307
ANTHROPIC_MAX_TOKENS=4096
ANTHROPIC_TEMPERATURE=0.7

# Database Settings
DATABASE_URL=sqlite:///./icu_mortality.db
VECTOR_DB_PATH=./rag_system/vector_db/chroma

# Model Settings
MODEL_PATH=./onnx_models
ONNX_OPTIMIZED=true
ARM64_OPTIMIZED={str(self.is_arm64).lower()}
USE_NPU={str(self.is_arm64).lower()}

# Agent Settings
NUM_AGENTS=21
ENABLE_RAG=true

# Data Sources
ENABLE_PHYSIONET_CHALLENGE=true
ENABLE_SICDB=true
ENABLE_NWICU=true
ENABLE_HIRID=true
ENABLE_WHO_MORTALITY=true
ENABLE_CDC_DATA=true

# Evaluation Settings
ENABLE_CONTINUOUS_EVAL=true
EVAL_INTERVAL_HOURS=24

# Logging
LOG_LEVEL=INFO

# Frontend Configuration
FRONTEND_URL=http://localhost:3054
ENABLE_CORS=true
"""
        
        try:
            with open(env_file, 'w') as f:
                f.write(env_content)
            logger.info(f"✓ Configuration file created at {env_file}")
        except Exception as e:
            logger.error(f"Failed to create configuration file: {e}")
            return False
        
        return True
    
    def generate_startup_script(self):
        """Generate startup script for the system."""
        logger.info("\n" + "="*60)
        logger.info("Creating Startup Scripts...")
        logger.info("="*60)
        
        if self.is_windows:
            # Create Windows batch script
            startup_script = self.project_root / "start_system.bat"
            
            script_content = """@echo off
echo Starting ICU Mortality Prediction System...
echo.

echo Starting Backend...
cd backend
venv\\Scripts\\activate
python main.py
"""
            
            try:
                with open(startup_script, 'w') as f:
                    f.write(script_content)
                logger.info(f"✓ Windows startup script created: {startup_script}")
            except Exception as e:
                logger.error(f"Failed to create startup script: {e}")
        
        return True
    
    def print_summary(self):
        """Print setup summary."""
        logger.info("\n" + "="*60)
        logger.info("SETUP COMPLETE!")
        logger.info("="*60)
        
        logger.info("\nSystem Components:")
        logger.info("✓ Backend API (FastAPI)")
        logger.info("✓ 20 AI Agents")
        logger.info("✓ RAG System (ChromaDB)")
        logger.info("✓ ONNX Model Optimization")
        
        if self.is_arm64:
            logger.info("✓ ARM64 Snapdragon NPU Optimization")
        
        logger.info("\nTo start the system:")
        if self.is_windows:
            logger.info("1. Run: start_system.bat")
            logger.info("   Or manually:")
            logger.info("   cd backend")
            logger.info("   venv\\Scripts\\activate")
            logger.info("   python main.py")
        else:
            logger.info("1. cd backend")
            logger.info("2. source venv/bin/activate")
            logger.info("3. python main.py")
        
        logger.info("\nAPI Documentation will be available at:")
        logger.info("http://localhost:8054/docs")
        
        logger.info("\nFor more information, see SYSTEM_README.md")
        
    def run(self):
        """Run the complete setup process."""
        logger.info("="*60)
        logger.info("ICU MORTALITY PREDICTION SYSTEM - SETUP")
        logger.info("="*60)
        
        steps = [
            ("Checking Prerequisites", self.check_prerequisites),
            ("Setting up Backend", self.setup_backend),
            ("Converting Models to ONNX", self.convert_models),
            ("Setting up Frontend", self.setup_frontend),
            ("Setting up Data Sources", self.download_sample_data),
            ("Creating Configuration", self.create_env_file),
            ("Creating Startup Scripts", self.generate_startup_script)
        ]
        
        failed_steps = []
        
        for step_name, step_func in steps:
            try:
                if not step_func():
                    failed_steps.append(step_name)
            except Exception as e:
                logger.error(f"Error in {step_name}: {e}")
                failed_steps.append(step_name)
        
        if failed_steps:
            logger.warning("\n" + "="*60)
            logger.warning("SETUP COMPLETED WITH WARNINGS")
            logger.warning("="*60)
            logger.warning(f"Failed steps: {', '.join(failed_steps)}")
        else:
            self.print_summary()


def main():
    """Main entry point."""
    setup = SystemSetup()
    setup.run()


if __name__ == "__main__":
    main()