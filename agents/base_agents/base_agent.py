"""
Base Agent Class for AI Agent System
Provides the foundation for all specialized agents
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import logging
import asyncio
from datetime import datetime
import json


class BaseAgent(ABC):
    """
    Abstract base class for all AI agents.
    
    All specialized agents must inherit from this class and implement
    the required methods.
    """
    
    def __init__(self, agent_id: str, name: str, description: str):
        self.agent_id = agent_id
        self.name = name
        self.description = description
        self.status = "inactive"
        self.execution_count = 0
        self.last_execution = None
        self.logger = logging.getLogger(f"agent.{agent_id}")
        self.capabilities = []
        self._initialize_capabilities()
        
    @abstractmethod
    def _initialize_capabilities(self):
        """Initialize agent-specific capabilities."""
        pass
    
    @abstractmethod
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the agent's primary function.
        
        Args:
            input_data: Input data for the agent
            
        Returns:
            Dict containing the agent's output
        """
        pass
    
    @abstractmethod
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate input data for the agent.
        
        Args:
            input_data: Input data to validate
            
        Returns:
            True if valid, False otherwise
        """
        pass
    
    async def start(self):
        """Start the agent."""
        self.status = "active"
        self.logger.info(f"Agent {self.name} started")
        
    async def stop(self):
        """Stop the agent."""
        self.status = "inactive"
        self.logger.info(f"Agent {self.name} stopped")
        
    async def health_check(self) -> bool:
        """
        Perform health check on the agent.
        
        Returns:
            True if healthy, False otherwise
        """
        return self.status == "active"
    
    def get_info(self) -> Dict[str, Any]:
        """
        Get agent information.
        
        Returns:
            Dict containing agent information
        """
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "capabilities": self.capabilities,
            "execution_count": self.execution_count,
            "last_execution": self.last_execution
        }
    
    async def execute_with_monitoring(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute agent with monitoring and error handling.
        
        Args:
            input_data: Input data for the agent
            
        Returns:
            Dict containing agent output and metadata
        """
        start_time = datetime.now()
        self.execution_count += 1
        
        try:
            # Validate input
            if not await self.validate_input(input_data):
                raise ValueError(f"Invalid input for agent {self.name}")
            
            # Execute agent
            result = await self.execute(input_data)
            
            # Update metadata
            execution_time = (datetime.now() - start_time).total_seconds()
            self.last_execution = datetime.now().isoformat()
            
            return {
                "success": True,
                "result": result,
                "execution_time": execution_time,
                "agent_id": self.agent_id,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error in agent {self.name}: {e}")
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "success": False,
                "error": str(e),
                "execution_time": execution_time,
                "agent_id": self.agent_id,
                "timestamp": datetime.now().isoformat()
            }
    
    def add_capability(self, capability: str):
        """Add a capability to the agent."""
        if capability not in self.capabilities:
            self.capabilities.append(capability)
    
    def has_capability(self, capability: str) -> bool:
        """Check if agent has a specific capability."""
        return capability in self.capabilities