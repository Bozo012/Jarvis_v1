import threading
import uvicorn
from typing import Dict, List, Any, Optional, Callable
from fastapi import FastAPI, HTTPException, Body, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from loguru import logger

from config.settings import settings


# API models
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


class APIServer:
    """
    FastAPI server for REST API.
    Provides endpoints for controlling the system.
    """
    
    def __init__(self):
        self.app = FastAPI(title="Local AI Assistant API", version="1.0.0")
        self.host = settings.general.host
        self.port = settings.general.port
        self.command_callback = None
        self.server = None
        self.running = False
        
        # Set up CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Register routes
        self._setup_routes()
        
    def set_command_callback(self, callback: Callable[[str], str]):
        """
        Set callback function for processing commands.
        
        Args:
            callback: Function to call with command text
        """
        self.command_callback = callback
        
    def _setup_routes(self):
        """Set up API routes."""
        
        @self.app.get("/")
        async def root():
            return {"message": "Local AI Assistant API"}
            
        @self.app.get("/health")
        async def health():
            return {"status": "ok"}
            
        @self.app.post("/command", response_model=CommandResponse)
        async def process_command(request: CommandRequest):
            if not self.command_callback:
                raise HTTPException(status_code=503, detail="Command processor not available")
                
            try:
                response = self.command_callback(request.command)
                return CommandResponse(response=response)
            except Exception as e:
                logger.error(f"Error processing command: {e}")
                raise HTTPException(status_code=500, detail=str(e))
                
        # Additional routes will be added for task scheduling, configuration, etc.
        
    def start(self):
        """Start the API server."""
        if self.running:
            logger.warning("API server is already running")
            return
            
        try:
            # Create and start server in a separate thread
            self.server_thread = threading.Thread(target=self._run_server)
            self.server_thread.daemon = True
            self.server_thread.start()
            
            logger.info(f"API server started at http://{self.host}:{self.port}")
            self.running = True
            
        except Exception as e:
            logger.error(f"Error starting API server: {e}")
            
    def _run_server(self):
        """Run the uvicorn server."""
        try:
            uvicorn.run(
                self.app,
                host=self.host,
                port=self.port,
                log_level="info"
            )
        except Exception as e:
            logger.error(f"Error in API server: {e}")
            self.running = False
            
    def stop(self):
        """Stop the API server."""
        if not self.running:
            logger.warning("API server is not running")
            return
            
        logger.info("Stopping API server")
        self.running = False
        # Note: There's no clean way to stop uvicorn programmatically
        # This will be handled by the MCP terminating the thread
