"""
Agent Service - Registry and lightweight orchestration for the ICU
multi-agent system.

This service intentionally has no heavy ML dependencies: it manages agent
metadata/state and provides a simple (stubbed) execution + orchestration
surface that the API layer in ``api/agents.py`` calls into. Swap the stubbed
execution for real model/LLM calls as those integrations come online.
"""

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from services.llm_service import LLMService


# The 21 specialized agents that make up the system. Kept in sync with the
# agent list surfaced on the frontend (/agents page).
_AGENT_DEFINITIONS: List[Dict[str, Any]] = [
    {"agent_id": "data_ingestion", "name": "Data Ingestion", "type": "pipeline",
     "description": "Ingests and normalizes multi-source EHR data streams.",
     "capabilities": ["ingest", "normalize", "validate"]},
    {"agent_id": "clinical_nlp", "name": "Clinical NLP", "type": "nlp",
     "description": "Extracts structured signal from unstructured clinical notes.",
     "capabilities": ["ner", "embeddings", "summarization"]},
    {"agent_id": "model_ensemble", "name": "Model Ensemble", "type": "inference",
     "description": "Combines baseline, deep-learning and fusion model outputs.",
     "capabilities": ["ensemble", "calibration"]},
    {"agent_id": "vitals_analysis", "name": "Vitals Analysis", "type": "analysis",
     "description": "Analyzes vital-sign time series for early deterioration.",
     "capabilities": ["timeseries", "trend-detection"]},
    {"agent_id": "labs_analysis", "name": "Labs Analysis", "type": "analysis",
     "description": "Interprets laboratory results and derived indices.",
     "capabilities": ["labs", "reference-ranges"]},
    {"agent_id": "medication_analysis", "name": "Medication Analysis", "type": "analysis",
     "description": "Reviews medication exposure and interaction risk.",
     "capabilities": ["pharmacology", "interactions"]},
    {"agent_id": "comorbidity_analysis", "name": "Comorbidity Analysis", "type": "analysis",
     "description": "Derives comorbidity burden and indices (e.g. Charlson).",
     "capabilities": ["icd", "comorbidity-index"]},
    {"agent_id": "demographics_analysis", "name": "Demographics Analysis", "type": "analysis",
     "description": "Contextualizes predictions with demographic factors.",
     "capabilities": ["demographics"]},
    {"agent_id": "confidence_estimation", "name": "Confidence Estimation", "type": "meta",
     "description": "Estimates predictive uncertainty and confidence intervals.",
     "capabilities": ["uncertainty", "calibration"]},
    {"agent_id": "explainability", "name": "Explainability", "type": "meta",
     "description": "Produces SHAP-style feature attributions for each prediction.",
     "capabilities": ["shap", "attribution"]},
    {"agent_id": "fairness_monitoring", "name": "Fairness Monitoring", "type": "governance",
     "description": "Monitors subgroup performance and fairness metrics.",
     "capabilities": ["fairness", "bias-detection"]},
    {"agent_id": "alert_generation", "name": "Alert Generation", "type": "action",
     "description": "Generates clinician-facing alerts from risk signals.",
     "capabilities": ["alerting", "thresholding"]},
    {"agent_id": "evaluation_monitoring", "name": "Evaluation Monitoring", "type": "governance",
     "description": "Tracks continuous evaluation metrics and drift.",
     "capabilities": ["evaluation", "drift"]},
    {"agent_id": "correction_trigger", "name": "Correction Trigger", "type": "governance",
     "description": "Triggers retraining/correction workflows on degradation.",
     "capabilities": ["retrain-trigger"]},
    {"agent_id": "knowledge_retrieval", "name": "Knowledge Retrieval", "type": "rag",
     "description": "Retrieves relevant clinical knowledge via RAG.",
     "capabilities": ["retrieval", "vector-search"]},
    {"agent_id": "clinical_guidelines", "name": "Clinical Guidelines", "type": "rag",
     "description": "Surfaces applicable evidence-based guidelines.",
     "capabilities": ["guidelines", "evidence"]},
    {"agent_id": "patient_context", "name": "Patient Context", "type": "analysis",
     "description": "Assembles a longitudinal view of the patient.",
     "capabilities": ["context", "timeline"]},
    {"agent_id": "data_quality", "name": "Data Quality", "type": "pipeline",
     "description": "Assesses completeness and quality of incoming data.",
     "capabilities": ["quality", "missingness"]},
    {"agent_id": "feature_engineering", "name": "Feature Engineering", "type": "pipeline",
     "description": "Constructs model features from raw signals.",
     "capabilities": ["features", "aggregation"]},
    {"agent_id": "time_series_analysis", "name": "Time Series Analysis", "type": "analysis",
     "description": "Models temporal dynamics across the admission window.",
     "capabilities": ["timeseries", "sequence"]},
    {"agent_id": "risk_assessment", "name": "Risk Assessment", "type": "inference",
     "description": "Produces the final mortality-risk assessment.",
     "capabilities": ["risk-scoring"]},
]

