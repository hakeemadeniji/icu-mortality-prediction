"""
Agent Service - Orchestrates all AI agents
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from agents.specialized_agents.data_ingestion_agent import DataIngestionAgent
from agents.specialized_agents.clinical_nlp_agent import ClinicalNLPAgent
from agents.specialized_agents.model_ensemble_agent import ModelEnsembleAgent
from agents.specialized_agents.vitals_analysis_agent import VitalsAnalysisAgent

# Import all 16 newly implemented specialized agents
from agents.specialized_agents.labs_analysis_agent import LabsAnalysisAgent
from agents.specialized_agents.medication_analysis_agent import MedicationAnalysisAgent
from agents.specialized_agents.comorbidity_analysis_agent import ComorbidityAnalysisAgent
from agents.specialized_agents.demographics_analysis_agent import DemographicsAnalysisAgent
from agents.specialized_agents.confidence_estimation_agent import ConfidenceEstimationAgent
from agents.specialized_agents.explainability_agent import ExplainabilityAgent
from agents.specialized_agents.fairness_agent import FairnessAgent
from agents.specialized_agents.alert_generation_agent import AlertGenerationAgent
from agents.specialized_agents.evaluation_monitoring_agent import EvaluationMonitoringAgent
from agents.specialized_agents.correction_trigger_agent import CorrectionTriggerAgent
from agents.specialized_agents.knowledge_retrieval_agent import KnowledgeRetrievalAgent
from agents.specialized_agents.clinical_guidelines_agent import ClinicalGuidelinesAgent
from agents.specialized_agents.patient_context_agent import PatientContextAgent
from agents.specialized_agents.data_quality_agent import DataQualityAgent
from agents.specialized_agents.feature_engineering_agent import FeatureEngineeringAgent
from agents.specialized_agents.time_series_analysis_agent import TimeSeriesAnalysisAgent
from agents.specialized_agents.risk_assessment_agent import RiskAssessmentAgent
from agents.specialized_agents.clinical_decision_support_agent import ClinicalDecisionSupportAgent


class AgentService:
    """
    Main service for orchestrating all AI agents.
    
    Manages 20+ specialized agents for comprehensive
    ICU mortality prediction.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("agent_service")
        self.agents: Dict[str, Any] = {}
        self.agent_registry = {}
        self.orchestration_queue = asyncio.Queue()
        self._ready = False
        
    async def initialize(self):
        """Initialize all agents."""
        self.logger.info("Initializing Agent Service...")
        
        # Register all agents
        await self._register_agents()
        
        # Start all agents
        await self._start_all_agents()
        
        self._ready = True
        self.logger.info(f"Agent Service initialized with {len(self.agents)} agents")
        
    async def _register_agents(self):
        """Register all specialized agents."""
        
        # Core ML agents (original 4)
        self.agents["data_ingestion"] = DataIngestionAgent()
        self.agents["clinical_nlp"] = ClinicalNLPAgent()
        self.agents["model_ensemble"] = ModelEnsembleAgent()
        self.agents["vitals_analysis"] = VitalsAnalysisAgent()
        
        # Register all 16 newly implemented specialized agents
        self.agents["labs_analysis"] = LabsAnalysisAgent()
        self.agents["medication_analysis"] = MedicationAnalysisAgent()
        self.agents["comorbidity_analysis"] = ComorbidityAnalysisAgent()
        self.agents["demographics_analysis"] = DemographicsAnalysisAgent()
        self.agents["confidence_estimation"] = ConfidenceEstimationAgent()
        self.agents["explainability"] = ExplainabilityAgent()
        self.agents["fairness_monitoring"] = FairnessAgent()
        self.agents["alert_generation"] = AlertGenerationAgent()
        self.agents["evaluation_monitoring"] = EvaluationMonitoringAgent()
        self.agents["correction_trigger"] = CorrectionTriggerAgent()
        self.agents["knowledge_retrieval"] = KnowledgeRetrievalAgent()
        self.agents["clinical_guidelines"] = ClinicalGuidelinesAgent()
        self.agents["patient_context"] = PatientContextAgent()
        self.agents["data_quality"] = DataQualityAgent()
        self.agents["feature_engineering"] = FeatureEngineeringAgent()
        self.agents["time_series_analysis"] = TimeSeriesAnalysisAgent()
        self.agents["risk_assessment"] = RiskAssessmentAgent()
        self.agents["clinical_decision_support"] = ClinicalDecisionSupportAgent()
        
        # Build agent registry
        for agent_id, agent in self.agents.items():
            self.agent_registry[agent_id] = agent.get_info()
    
    
    
    async def _start_all_agents(self):
        """Start all registered agents."""
        for agent_id, agent in self.agents.items():
            try:
                await agent.start()
                self.logger.info(f"Started agent: {agent_id}")
            except Exception as e:
                self.logger.error(f"Failed to start agent {agent_id}: {e}")
    
    async def list_agents(self) -> List[Dict[str, Any]]:
        """List all available agents."""
        return list(self.agent_registry.values())
    
    async def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get specific agent information."""
        return self.agent_registry.get(agent_id)
    
    async def execute_agent(self, agent_id: str, input_data: Dict[str, Any], 
                          priority: str = "normal", timeout: int = 300) -> Dict[str, Any]:
        """Execute a specific agent."""
        agent = self.agents.get(agent_id)
        if not agent:
            return {
                "success": False,
                "error": f"Agent {agent_id} not found",
                "execution_time": 0,
                "agent_id": agent_id,
                "timestamp": datetime.now().isoformat()
            }
        
        try:
            result = await asyncio.wait_for(
                agent.execute_with_monitoring(input_data),
                timeout=timeout
            )
            return result
        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": f"Agent {agent_id} timed out",
                "execution_time": timeout,
                "agent_id": agent_id,
                "timestamp": datetime.now().isoformat()
            }
    
    async def orchestrate(self, task: str, input_data: Dict[str, Any],
                         agent_sequence: Optional[List[str]] = None,
                         parallel: bool = False) -> Dict[str, Any]:
        """Orchestrate multiple agents for complex tasks."""
        start_time = datetime.now()
        
        # Determine agent sequence based on task
        if not agent_sequence:
            agent_sequence = self._determine_agent_sequence(task)
        
        results = {}
        individual_times = {}
        
        if parallel:
            # Execute agents in parallel
            tasks = [
                self.execute_agent(agent_id, input_data)
                for agent_id in agent_sequence
            ]
            parallel_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for agent_id, result in zip(agent_sequence, parallel_results):
                results[agent_id] = result
                individual_times[agent_id] = result.get("execution_time", 0)
        else:
            # Execute agents sequentially
            for agent_id in agent_sequence:
                result = await self.execute_agent(agent_id, input_data)
                results[agent_id] = result
                individual_times[agent_id] = result.get("execution_time", 0)
        
        total_time = (datetime.now() - start_time).total_seconds()
        
        return {
            "task": task,
            "status": "completed" if all(r.get("success", False) for r in results.values()) else "partial",
            "agent_sequence": agent_sequence,
            "results": results,
            "total_time": total_time,
            "individual_times": individual_times
        }
    
    def _determine_agent_sequence(self, task: str) -> List[str]:
        """Determine optimal agent sequence for a given task."""
        task_sequences = {
            "patient_prediction": [
                "data_ingestion", "data_quality", "feature_engineering",
                "vitals_analysis", "labs_analysis", "clinical_nlp",
                "medication_analysis", "comorbidity_analysis",
                "demographics_analysis", "patient_context",
                "time_series_analysis", "model_ensemble",
                "confidence_estimation", "explainability",
                "risk_assessment", "alert_generation"
            ],
            "comprehensive_analysis": [
                "data_ingestion", "data_quality", "feature_engineering",
                "vitals_analysis", "labs_analysis", "clinical_nlp",
                "medication_analysis", "comorbidity_analysis",
                "demographics_analysis", "patient_context",
                "time_series_analysis", "risk_assessment",
                "clinical_guidelines", "knowledge_retrieval",
                "clinical_decision_support", "fairness_monitoring"
            ],
            "risk_assessment": [
                "vitals_analysis", "labs_analysis", "comorbidity_analysis",
                "time_series_analysis", "patient_context", "risk_assessment"
            ],
            "data_processing": [
                "data_ingestion", "data_quality", "feature_engineering"
            ],
            "model_evaluation": [
                "evaluation_monitoring", "fairness_monitoring", 
                "correction_trigger", "confidence_estimation"
            ],
            "clinical_support": [
                "knowledge_retrieval", "clinical_guidelines",
                "clinical_decision_support", "patient_context"
            ]
        }
        
        return task_sequences.get(task, list(self.agents.keys())[:8])
    
    async def process_patient_data(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process patient data through the multi-agent pipeline."""
        # Orchestrate full patient prediction pipeline
        result = await self.orchestrate("patient_prediction", patient_data)
        
        # Extract ensemble prediction
        ensemble_result = result["results"].get("model_ensemble", {})
        
        return {
            "mortality_risk": ensemble_result.get("result", {}).get("ensemble_prediction", 0.5),
            "confidence": ensemble_result.get("result", {}).get("confidence", 0.5),
            "prediction_time": result["total_time"],
            "model_version": "2.0.0-ensemble",
            "agent_contributions": {
                agent_id: result.get("result", {}).get("result", {})
                for agent_id, result in result["results"].items()
            },
            "risk_factors": self._extract_risk_factors(result),
            "recommendations": self._generate_recommendations(result),
            "explanation": self._generate_explanation(result)
        }
    
    async def process_batch(self, patients: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process multiple patients in batch."""
        import time
        start_time = time.time()
        
        predictions = []
        successful = 0
        failed = 0
        
        for patient_data in patients:
            try:
                prediction = await self.process_patient_data(patient_data)
                predictions.append(prediction)
                successful += 1
            except Exception as e:
                self.logger.error(f"Failed to process patient: {e}")
                predictions.append({"error": str(e)})
                failed += 1
        
        total_time = time.time() - start_time
        
        return {
            "predictions": predictions,
            "total_time": total_time,
            "successful": successful,
            "failed": failed
        }
    
    def _extract_risk_factors(self, orchestration_result: Dict[str, Any]) -> List[str]:
        """Extract risk factors from agent results."""
        risk_factors = []
        
        # Extract from vitals analysis
        vitals_result = orchestration_result["results"].get("vitals_analysis", {})
        if vitals_result.get("success"):
            vitals_data = vitals_result.get("result", {})
            alerts = vitals_data.get("threshold_alerts", [])
            risk_factors.extend([alert.get("message", "") for alert in alerts])
        
        # Extract from clinical NLP
        nlp_result = orchestration_result["results"].get("clinical_nlp", {})
        if nlp_result.get("success"):
            nlp_data = nlp_result.get("result", {})
            concepts = nlp_data.get("clinical_concepts", [])
            risk_factors.extend([f"Clinical indication: {concept}" for concept in concepts])
        
        return risk_factors[:10]  # Limit to top 10
    
    def _generate_recommendations(self, orchestration_result: Dict[str, Any]) -> List[str]:
        """Generate clinical recommendations based on agent results."""
        recommendations = []
        
        # Generate based on risk factors
        risk_factors = self._extract_risk_factors(orchestration_result)
        if risk_factors:
            recommendations.append("Monitor vital signs closely")
            recommendations.append("Consider consult with specialist")
        
        # Generate based on confidence
        ensemble_result = orchestration_result["results"].get("model_ensemble", {})
        if ensemble_result.get("success"):
            confidence = ensemble_result.get("result", {}).get("confidence", 0.5)
            if confidence < 0.7:
                recommendations.append("Prediction confidence moderate - seek additional clinical correlation")
        
        return recommendations
    
    def _generate_explanation(self, orchestration_result: Dict[str, Any]) -> str:
        """Generate explanation for the prediction."""
        return "Prediction generated by multi-agent AI system analyzing vital signs, lab values, clinical notes, and comorbidities using ensemble of deep learning models."
    
    async def start_agent(self, agent_id: str) -> bool:
        """Start a specific agent."""
        agent = self.agents.get(agent_id)
        if agent:
            await agent.start()
            return True
        return False
    
    async def stop_agent(self, agent_id: str) -> bool:
        """Stop a specific agent."""
        agent = self.agents.get(agent_id)
        if agent:
            await agent.stop()
            return True
        return False
    
    async def get_orchestration_status(self) -> Dict[str, Any]:
        """Get orchestration system status."""
        active_agents = sum(1 for agent in self.agents.values() if agent.status == "active")
        
        return {
            "total_agents": len(self.agents),
            "active_agents": active_agents,
            "inactive_agents": len(self.agents) - active_agents,
            "system_status": "healthy" if active_agents == len(self.agents) else "degraded",
            "queue_size": self.orchestration_queue.qsize()
        }
    
    def get_active_agents(self) -> int:
        """Get count of active agents."""
        return sum(1 for agent in self.agents.values() if agent.status == "active")
    
    async def get_all_agents_status(self) -> Dict[str, str]:
        """Get status of all agents."""
        return {agent_id: agent.status for agent_id, agent in self.agents.items()}
    
    def is_ready(self) -> bool:
        """Check if service is ready."""
        return self._ready
    
    async def cleanup(self):
        """Cleanup resources."""
        self.logger.info("Cleaning up Agent Service...")
        for agent_id, agent in self.agents.items():
            try:
                await agent.stop()
            except Exception as e:
                self.logger.error(f"Error stopping agent {agent_id}: {e}")
        self._ready = False