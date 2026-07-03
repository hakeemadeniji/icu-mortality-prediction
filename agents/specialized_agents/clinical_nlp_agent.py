"""
Clinical NLP Agent - Processes clinical notes with medical NER
"""

import asyncio
import logging
import re
from typing import Dict, Any, List
from datetime import datetime
from base_agents.base_agent import BaseAgent


class ClinicalNLPAgent(BaseAgent):
    """
    Agent specialized in processing clinical notes.
    
    Capabilities:
    - Medical named entity recognition
    - Clinical concept extraction
    - Sentiment analysis
    - Temporal information extraction
    """
    
    def __init__(self):
        super().__init__(
            agent_id="clinical_nlp_agent",
            name="Clinical NLP Agent",
            description="Processes clinical notes with medical NLP"
        )
        
        # Medical entity patterns (simplified)
        self.medical_entities = {
            "conditions": r"(?:diagnosis|condition|disease):\s*([^.]+)",
            "medications": r"(?:medication|drug|prescribed):\s*([^.]+)",
            "procedures": r"(?:procedure|surgery|operation):\s*([^.]+)",
            "symptoms": r"(?:symptom|complaint|presenting with):\s*([^.]+)"
        }
        
    def _initialize_capabilities(self):
        self.add_capability("medical_ner")
        self.add_capability("clinical_concept_extraction")
        self.add_capability("sentiment_analysis")
        self.add_capability("temporal_extraction")
        
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data for clinical NLP."""
        return "clinical_notes" in input_data or "text" in input_data
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process clinical notes and extract medical information.
        
        Args:
            input_data: Contains clinical notes text
            
        Returns:
            Dict with extracted medical entities and analysis
        """
        text = input_data.get("clinical_notes") or input_data.get("text", "")
        
        self.logger.info(f"Processing clinical notes ({len(text)} characters)")
        
        # Extract medical entities
        entities = await self._extract_medical_entities(text)
        
        # Perform sentiment analysis
        sentiment = await self._analyze_sentiment(text)
        
        # Extract temporal information
        temporal_info = await self._extract_temporal_info(text)
        
        # Extract key clinical concepts
        concepts = await self._extract_clinical_concepts(text)
        
        return {
            "entities": entities,
            "sentiment": sentiment,
            "temporal_info": temporal_info,
            "clinical_concepts": concepts,
            "processing_metadata": {
                "text_length": len(text),
                "processing_time": datetime.now().isoformat()
            }
        }
    
    async def _extract_medical_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract medical named entities from text."""
        entities = {}
        
        for entity_type, pattern in self.medical_entities.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities[entity_type] = [match.strip() for match in matches]
        
        return entities
    
    async def _analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment of clinical notes."""
        # Simplified sentiment analysis
        negative_words = ["critical", "severe", "worsening", "deteriorating", "unstable"]
        positive_words = ["stable", "improving", "recovering", "better"]
        
        text_lower = text.lower()
        negative_count = sum(1 for word in negative_words if word in text_lower)
        positive_count = sum(1 for word in positive_words if word in text_lower)
        
        if negative_count > positive_count:
            sentiment = "negative"
            score = -0.5 - (0.1 * negative_count)
        elif positive_count > negative_count:
            sentiment = "positive"
            score = 0.5 + (0.1 * positive_count)
        else:
            sentiment = "neutral"
            score = 0.0
        
        return {
            "sentiment": sentiment,
            "score": max(-1.0, min(1.0, score)),
            "negative_indicators": negative_count,
            "positive_indicators": positive_count
        }
    
    async def _extract_temporal_info(self, text: str) -> Dict[str, Any]:
        """Extract temporal information from clinical notes."""
        # Simplified temporal extraction
        time_patterns = [
            r"(\d+)\s*(?:hours|hrs|h)\s*ago",
            r"(\d+)\s*(?:days|d)\s*ago",
            r"(\d+)\s*(?:weeks|w)\s*ago"
        ]
        
        temporal_info = {"time_references": []}
        
        for pattern in time_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            temporal_info["time_references"].extend(matches)
        
        return temporal_info
    
    async def _extract_clinical_concepts(self, text: str) -> List[str]:
        """Extract key clinical concepts."""
        # Simplified concept extraction
        clinical_keywords = [
            "sepsis", "pneumonia", "heart failure", "renal failure",
            "respiratory failure", "shock", "cardiac arrest",
            "stroke", "bleeding", "infection", "fever"
        ]
        
        text_lower = text.lower()
        concepts = [keyword for keyword in clinical_keywords if keyword in text_lower]
        
        return concepts