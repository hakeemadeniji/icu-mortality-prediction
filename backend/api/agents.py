"""
Agents API endpoints for AI agent management and orchestration
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class AgentInfo(BaseModel):
    """Agent information model."""
    
    agent_id: str = Field(..., description="Unique agent identifier")
    name: str = Field(..., description="Agent name")
    type: str = Field(..., description="Agent type")
    description: str = Field(..., description="Agent description")
    model: Optional[str] = Field(None, description="LLM backing this agent")
    status: str = Field(..., description="Agent status (active/inactive/error)")
    capabilities: List[str] = Field(default_factory=list, description="Agent capabilities")
    last_execution: Optional[str] = Field(None, description="Last execution timestamp")
    execution_count: int = Field(default=0, description="Total execution count")


class AgentExecutionRequest(BaseModel):
    """Agent execution request model."""
    
    agent_id: str = Field(..., description="Agent to execute")
    input_data: Dict[str, Any] = Field(..., description="Input data for agent")
    priority: Optional[str] = Field("normal", description="Execution priority")
    timeout: Optional[int] = Field(300, description="Execution timeout in seconds")


class AgentExecutionResponse(BaseModel):
    """Agent execution response model."""
    
    agent_id: str = Field(..., description="Executed agent ID")
    status: str = Field(..., description="Execution status")
    result: Optional[Dict[str, Any]] = Field(None, description="Execution result")
    execution_time: float = Field(..., description="Execution time in seconds")
    error: Optional[str] = Field(None, description="Error message if failed")


class OrchestrationRequest(BaseModel):
    """Multi-agent orchestration request model."""
    
    task: str = Field(..., description="Task to orchestrate")
    input_data: Dict[str, Any] = Field(..., description="Input data")
    agent_sequence: Optional[List[str]] = Field(
        None,
        description="Specific agent sequence (if None, auto-orchestrated)"
    )
    parallel: Optional[bool] = Field(False, description="Execute agents in parallel")


class OrchestrationResponse(BaseModel):
    """Orchestration response model."""
    
    task: str = Field(..., description="Executed task")
    status: str = Field(..., description="Overall status")
    agent_sequence: List[str] = Field(..., description="Agents executed")
    results: Dict[str, Any] = Field(..., description="Combined results")
    total_time: float = Field(..., description="Total orchestration time")
    individual_times: Dict[str, float] = Field(
        default_factory=dict,
        description="Individual agent execution times"
    )


@router.get("/list", response_model=List[AgentInfo])
async def list_agents():
    """List all available AI agents."""
    try:
        from main import agent_service
        
        if not agent_service:
            raise HTTPException(status_code=503, detail="Agent service not ready")
        
        agents = await agent_service.list_agents()
        return agents
        
    except Exception as e:
        logger.error(f"Error listing agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_id}", response_model=AgentInfo)
async def get_agent(agent_id: str):
    """Get detailed information about a specific agent."""
    try:
        from main import agent_service
        
        if not agent_service:
            raise HTTPException(status_code=503, detail="Agent service not ready")
        
        agent = await agent_service.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
        
        return agent
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute", response_model=AgentExecutionResponse)
async def execute_agent(request: AgentExecutionRequest):
    """Execute a specific agent."""
    try:
        from main import agent_service
        
        if not agent_service:
            raise HTTPException(status_code=503, detail="Agent service not ready")
        
        result = await agent_service.execute_agent(
            request.agent_id,
            request.input_data,
            request.priority,
            request.timeout
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error executing agent {request.agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/orchestrate", response_model=OrchestrationResponse)
async def orchestrate_agents(request: OrchestrationRequest):
    """
    Orchestrate multiple agents for complex tasks.
    
    This endpoint coordinates multiple agents to work together
    on complex tasks, handling dependencies and data flow automatically.
    """
    try:
        from main import agent_service
        
        if not agent_service:
            raise HTTPException(status_code=503, detail="Agent service not ready")
        
        result = await agent_service.orchestrate(
            request.task,
            request.input_data,
            request.agent_sequence,
            request.parallel
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error orchestrating agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{agent_id}/start")
async def start_agent(agent_id: str):
    """Start a specific agent."""
    try:
        from main import agent_service
        
        if not agent_service:
            raise HTTPException(status_code=503, detail="Agent service not ready")
        
        success = await agent_service.start_agent(agent_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
        
        return {"status": "started", "agent_id": agent_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{agent_id}/stop")
async def stop_agent(agent_id: str):
    """Stop a specific agent."""
    try:
        from main import agent_service
        
        if not agent_service:
            raise HTTPException(status_code=503, detail="Agent service not ready")
        
        success = await agent_service.stop_agent(agent_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
        
        return {"status": "stopped", "agent_id": agent_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orchestration/status")
async def get_orchestration_status():
    """Get current orchestration system status."""
    try:
        from main import agent_service
        
        if not agent_service:
            raise HTTPException(status_code=503, detail="Agent service not ready")
        
        status = await agent_service.get_orchestration_status()
        return status
        
    except Exception as e:
        logger.error(f"Error getting orchestration status: {e}")
        raise HTTPException(status_code=500, detail=str(e))