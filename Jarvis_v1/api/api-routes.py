from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Body, Depends
from pydantic import BaseModel, Field

from core.command_processor import CommandProcessor
from core.task_scheduler import TaskScheduler
from config.settings import settings


# Define API models
class CommandRequest(BaseModel):
    command: str = Field(..., description="Command text to process")


class CommandResponse(BaseModel):
    response: str = Field(..., description="Response from command processor")


class ScheduleRequest(BaseModel):
    job_id: str = Field(..., description="Unique job identifier")
    command: str = Field(..., description="Command to execute")
    schedule: str = Field(..., description="Schedule in natural language")


class ScheduleResponse(BaseModel):
    success: bool = Field(..., description="Success status")
    message: str = Field(..., description="Status message")


class JobInfo(BaseModel):
    id: str = Field(..., description="Job identifier")
    next_run_time: Optional[str] = Field(None, description="Next run time")
    trigger: Dict[str, Any] = Field(..., description="Trigger information")


# Create routers
command_router = APIRouter(prefix="/command", tags=["Commands"])
schedule_router = APIRouter(prefix="/schedule", tags=["Scheduling"])
system_router = APIRouter(prefix="/system", tags=["System"])


# Command routes
@command_router.post("/", response_model=CommandResponse)
async def process_command(
    request: CommandRequest,
    command_processor: CommandProcessor = Depends(lambda: None)
):
    """
    Process a voice command.
    
    Args:
        request: Command request
        command_processor: Command processor dependency
        
    Returns:
        Command response
    """
    if not command_processor:
        raise HTTPException(status_code=503, detail="Command processor not available")
        
    try:
        response = command_processor.process_command(request.command)
        return CommandResponse(response=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Schedule routes
@schedule_router.post("/", response_model=ScheduleResponse)
async def create_schedule(
    request: ScheduleRequest,
    task_scheduler: TaskScheduler = Depends(lambda: None)
):
    """
    Create a scheduled task.
    
    Args:
        request: Schedule request
        task_scheduler: Task scheduler dependency
        
    Returns:
        Schedule response
    """
    if not task_scheduler:
        raise HTTPException(status_code=503, detail="Task scheduler not available")
        
    try:
        success = task_scheduler.parse_natural_language_schedule(
            request.job_id,
            request.command,
            request.schedule
        )
        
        if success:
            return ScheduleResponse(
                success=True,
                message=f"Successfully scheduled task {request.job_id}"
            )
        else:
            return ScheduleResponse(
                success=False,
                message=f"Failed to schedule task {request.job_id}"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@schedule_router.get("/", response_model=List[JobInfo])
async def list_schedules(
    task_scheduler: TaskScheduler = Depends(lambda: None)
):
    """
    List all scheduled tasks.
    
    Args:
        task_scheduler: Task scheduler dependency
        
    Returns:
        List of job information
    """
    if not task_scheduler:
        raise HTTPException(status_code=503, detail="Task scheduler not available")
        
    try:
        jobs = task_scheduler.get_jobs()
        return jobs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@schedule_router.delete("/{job_id}", response_model=ScheduleResponse)
async def delete_schedule(
    job_id: str,
    task_scheduler: TaskScheduler = Depends(lambda: None)
):
    """
    Delete a scheduled task.
    
    Args:
        job_id: Job identifier
        task_scheduler: Task scheduler dependency
        
    Returns:
        Schedule response
    """
    if not task_scheduler:
        raise HTTPException(status_code=503, detail="Task scheduler not available")
        
    try:
        success = task_scheduler.remove_job(job_id)
        
        if success:
            return ScheduleResponse(
                success=True,
                message=f"Successfully removed task {job_id}"
            )
        else:
            return ScheduleResponse(
                success=False,
                message=f"Failed to remove task {job_id}"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# System routes
@system_router.get("/status")
async def get_system_status():
    """
    Get system status.
    
    Returns:
        System status information
    """
    return {
        "status": "running",
        "version": "1.0.0",
        "debug": settings.general.debug
    }