# Which model backs each agent. "Claude Opus" / "Claude Haiku" route to Anthropic
# (default / fast model), "GLM" routes to Zhipu GLM-4.
_AGENT_MODELS: Dict[str, str] = {
    "data_ingestion": "GLM",
    "clinical_nlp": "Claude Opus",
    "model_ensemble": "Claude Opus",
    "vitals_analysis": "GLM",
    "labs_analysis": "GLM",
    "medication_analysis": "Claude Opus",
    "comorbidity_analysis": "Claude Opus",
    "demographics_analysis": "Claude Haiku",
    "confidence_estimation": "Claude Opus",
    "explainability": "Claude Opus",
    "fairness_monitoring": "Claude Opus",
    "alert_generation": "Claude Haiku",
    "evaluation_monitoring": "GLM",
    "correction_trigger": "Claude Opus",
    "knowledge_retrieval": "Claude Haiku",
    "clinical_guidelines": "Claude Opus",
    "patient_context": "Claude Opus",
    "data_quality": "GLM",
    "feature_engineering": "Claude Opus",
    "time_series_analysis": "GLM",
    "risk_assessment": "Claude Opus",
}


class AgentService:
    """Manages agent registry, state and (stubbed) orchestration."""

    def __init__(self) -> None:
        self.logger = logging.getLogger("agent_service")
        self._ready = False
        self._agents: Dict[str, Dict[str, Any]] = {}
        self._llm = LLMService()

    async def initialize(self) -> None:
        """Load the agent registry and mark the service ready."""
        self.logger.info("Initializing Agent Service...")
        for definition in _AGENT_DEFINITIONS:
            agent_id = definition["agent_id"]
            self._agents[agent_id] = {
                **definition,
                "model": _AGENT_MODELS.get(agent_id, "Claude Opus"),
                "status": "active",
                "last_execution": None,
                "execution_count": 0,
            }
        self._ready = True
        self.logger.info(
            "Agent Service initialized with %d agents (LLM providers: %s)",
            len(self._agents),
            self._llm.available(),
        )

    def llm_status(self) -> Dict[str, bool]:
        """Which LLM providers are configured (anthropic / glm)."""
        return self._llm.available()

    def is_ready(self) -> bool:
        """Check if the service is ready."""
        return self._ready

    async def cleanup(self) -> None:
        """Release resources."""
        self.logger.info("Cleaning up Agent Service...")
        self._ready = False
        self._agents.clear()

    # --- Query -----------------------------------------------------------

    async def list_agents(self) -> List[Dict[str, Any]]:
        """Return metadata for all registered agents."""
        return list(self._agents.values())

    async def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Return a single agent's metadata, or None if not found."""
        return self._agents.get(agent_id)

    def get_active_agents(self) -> int:
        """Return the number of agents currently active."""
        return sum(1 for a in self._agents.values() if a["status"] == "active")

    # --- Lifecycle -------------------------------------------------------

    async def start_agent(self, agent_id: str) -> bool:
        agent = self._agents.get(agent_id)
        if not agent:
            return False
        agent["status"] = "active"
        return True

    async def stop_agent(self, agent_id: str) -> bool:
        agent = self._agents.get(agent_id)
        if not agent:
            return False
        agent["status"] = "idle"
        return True

    # --- Execution -------------------------------------------------------

    async def execute_agent(
        self,
        agent_id: str,
        input_data: Dict[str, Any],
        priority: Optional[str] = "normal",
        timeout: Optional[int] = 300,
    ) -> Dict[str, Any]:
        """Execute a single agent via its assigned LLM and update bookkeeping.

        Falls back to a deterministic acknowledgement if no LLM is configured or
        the provider call fails.
        """
        agent = self._agents.get(agent_id)
        if not agent:
            return {
                "agent_id": agent_id,
                "status": "error",
                "result": None,
                "execution_time": 0.0,
                "error": f"Agent {agent_id} not found",
            }

        start = time.perf_counter()
        system = (
            f"You are the '{agent['name']}' agent in an ICU mortality-prediction "
            f"system. Your role: {agent['description']} Respond in one concise "
            f"clinical sentence."
        )
        prompt = f"Patient snapshot: {input_data}\nProvide your {agent['type']} assessment."
        text = await self._llm.complete(
            prompt, system=system, model_label=agent["model"], max_tokens=160
        )
        elapsed = time.perf_counter() - start

        agent["execution_count"] += 1
        agent["last_execution"] = datetime.now(timezone.utc).isoformat()

        used_llm = text is not None
        return {
            "agent_id": agent_id,
            "status": "completed",
            "result": {
                "assessment": text or f"{agent['name']} completed (offline stub).",
                "model": agent["model"],
                "used_llm": used_llm,
            },
            "execution_time": round(elapsed, 4),
            "error": None,
        }

    async def generate_clinical_explanation(
        self, features: Dict[str, Any], prediction: Dict[str, Any]
    ) -> Optional[str]:
        """Use the explainability agent's LLM to narrate a prediction.

        Returns ``None`` (and callers omit the field) if no LLM is available.
        """
        agent = self._agents.get("explainability")
        model_label = agent["model"] if agent else "Claude Opus"

        system = (
            "You are a clinical decision-support assistant for ICU clinicians. "
            "Given a patient snapshot and a model's mortality-risk output, explain "
            "the assessment in 2-3 short sentences: name the main drivers and the "
            "suggested focus of care. Be factual and cautious; this is decision "
            "support, not a directive. Do not invent values."
        )
        prompt = (
            f"Patient snapshot: {features}\n"
            f"Model output: risk={prediction.get('mortality_risk')}, "
            f"category={prediction.get('risk_category')}, "
            f"key_factors={prediction.get('key_factors')}.\n"
            "Write the explanation."
        )
        text = await self._llm.complete(
            prompt, system=system, model_label=model_label, max_tokens=220
        )

        # Resilience: if the assigned provider is down (e.g. an invalid Anthropic
        # key), fall back to any other configured provider so the narration still
        # works. Switches back to the preferred model automatically once its key
        # is valid.
        if text is None:
            avail = self._llm.available()
            fallback = None
            if model_label != "GLM" and avail.get("glm"):
                fallback = "GLM"
            elif model_label == "GLM" and avail.get("anthropic"):
                fallback = "Claude Opus"
            if fallback:
                text = await self._llm.complete(
                    prompt, system=system, model_label=fallback, max_tokens=220
                )

        if agent and text is not None:
            agent["execution_count"] += 1
            agent["last_execution"] = datetime.now(timezone.utc).isoformat()
        return text

    async def orchestrate(
        self,
        task: str,
        input_data: Dict[str, Any],
        agent_sequence: Optional[List[str]] = None,
        parallel: Optional[bool] = False,
    ) -> Dict[str, Any]:
        """Run a sequence of agents (in order or in parallel) for a task."""
        sequence = agent_sequence or list(self._agents.keys())
        # Only orchestrate agents that actually exist.
        sequence = [a for a in sequence if a in self._agents]

        start = time.perf_counter()
        results: Dict[str, Any] = {}
        individual_times: Dict[str, float] = {}

        if parallel:
            outputs = await asyncio.gather(
                *(self.execute_agent(a, input_data) for a in sequence)
            )
            for agent_id, output in zip(sequence, outputs):
                results[agent_id] = output["result"]
                individual_times[agent_id] = output["execution_time"]
        else:
            for agent_id in sequence:
                output = await self.execute_agent(agent_id, input_data)
                results[agent_id] = output["result"]
                individual_times[agent_id] = output["execution_time"]

        return {
            "task": task,
            "status": "completed",
            "agent_sequence": sequence,
            "results": results,
            "total_time": round(time.perf_counter() - start, 4),
            "individual_times": individual_times,
        }

    async def get_orchestration_status(self) -> Dict[str, Any]:
        """Summarize current orchestration/agent state."""
        active = sum(1 for a in self._agents.values() if a["status"] == "active")
        total_exec = sum(a["execution_count"] for a in self._agents.values())
        return {
            "ready": self._ready,
            "total_agents": len(self._agents),
            "active_agents": active,
            "idle_agents": len(self._agents) - active,
            "total_executions": total_exec,
            "llm_providers": self._llm.available(),
        }
