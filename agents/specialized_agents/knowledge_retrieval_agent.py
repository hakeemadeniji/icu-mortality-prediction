"""
Knowledge Retrieval Agent - RAG-based medical knowledge retrieval
"""

import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime
from base_agents.base_agent import BaseAgent


class KnowledgeRetrievalAgent(BaseAgent):
    """
    Agent specialized in RAG-based medical knowledge retrieval.
    
    Capabilities:
    - Medical literature search
    - Clinical guidelines retrieval
    - Evidence-based information access
    - Knowledge synthesis
    """
    
    def __init__(self):
        super().__init__(
            agent_id="knowledge_retrieval_agent",
            name="Knowledge Retrieval Agent",
            description="RAG-based medical knowledge retrieval with AI-powered synthesis"
        )
        
        # Knowledge base categories
        self.knowledge_categories = [
            "clinical_guidelines",
            "medical_literature",
            "best_practices",
            "drug_information",
            "diagnostic_criteria"
        ]
        
        # Model selection: Claude Haiku for fast retrieval
        self.model_preference = "claude-haiku"
        self.model_reasoning = "Fast retrieval and synthesis of medical knowledge"

    def _initialize_capabilities(self):
        self.add_capability("literature_search")
        self.add_capability("guidelines_retrieval")
        self.add_capability("evidence_synthesis")
        self.add_capability("knowledge_base_access")
        
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data for knowledge retrieval."""
        return "query" in input_data or "clinical_question" in input_data
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Retrieve medical knowledge based on query.
        
        Args:
            input_data: Contains query and context
            
        Returns:
            Dict with retrieved knowledge
        """
        query = input_data.get("query") or input_data.get("clinical_question", "")
        context = input_data.get("context", {})
        knowledge_base = input_data.get("knowledge_base", "all")
        
        self.logger.info(f"Retrieving knowledge for query: {query[:50]}...")
        
        # Search knowledge base
        search_results = await self._search_knowledge_base(query, knowledge_base)
        
        # Retrieve clinical guidelines
        guidelines = await self._retrieve_guidelines(query, context)
        
        # Synthesize evidence
        evidence_synthesis = await self._synthesize_evidence(search_results, guidelines)
        
        # Generate knowledge summary
        knowledge_summary = await self._generate_knowledge_summary(query, evidence_synthesis)
        
        return {
            "search_results": search_results,
            "guidelines": guidelines,
            "evidence_synthesis": evidence_synthesis,
            "knowledge_summary": knowledge_summary,
            "retrieval_metadata": {
                "query": query,
                "retrieval_time": datetime.now().isoformat(),
                "model_used": self.model_preference,
                "sources_accessed": len(search_results) + len(guidelines)
            }
        }
    
    async def _search_knowledge_base(self, query: str, knowledge_base: str) -> List[Dict[str, Any]]:
        """Search the knowledge base for relevant information."""
        # Simulated knowledge base search
        # In production, this would query ChromaDB or similar vector database
        
        search_results = []
        
        # Simulated results based on query keywords
        query_lower = query.lower()
        
        if "sepsis" in query_lower:
            search_results.append({
                "source": "Surviving Sepsis Campaign Guidelines",
                "content": "Early recognition and treatment of sepsis improves outcomes",
                "relevance": 0.95,
                "year": 2021,
                "evidence_level": "high"
            })
        elif "ards" in query_lower or "acute_respiratory_distress" in query_lower:
            search_results.append({
                "source": "ARDSNet Guidelines",
                "content": "Lung-protective ventilation strategy for ARDS",
                "relevance": 0.92,
                "year": 2019,
                "evidence_level": "high"
            })
        elif "delirium" in query_lower:
            search_results.append({
                "source": "ICU Delirium Guidelines",
                "content": "ABCDE bundle for delirium prevention and management",
                "relevance": 0.88,
                "year": 2018,
                "evidence_level": "moderate"
            })
        
        # Add general ICU knowledge
        search_results.append({
            "source": "Critical Care Medicine",
            "content": "Multimodal monitoring improves early detection of clinical deterioration",
            "relevance": 0.75,
            "year": 2020,
            "evidence_level": "moderate"
        })
        
        return search_results
    
    async def _retrieve_guidelines(self, query: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Retrieve relevant clinical guidelines."""
        guidelines = []
        
        query_lower = query.lower()
        
        # Common clinical guidelines
        if "sepsis" in query_lower:
            guidelines.append({
                "guideline": "Surviving Sepsis Campaign",
                "recommendation": "Administer antibiotics within 1 hour of recognition",
                "strength": "strong",
                "quality": "moderate"
            })
        elif "ventilation" in query_lower or "respiratory" in query_lower:
            guidelines.append({
                "guideline": "ARDS Network",
                "recommendation": "Use low tidal volume ventilation (6 mL/kg PBW)",
                "strength": "strong",
                "quality": "high"
            })
        elif "sedation" in query_lower:
            guidelines.append({
                "guideline": "PADIS Guidelines",
                "recommendation": "Use sedation protocols with daily interruption",
                "strength": "strong",
                "quality": "high"
            })
        
        return guidelines
    
    async def _synthesize_evidence(self, search_results: List[Dict[str, Any]], 
                                  guidelines: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Synthesize evidence from multiple sources."""
        synthesis = {
            "key_findings": [],
            "evidence_strength": "moderate",
            "consensus_level": "moderate",
            "gaps": []
        }
        
        # Extract key findings
        for result in search_results:
            synthesis["key_findings"].append(result["content"])
        
        for guideline in guidelines:
            synthesis["key_findings"].append(f"Guideline: {guideline['recommendation']}")
        
        # Determine evidence strength
        high_evidence = [r for r in search_results if r.get("evidence_level") == "high"]
        if len(high_evidence) >= 2:
            synthesis["evidence_strength"] = "high"
            synthesis["consensus_level"] = "strong"
        elif len(high_evidence) >= 1:
            synthesis["evidence_strength"] = "moderate"
            synthesis["consensus_level"] = "moderate"
        else:
            synthesis["evidence_strength"] = "low"
            synthesis["consensus_level"] = "limited"
        
        return synthesis
    
    async def _generate_knowledge_summary(self, query: str, 
                                        evidence_synthesis: Dict[str, Any]) -> str:
        """Generate a summary of retrieved knowledge."""
        summary = f"Based on the query '{query}', "
        summary += f"evidence strength is {evidence_synthesis['evidence_strength']} "
        summary += f"with {evidence_synthesis['consensus_level']} consensus. "
        
        if evidence_synthesis["key_findings"]:
            summary += f"Key findings include: {evidence_synthesis['key_findings'][0]}"
            if len(evidence_synthesis["key_findings"]) > 1:
                summary += f" and {len(evidence_synthesis['key_findings']) - 1} additional findings."
        
        return summary