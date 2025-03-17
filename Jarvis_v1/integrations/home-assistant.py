import requests
import json
from typing import Dict, List, Any, Optional
from loguru import logger

from config.settings import settings


class HomeAssistantClient:
    """
    Client for Home Assistant integration.
    Provides methods to interact with Home Assistant API.
    """
    
    def __init__(self):
        self.url = settings.home_assistant.url
        self.token = settings.home_assistant.token
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        self.entities_cache = {}
        self.states_cache = {}
        
    def initialize(self) -> bool:
        """Initialize the Home Assistant client and test the connection."""
        try:
            # Test connection by getting API status
            response = requests.get(f"{self.url}/api/", headers=self.headers)
            
            if response.status_code == 200:
                logger.info("Home Assistant connection successful")
                # Refresh entities cache
                self.get_entities()
                return True
            else:
                logger.error(f"Failed to connect to Home Assistant: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error initializing Home Assistant client: {e}")
            return False
            
    def get_entities(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Get all entities from Home Assistant.
        
        Args:
            force_refresh: Force refresh of entities cache
            
        Returns:
            List of entity objects
        """
        if not force_refresh and self.entities_cache:
            return list(self.entities_cache.values())
            
        try:
            response = requests.get(f"{self.url}/api/states", headers=self.headers)
            
            if response.status_code == 200:
                entities = response.json()
                
                # Update cache
                self.entities_cache = {entity["entity_id"]: entity for entity in entities}
                self.states_cache = {entity["entity_id"]: entity["state"] for entity in entities}
                
                logger.info(f"Retrieved {len(entities)} entities from Home Assistant")
                return entities
            else:
                logger.error(f"Failed to get entities: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting entities: {e}")
            return []
            
    def find_entities(self, domain: str, name_filter: str) -> List[Dict[str, Any]]:
        """
        Find entities by domain and name filter.
        
        Args:
            domain: Entity domain (light, switch, etc.)
            name_filter: String to filter entity names
            
        Returns:
            List of matching entities
        """
        try:
            # Refresh entities if cache is empty
            if not self.entities_cache:
                self.get_entities()
                
            # Filter entities by domain and name
            matching_entities = []
            name_filter_lower = name_filter.lower()
            
            for entity_id, entity in self.entities_cache.items():
                if entity_id.startswith(f"{domain}."):
                    # Check friendly name in attributes
                    attributes = entity.get("attributes", {})
                    friendly_name = attributes.get("friendly_name", "").lower()
                    
                    # Match if name filter is empty or if it's in the friendly name or entity ID
                    if not name_filter or name_filter_lower in friendly_name or name_filter_lower in entity_id.lower():
                        matching_entities.append(entity)
            
            return matching_entities
            
        except Exception as e:
            logger.error(f"Error finding entities: {e}")
            return []
            
    def get_entity(self, entity_id: str, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        """
        Get entity by ID.
        
        Args:
            entity_id: Entity ID
            force_refresh: Force refresh of entity data
            
        Returns:
            Entity object or None if not found
        """
        if not force_refresh and entity_id in self.entities_cache:
            return self.entities_cache[entity_id]
            
        try:
            response = requests.get(f"{self.url}/api/states/{entity_id}", headers=self.headers)
            
            if response.status_code == 200:
                entity = response.json()
                
                # Update cache
                self.entities_cache[entity_id] = entity
                self.states_cache[entity_id] = entity["state"]
                
                return entity
            else:
                logger.error(f"Failed to get entity {entity_id}: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting entity {entity_id}: {e}")
            return None
            
    def get_entity_state(self, entity_id: str, force_refresh: bool = False) -> Optional[str]:
        """
        Get entity state by ID.
        
        Args:
            entity_id: Entity ID
            force_refresh: Force refresh of entity data
            
        Returns:
            Entity state or None if not found
        """
        if not force_refresh and entity_id in self.states_cache:
            return self.states_cache[entity_id]
            
        entity = self.get_entity(entity_id, force_refresh)
        if entity:
            return entity["state"]
        else:
            return None
            
    def get_entity_attributes(self, entity_id: str, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        """
        Get entity attributes by ID.
        
        Args:
            entity_id: Entity ID
            force_refresh: Force refresh of entity data
            
        Returns:
            Entity attributes or None if not found
        """
        entity = self.get_entity(entity_id, force_refresh)
        if entity:
            return entity.get("attributes", {})
        else:
            return None
            
    def get_entity_name(self, entity_id: str) -> str:
        """
        Get friendly name of entity.
        
        Args:
            entity_id: Entity ID
            
        Returns:
            Friendly name or entity ID if not found
        """
        attributes = self.get_entity_attributes(entity_id)
        if attributes and "friendly_name" in attributes:
            return attributes["friendly_name"]
        else:
            return entity_id
            
    def call_service(self, domain: str, service: str, service_data: Dict[str, Any] = None) -> bool:
        """
        Call a Home Assistant service.
        
        Args:
            domain: Service domain (light, switch, etc.)
            service: Service name (turn_on, turn_off, etc.)
            service_data: Service data including entity_id
            
        Returns:
            True if successful, False otherwise
        """
        if service_data is None:
            service_data = {}
            
        try:
            service_url = f"{self.url}/api/services/{domain}/{service}"
            response = requests.post(
                service_url,
                headers=self.headers,
                json=service_data
            )
            
            if response.status_code in [200, 201]:
                # Force refresh affected entities
                if "entity_id" in service_data:
                    entity_ids = service_data["entity_id"]
                    if isinstance(entity_ids, str):
                        entity_ids = [entity_ids]
                    
                    for entity_id in entity_ids:
                        self.get_entity(entity_id, force_refresh=True)
                        
                return True
            else:
                logger.error(f"Failed to call service {domain}.{service}: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error calling service {domain}.{service}: {e}")
            return False
            
    def get_camera_image(self, camera_entity_id: str) -> Optional[bytes]:
        """
        Get image from camera entity.
        
        Args:
            camera_entity_id: Camera entity ID
            
        Returns:
            Image data as bytes or None if failed
        """
        try:
            response = requests.get(
                f"{self.url}/api/camera_proxy/{camera_entity_id}",
                headers=self.headers
            )
            
            if response.status_code == 200:
                return response.content
            else:
                logger.error(f"Failed to get camera image: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting camera image: {e}")
            return None
