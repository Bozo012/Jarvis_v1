import threading
import signal
import time
from typing import Dict, List, Any, Optional, Callable
from loguru import logger

from core.audio_listener import AudioListener
from core.command_processor import CommandProcessor
from core.task_scheduler import TaskScheduler
from api.server import APIServer


class MicroservicesControlPlane:
    """
    Microservices Control Plane (MCP) for managing services.
    Handles starting, stopping, and communication between services.
    """
    
    def __init__(self):
        self.services = {}
        self.running = False
        self.threads = {}
        
        # Initialize services
        self.audio_listener = None
        self.command_processor = None
        self.task_scheduler = None
        self.api_server = None
        
    def initialize(self) -> bool:
        """Initialize all services."""
        try:
            logger.info("Initializing MCP...")
            
            # Initialize audio listener
            self.audio_listener = AudioListener()
            self.services["audio_listener"] = self.audio_listener
            
            # Initialize command processor
            self.command_processor = CommandProcessor()
            self.services["command_processor"] = self.command_processor
            
            # Initialize task scheduler
            self.task_scheduler = TaskScheduler()
            self.services["task_scheduler"] = self.task_scheduler
            
            # Initialize API server
            self.api_server = APIServer()
            self.services["api_server"] = self.api_server
            
            # Cross-wire services
            self.command_processor.initialize(self.audio_listener)
            
            logger.info("MCP initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize MCP: {e}")
            return False
            
    def start(self) -> bool:
        """Start all services."""
        if self.running:
            logger.warning("MCP is already running")
            return True
            
        try:
            logger.info("Starting MCP...")
            self.running = True
            
            # Set up signal handlers for graceful shutdown
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
            
            # Start API server
            api_thread = threading.Thread(target=self._run_api_server)
            api_thread.daemon = True
            api_thread.start()
            self.threads["api_server"] = api_thread
            
            # Start task scheduler
            scheduler_thread = threading.Thread(target=self._run_task_scheduler)
            scheduler_thread.daemon = True
            scheduler_thread.start()
            self.threads["task_scheduler"] = scheduler_thread
            
            # Start audio listener
            self.audio_listener.start(self.command_processor.process_command)
            
            logger.info("MCP started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start MCP: {e}")
            self.stop()
            return False
            
    def stop(self) -> bool:
        """Stop all services."""
        if not self.running:
            logger.warning("MCP is not running")
            return True
            
        try:
            logger.info("Stopping MCP...")
            self.running = False
            
            # Stop audio listener
            if self.audio_listener:
                self.audio_listener.stop()
                
            # Stop API server
            if self.api_server:
                self.api_server.stop()
                
            # Stop task scheduler
            if self.task_scheduler:
                self.task_scheduler.stop()
                
            # Wait for threads to finish
            for name, thread in self.threads.items():
                if thread.is_alive():
                    logger.info(f"Waiting for {name} thread to finish...")
                    thread.join(timeout=5.0)
                    
            # Cleanup resources
            self._cleanup()
            
            logger.info("MCP stopped successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping MCP: {e}")
            return False
            
    def _cleanup(self):
        """Clean up resources."""
        # Clean up audio listener
        if self.audio_listener:
            self.audio_listener.cleanup()
            
        # Other cleanup as needed
        
    def _run_api_server(self):
        """Run API server in a separate thread."""
        try:
            # Configure API server with callbacks
            self.api_server.set_command_callback(self.command_processor.process_command)
            
            # Start API server
            self.api_server.start()
            
        except Exception as e:
            logger.error(f"Error in API server thread: {e}")
            
    def _run_task_scheduler(self):
        """Run task scheduler in a separate thread."""
        try:
            # Configure scheduler
            self.task_scheduler.set_command_callback(self.command_processor.process_command)
            
            # Start scheduler
            self.task_scheduler.start()
            
        except Exception as e:
            logger.error(f"Error in task scheduler thread: {e}")
            
    def process_command(self, command: str) -> str:
        """
        Process a command through the command processor.
        
        Args:
            command: Command text
            
        Returns:
            Response text
        """
        if not self.command_processor:
            return "Command processor is not available"
            
        return self.command_processor.process_command(command)
        
    def _signal_handler(self, sig, frame):
        """Handle signals for graceful shutdown."""
        logger.info(f"Received signal {sig}, shutting down...")
        self.stop()
