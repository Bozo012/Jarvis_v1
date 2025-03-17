import re
import json
import importlib
from typing import Dict, List, Any, Optional, Callable, Tuple
from loguru import logger

from core.llm import LLMService
from core.audio_listener import AudioListener
from integrations.home_assistant import HomeAssistantClient
from integrations.media_control import MediaController


class CommandProcessor:
    """
    Command processor service that interprets and executes user commands.
    Uses the LLM to understand user intents and routes commands to appropriate integrations.
    """
    
    def __init__(self):
        self.llm = LLMService()
        self.audio_listener = None
        self.home_assistant = None
        self.media_controller = None
        
        # Command handlers keyed by intent
        self.handlers = {}
        self.integrations = {}
        
    def initialize(self, audio_listener: Optional[AudioListener] = None) -> bool:
        """
        Initialize the command processor and integrations.
        
        Args:
            audio_listener: Audio listener instance for TTS responses
        """
        try:
            # Set audio listener for responses
            self.audio_listener = audio_listener
            
            # Initialize integrations
            self._initialize_integrations()
            
            # Register command handlers
            self._register_handlers()
            
            logger.info("Command processor initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize command processor: {e}")
            return False
            
    def _initialize_integrations(self):
        """Initialize integrations."""
        try:
            # Initialize Home Assistant client
            self.home_assistant = HomeAssistantClient()
            self.home_assistant.initialize()
            self.integrations["home_assistant"] = self.home_assistant
            
            # Initialize Media Controller
            self.media_controller = MediaController()
            self.media_controller.initialize()
            self.integrations["media"] = self.media_controller
            
            # Initialize other integrations as needed
            # ...
            
        except Exception as e:
            logger.error(f"Error initializing integrations: {e}")
            
    def _register_handlers(self):
        """Register command handlers for different intents."""
        # Home automation handlers
        self.handlers["light_control"] = self._handle_light_control
        self.handlers["climate_control"] = self._handle_climate_control
        self.handlers["switch_control"] = self._handle_switch_control
        self.handlers["device_status"] = self._handle_device_status
        
        # Media control handlers
        self.handlers["play_music"] = self._handle_play_music
        self.handlers["media_control"] = self._handle_media_control
        self.handlers["volume_control"] = self._handle_volume_control
        
        # TV control handlers
        self.handlers["tv_control"] = self._handle_tv_control
        
        # Information handlers
        self.handlers["weather"] = self._handle_weather
        self.handlers["time"] = self._handle_time
        self.handlers["general_query"] = self._handle_general_query
        
        # System control handlers
        self.handlers["system_control"] = self._handle_system_control
        
    def _parse_command(self, command: str) -> Tuple[str, Dict[str, Any]]:
        """
        Parse command to determine intent and extract parameters using LLM.
        
        Args:
            command: User command text
            
        Returns:
            Tuple containing intent and parameters dictionary
        """
        try:
            # Default system prompt to guide the LLM in parsing commands
            system_prompt = """
            You are an assistant that helps parse voice commands for a home assistant system.
            Extract the intent and parameters from the user's command.
            Return a JSON object with "intent" and "parameters" keys.
            
            Available intents:
            - light_control: Control lights (on/off/brightness/color)
            - climate_control: Control temperature, fans, etc.
            - switch_control: Control switches and outlets
            - device_status: Get status of devices
            - play_music: Play music or audio
            - media_control: Control media playback (pause/resume/next/previous)
            - volume_control: Adjust volume
            - tv_control: Control TV (on/off/channel/input)
            - weather: Get weather information
            - time: Get current time or set timers/alarms
            - general_query: Answer general questions
            - system_control: Control the assistant system
            
            Example formats:
            {"intent": "light_control", "parameters": {"action": "turn_on", "device": "living room lights", "brightness": 80}}
            {"intent": "play_music", "parameters": {"artist": "Taylor Swift", "source": "spotify"}}
            """
            
            # Prompt for the LLM
            prompt = f"Parse this voice command: '{command}'\nExtract the intent and parameters as JSON."
            
            # Get response from LLM
            response = self.llm.generate(prompt, system_prompt=system_prompt)
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                parsed_json = json.loads(json_match.group(0))
                intent = parsed_json.get("intent", "general_query")
                parameters = parsed_json.get("parameters", {})
                return intent, parameters
            else:
                logger.warning(f"Could not extract JSON from LLM response: {response}")
                return "general_query", {"query": command}
                
        except Exception as e:
            logger.error(f"Error parsing command: {e}")
            return "general_query", {"query": command}
            
    def process_command(self, command: str) -> str:
        """
        Process a user command, determine intent, and execute appropriate handler.
        
        Args:
            command: User command text
            
        Returns:
            Response message
        """
        try:
            logger.info(f"Processing command: {command}")
            
            # Parse command to determine intent and parameters
            intent, parameters = self._parse_command(command)
            logger.info(f"Detected intent: {intent}, parameters: {parameters}")
            
            # Execute appropriate handler
            if intent in self.handlers:
                response = self.handlers[intent](parameters)
            else:
                # Fallback to general query
                response = self._handle_general_query({"query": command})
                
            # Speak response if audio listener is available
            if self.audio_listener:
                self.audio_listener.say(response)
                
            return response
            
        except Exception as e:
            logger.error(f"Error processing command: {e}")
            error_msg = "Sorry, I encountered an error while processing your command."
            
            if self.audio_listener:
                self.audio_listener.say(error_msg)
                
            return error_msg
            
    # Command handlers
    def _handle_light_control(self, parameters: Dict[str, Any]) -> str:
        """Handle light control commands."""
        if not self.home_assistant:
            return "Home Assistant integration is not available"
            
        try:
            action = parameters.get("action", "")
            device = parameters.get("device", "")
            brightness = parameters.get("brightness")
            color = parameters.get("color")
            
            if not device:
                return "Please specify which light you want to control"
                
            # Find matching light entities
            lights = self.home_assistant.find_entities("light", device)
            if not lights:
                return f"I couldn't find any lights matching '{device}'"
                
            results = []
            for light in lights:
                if action in ["on", "turn_on"]:
                    # Turn on light with optional brightness/color
                    attributes = {}
                    if brightness is not None:
                        attributes["brightness_pct"] = brightness
                    if color:
                        attributes["color_name"] = color
                        
                    success = self.home_assistant.call_service(
                        "light", "turn_on", 
                        {"entity_id": light["entity_id"], **attributes}
                    )
                    results.append((light["entity_id"], success))
                    
                elif action in ["off", "turn_off"]:
                    # Turn off light
                    success = self.home_assistant.call_service(
                        "light", "turn_off", 
                        {"entity_id": light["entity_id"]}
                    )
                    results.append((light["entity_id"], success))
                    
                elif action in ["toggle"]:
                    # Toggle light
                    success = self.home_assistant.call_service(
                        "light", "toggle", 
                        {"entity_id": light["entity_id"]}
                    )
                    results.append((light["entity_id"], success))
            
            # Generate response based on results
            if all(success for _, success in results):
                friendly_names = [self.home_assistant.get_entity_name(entity_id) for entity_id, _ in results]
                names_str = ", ".join(friendly_names[:-1]) + " and " + friendly_names[-1] if len(friendly_names) > 1 else friendly_names[0]
                
                if action in ["on", "turn_on"]:
                    return f"Turned on {names_str}"
                elif action in ["off", "turn_off"]:
                    return f"Turned off {names_str}"
                elif action in ["toggle"]:
                    return f"Toggled {names_str}"
            else:
                return f"I had trouble controlling some of the lights"
                
            return "Light control command completed"
            
        except Exception as e:
            logger.error(f"Error handling light control: {e}")
            return "Sorry, I had trouble controlling the lights"
            
    def _handle_climate_control(self, parameters: Dict[str, Any]) -> str:
        """Handle climate control commands."""
        if not self.home_assistant:
            return "Home Assistant integration is not available"
            
        try:
            action = parameters.get("action", "")
            device = parameters.get("device", "")
            temperature = parameters.get("temperature")
            mode = parameters.get("mode")
            
            if not device:
                return "Please specify which climate device you want to control"
                
            # Find matching climate entities
            climate_devices = self.home_assistant.find_entities("climate", device)
            if not climate_devices:
                return f"I couldn't find any climate devices matching '{device}'"
                
            results = []
            for climate in climate_devices:
                if action in ["set_temperature"] and temperature is not None:
                    # Set temperature
                    success = self.home_assistant.call_service(
                        "climate", "set_temperature", 
                        {"entity_id": climate["entity_id"], "temperature": temperature}
                    )
                    results.append((climate["entity_id"], success))
                    
                elif action in ["set_mode"] and mode:
                    # Set mode (heat, cool, auto, off)
                    success = self.home_assistant.call_service(
                        "climate", "set_hvac_mode", 
                        {"entity_id": climate["entity_id"], "hvac_mode": mode}
                    )
                    results.append((climate["entity_id"], success))
                    
                elif action in ["off", "turn_off"]:
                    # Turn off climate device
                    success = self.home_assistant.call_service(
                        "climate", "set_hvac_mode", 
                        {"entity_id": climate["entity_id"], "hvac_mode": "off"}
                    )
                    results.append((climate["entity_id"], success))
            
            # Generate response based on results
            if all(success for _, success in results):
                friendly_names = [self.home_assistant.get_entity_name(entity_id) for entity_id, _ in results]
                names_str = ", ".join(friendly_names[:-1]) + " and " + friendly_names[-1] if len(friendly_names) > 1 else friendly_names[0]
                
                if action in ["set_temperature"]:
                    return f"Set temperature to {temperature} degrees for {names_str}"
                elif action in ["set_mode"]:
                    return f"Set {names_str} to {mode} mode"
                elif action in ["off", "turn_off"]:
                    return f"Turned off {names_str}"
            else:
                return f"I had trouble controlling the climate devices"
                
            return "Climate control command completed"
            
        except Exception as e:
            logger.error(f"Error handling climate control: {e}")
            return "Sorry, I had trouble controlling the climate devices"
            
    def _handle_switch_control(self, parameters: Dict[str, Any]) -> str:
        """Handle switch control commands."""
        if not self.home_assistant:
            return "Home Assistant integration is not available"
            
        try:
            action = parameters.get("action", "")
            device = parameters.get("device", "")
            
            if not device:
                return "Please specify which switch you want to control"
                
            # Find matching switch entities
            switches = self.home_assistant.find_entities("switch", device)
            if not switches:
                return f"I couldn't find any switches matching '{device}'"
                
            results = []
            for switch in switches:
                if action in ["on", "turn_on"]:
                    # Turn on switch
                    success = self.home_assistant.call_service(
                        "switch", "turn_on", 
                        {"entity_id": switch["entity_id"]}
                    )
                    results.append((switch["entity_id"], success))
                    
                elif action in ["off", "turn_off"]:
                    # Turn off switch
                    success = self.home_assistant.call_service(
                        "switch", "turn_off", 
                        {"entity_id": switch["entity_id"]}
                    )
                    results.append((switch["entity_id"], success))
                    
                elif action in ["toggle"]:
                    # Toggle switch
                    success = self.home_assistant.call_service(
                        "switch", "toggle", 
                        {"entity_id": switch["entity_id"]}
                    )
                    results.append((switch["entity_id"], success))
            
            # Generate response based on results
            if all(success for _, success in results):
                friendly_names = [self.home_assistant.get_entity_name(entity_id) for entity_id, _ in results]
                names_str = ", ".join(friendly_names[:-1]) + " and " + friendly_names[-1] if len(friendly_names) > 1 else friendly_names[0]
                
                if action in ["on", "turn_on"]:
                    return f"Turned on {names_str}"
                elif action in ["off", "turn_off"]:
                    return f"Turned off {names_str}"
                elif action in ["toggle"]:
                    return f"Toggled {names_str}"
            else:
                return f"I had trouble controlling some of the switches"
                
            return "Switch control command completed"
            
        except Exception as e:
            logger.error(f"Error handling switch control: {e}")
            return "Sorry, I had trouble controlling the switches"
            
    def _handle_device_status(self, parameters: Dict[str, Any]) -> str:
        """Handle device status queries."""
        if not self.home_assistant:
            return "Home Assistant integration is not available"
            
        try:
            device = parameters.get("device", "")
            
            if not device:
                return "Please specify which device you want to check"
                
            # Try to find the device across different entity types
            entity_types = ["light", "switch", "climate", "sensor", "binary_sensor"]
            found_entities = []
            
            for entity_type in entity_types:
                entities = self.home_assistant.find_entities(entity_type, device)
                found_entities.extend(entities)
                
            if not found_entities:
                return f"I couldn't find any devices matching '{device}'"
                
            # Generate status report for found entities
            status_lines = []
            for entity in found_entities:
                entity_id = entity["entity_id"]
                entity_name = self.home_assistant.get_entity_name(entity_id)
                state = self.home_assistant.get_entity_state(entity_id)
                
                if "light." in entity_id or "switch." in entity_id:
                    status = "on" if state == "on" else "off"
                    status_lines.append(f"{entity_name} is {status}")
                    
                elif "climate." in entity_id:
                    if state == "off":
                        status_lines.append(f"{entity_name} is off")
                    else:
                        attributes = self.home_assistant.get_entity_attributes(entity_id)
                        current_temp = attributes.get("current_temperature", "unknown")
                        target_temp = attributes.get("temperature", "unknown")
                        status_lines.append(f"{entity_name} is {state}, current temperature: {current_temp}°, target: {target_temp}°")
                        
                elif "sensor." in entity_id:
                    attributes = self.home_assistant.get_entity_attributes(entity_id)
                    unit = attributes.get("unit_of_measurement", "")
                    status_lines.append(f"{entity_name}: {state}{unit}")
                    
                elif "binary_sensor." in entity_id:
                    status = "on" if state == "on" else "off"
                    status_lines.append(f"{entity_name} is {status}")
            
            if status_lines:
                return "\n".join(status_lines)
            else:
                return f"I couldn't get the status of {device}"
                
        except Exception as e:
            logger.error(f"Error handling device status: {e}")
            return "Sorry, I had trouble getting the device status"
            
    def _handle_play_music(self, parameters: Dict[str, Any]) -> str:
        """Handle music playback commands."""
        if not self.media_controller:
            return "Media controller is not available"
            
        try:
            source = parameters.get("source", "").lower()
            artist = parameters.get("artist", "")
            album = parameters.get("album", "")
            track = parameters.get("track", "")
            playlist = parameters.get("playlist", "")
            genre = parameters.get("genre", "")
            
            # Determine what to play
            if source == "spotify":
                if artist and track:
                    result = self.media_controller.play_spotify(artist=artist, track=track)
                elif artist and album:
                    result = self.media_controller.play_spotify(artist=artist, album=album)
                elif artist:
                    result = self.media_controller.play_spotify(artist=artist)
                elif playlist:
                    result = self.media_controller.play_spotify(playlist=playlist)
                elif genre:
                    result = self.media_controller.play_spotify(genre=genre)
                else:
                    return "Please specify what you'd like to play on Spotify"
                    
                if result:
                    if track:
                        return f"Playing {track} by {artist} on Spotify"
                    elif album:
                        return f"Playing album {album} by {artist} on Spotify"
                    elif artist:
                        return f"Playing music by {artist} on Spotify"
                    elif playlist:
                        return f"Playing playlist {playlist} on Spotify"
                    elif genre:
                        return f"Playing {genre} music on Spotify"
                else:
                    return f"Sorry, I couldn't play that on Spotify"
            
            elif source == "mpd" or not source:
                if artist and track:
                    result = self.media_controller.play_mpd(artist=artist, title=track)
                elif artist and album:
                    result = self.media_controller.play_mpd(artist=artist, album=album)
                elif artist:
                    result = self.media_controller.play_mpd(artist=artist)
                elif album:
                    result = self.media_controller.play_mpd(album=album)
                elif track:
                    result = self.media_controller.play_mpd(title=track)
                elif genre:
                    result = self.media_controller.play_mpd(genre=genre)
                else:
                    # Just play something
                    result = self.media_controller.play_mpd()
                    
                if result:
                    if track and artist:
                        return f"Playing {track} by {artist}"
                    elif album and artist:
                        return f"Playing album {album} by {artist}"
                    elif artist:
                        return f"Playing music by {artist}"
                    elif track:
                        return f"Playing {track}"
                    elif album:
                        return f"Playing album {album}"
                    elif genre:
                        return f"Playing {genre} music"
                    else:
                        return "Playing music"
                else:
                    return "Sorry, I couldn't play that music"
            
            else:
                return f"Sorry, I don't support playing music from {source}"
                
        except Exception as e:
            logger.error(f"Error handling play music: {e}")
            return "Sorry, I had trouble playing the music"
            
    def _handle_media_control(self, parameters: Dict[str, Any]) -> str:
        """Handle media control commands (pause, resume, next, etc.)."""
        if not self.media_controller:
            return "Media controller is not available"
            
        try:
            action = parameters.get("action", "")
            
            if action in ["pause", "stop"]:
                result = self.media_controller.pause()
                return "Paused" if result else "Failed to pause"
                
            elif action in ["play", "resume"]:
                result = self.media_controller.play()
                return "Resumed playback" if result else "Failed to resume playback"
                
            elif action in ["next", "skip"]:
                result = self.media_controller.next()
                return "Skipped to next track" if result else "Failed to skip to next track"
                
            elif action in ["previous", "back"]:
                result = self.media_controller.previous()
                return "Went back to previous track" if result else "Failed to go back"
                
            elif action in ["shuffle", "shuffle_on"]:
                result = self.media_controller.set_shuffle(True)
                return "Shuffle mode enabled" if result else "Failed to enable shuffle mode"
                
            elif action in ["shuffle_off"]:
                result = self.media_controller.set_shuffle(False)
                return "Shuffle mode disabled" if result else "Failed to disable shuffle mode"
                
            elif action in ["repeat", "repeat_on"]:
                result = self.media_controller.set_repeat(True)
                return "Repeat mode enabled" if result else "Failed to enable repeat mode"
                
            elif action in ["repeat_off"]:
                result = self.media_controller.set_repeat(False)
                return "Repeat mode disabled" if result else "Failed to disable repeat mode"
                
            else:
                return f"Unknown media control action: {action}"
                
        except Exception as e:
            logger.error(f"Error handling media control: {e}")
            return "Sorry, I had trouble controlling the media"
            
    def _handle_volume_control(self, parameters: Dict[str, Any]) -> str:
        """Handle volume control commands."""
        if not self.media_controller:
            return "Media controller is not available"
            
        try:
            action = parameters.get("action", "")
            level = parameters.get("level")
            step = parameters.get("step", 10)  # Default step is 10%
            
            if action in ["set", "set_volume"] and level is not None:
                result = self.media_controller.set_volume(level)
                return f"Volume set to {level}%" if result else "Failed to set volume"
                
            elif action in ["up", "increase"]:
                current = self.media_controller.get_volume()
                if current is not None:
                    new_level = min(100, current + step)
                    result = self.media_controller.set_volume(new_level)
                    return f"Volume increased to {new_level}%" if result else "Failed to increase volume"
                else:
                    return "Failed to get current volume"
                    
            elif action in ["down", "decrease"]:
                current = self.media_controller.get_volume()
                if current is not None:
                    new_level = max(0, current - step)
                    result = self.media_controller.set_volume(new_level)
                    return f"Volume decreased to {new_level}%" if result else "Failed to decrease volume"
                else:
                    return "Failed to get current volume"
                    
            elif action in ["mute", "mute_on"]:
                result = self.media_controller.set_mute(True)
                return "Muted" if result else "Failed to mute"
                
            elif action in ["unmute", "mute_off"]:
                result = self.media_controller.set_mute(False)
                return "Unmuted" if result else "Failed to unmute"
                
            else:
                return f"Unknown volume control action: {action}"
                
        except Exception as e:
            logger.error(f"Error handling volume control: {e}")
            return "Sorry, I had trouble controlling the volume"
            
    def _handle_tv_control(self, parameters: Dict[str, Any]) -> str:
        """Handle TV control commands."""
        try:
            # This will be implemented when we add TV integration modules
            return "TV control is not implemented yet"
            
        except Exception as e:
            logger.error(f"Error handling TV control: {e}")
            return "Sorry, I had trouble controlling the TV"
            
    def _handle_weather(self, parameters: Dict[str, Any]) -> str:
        """Handle weather queries."""
        if not self.home_assistant:
            return "Home Assistant integration is not available"
            
        try:
            # Find weather entities in Home Assistant
            weather_entities = self.home_assistant.find_entities("weather", "")
            
            if not weather_entities:
                return "I couldn't find any weather information"
                
            # Get current conditions from the first weather entity
            entity_id = weather_entities[0]["entity_id"]
            state = self.home_assistant.get_entity_state(entity_id)
            attributes = self.home_assistant.get_entity_attributes(entity_id)
            
            if not attributes:
                return "I couldn't get the weather information"
                
            temperature = attributes.get("temperature")
            humidity = attributes.get("humidity")
            pressure = attributes.get("pressure")
            wind_speed = attributes.get("wind_speed")
            wind_bearing = attributes.get("wind_bearing")
            forecast = attributes.get("forecast", [])
            
            # Build response
            response = f"Current weather: {state}"
            
            if temperature is not None:
                response += f", temperature: {temperature}°"
                
            if humidity is not None:
                response += f", humidity: {humidity}%"
                
            if wind_speed is not None:
                response += f", wind: {wind_speed}"
                
            # Add forecast if available
            if forecast and len(forecast) > 0:
                tomorrow = forecast[0]
                temp_low = tomorrow.get("temperature_low")
                temp_high = tomorrow.get("temperature")
                condition = tomorrow.get("condition")
                
                response += f"\nTomorrow: {condition}"
                
                if temp_low is not None and temp_high is not None:
                    response += f", {temp_low}° to {temp_high}°"
                elif temp_high is not None:
                    response += f", high of {temp_high}°"
                    
            return response
            
        except Exception as e:
            logger.error(f"Error handling weather query: {e}")
            return "Sorry, I couldn't get the weather information"
            
    def _handle_time(self, parameters: Dict[str, Any]) -> str:
        """Handle time-related queries."""
        from datetime import datetime
        
        try:
            action = parameters.get("action", "get_time")
            
            if action in ["get_time", "current_time"]:
                now = datetime.now()
                return f"The current time is {now.strftime('%I:%M %p')}"
                
            elif action in ["get_date", "current_date"]:
                now = datetime.now()
                return f"Today is {now.strftime('%A, %B %d, %Y')}"
                
            elif action in ["get_datetime", "current_datetime"]:
                now = datetime.now()
                return f"It's {now.strftime('%I:%M %p')} on {now.strftime('%A, %B %d, %Y')}"
                
            else:
                return f"Unknown time action: {action}"
                
        except Exception as e:
            logger.error(f"Error handling time query: {e}")
            return "Sorry, I couldn't get the time information"
            
    def _handle_general_query(self, parameters: Dict[str, Any]) -> str:
        """Handle general questions using the LLM."""
        try:
            query = parameters.get("query", "")
            
            if not query:
                return "I'm not sure what you're asking"
                
            # Use the LLM to answer general questions
            system_prompt = """
            You are a helpful home assistant AI. Answer the user's question concisely and accurately.
            If you don't know the answer, just say so without making up information.
            Keep responses brief but informative.
            """
            
            response = self.llm.generate(query, system_prompt=system_prompt, max_tokens=200)
            return response
            
        except Exception as e:
            logger.error(f"Error handling general query: {e}")
            return "Sorry, I couldn't answer that question"
            
    def _handle_system_control(self, parameters: Dict[str, Any]) -> str:
        """Handle system control commands."""
        try:
            action = parameters.get("action", "")
            
            if action in ["stop", "shutdown", "exit"]:
                # This will be handled by the main application
                return "SYSTEM_COMMAND:SHUTDOWN"
                
            elif action in ["restart"]:
                return "SYSTEM_COMMAND:RESTART"
                
            elif action in ["mute", "mute_on"]:
                return "SYSTEM_COMMAND:MUTE"
                
            elif action in ["unmute", "mute_off"]:
                return "SYSTEM_COMMAND:UNMUTE"
                
            else:
                return f"Unknown system command: {action}"
                
        except Exception as e:
            logger.error(f"Error handling system control: {e}")
            return "Sorry, I couldn't process that system command"
