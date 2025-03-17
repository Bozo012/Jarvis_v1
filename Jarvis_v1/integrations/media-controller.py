import mpd
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from typing import Dict, List, Any, Optional, Union
from loguru import logger

from config.settings import settings


class MediaController:
    """
    Media controller for MPD and Spotify.
    Provides methods to control music playback.
    """
    
    def __init__(self):
        self.mpd_client = None
        self.spotify_client = None
        self.mpd_host = settings.media.mpd_host
        self.mpd_port = settings.media.mpd_port
        self.spotify_client_id = settings.media.spotify_client_id
        self.spotify_client_secret = settings.media.spotify_client_secret
        self.spotify_redirect_uri = settings.media.spotify_redirect_uri
        
    def initialize(self) -> bool:
        """Initialize media clients."""
        success = True
        
        # Initialize MPD client
        if self.mpd_host and self.mpd_port:
            try:
                self.mpd_client = mpd.MPDClient()
                self.mpd_client.connect(self.mpd_host, self.mpd_port)
                logger.info(f"Connected to MPD server at {self.mpd_host}:{self.mpd_port}")
            except Exception as e:
                logger.error(f"Failed to connect to MPD server: {e}")
                self.mpd_client = None
                success = False
                
        # Initialize Spotify client
        if self.spotify_client_id and self.spotify_client_secret and self.spotify_redirect_uri:
            try:
                auth_manager = SpotifyOAuth(
                    client_id=self.spotify_client_id,
                    client_secret=self.spotify_client_secret,
                    redirect_uri=self.spotify_redirect_uri,
                    scope="user-read-playback-state,user-modify-playback-state"
                )
                self.spotify_client = spotipy.Spotify(auth_manager=auth_manager)
                logger.info("Spotify client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Spotify client: {e}")
                self.spotify_client = None
                success = False
                
        return success
    
    # MPD control methods
    def connect_mpd(self) -> bool:
        """Connect or reconnect to MPD server."""
        if not self.mpd_host or not self.mpd_port:
            return False
            
        try:
            if self.mpd_client:
                try:
                    self.mpd_client.ping()  # Check if connection is still alive
                    return True
                except Exception:
                    # Connection lost, reconnect
                    self.mpd_client = mpd.MPDClient()
                    
            # Connect to MPD
            self.mpd_client.connect(self.mpd_host, self.mpd_port)
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to MPD server: {e}")
            self.mpd_client = None
            return False
            
    def play_mpd(self, artist: str = None, album: str = None, title: str = None, 
                genre: str = None, playlist: str = None) -> bool:
        """
        Play music on MPD server.
        
        Args:
            artist: Artist name to filter
            album: Album name to filter
            title: Track title to filter
            genre: Genre to filter
            playlist: Playlist name to play
            
        Returns:
            True if successful, False otherwise
        """
        if not self.connect_mpd():
            return False
            
        try:
            # Clear current playlist
            self.mpd_client.clear()
            
            if playlist:
                # Play specific playlist
                playlists = self.mpd_client.listplaylists()
                playlist_names = [p["playlist"] for p in playlists]
                
                if playlist in playlist_names:
                    self.mpd_client.load(playlist)
                else:
                    # Try partial match
                    matches = [p for p in playlist_names if playlist.lower() in p.lower()]
                    if matches:
                        self.mpd_client.load(matches[0])
                    else:
                        logger.warning(f"Playlist '{playlist}' not found")
                        return False
                        
            else:
                # Build search query
                search_terms = {}
                if artist:
                    search_terms["artist"] = artist
                if album:
                    search_terms["album"] = album
                if title:
                    search_terms["title"] = title
                if genre:
                    search_terms["genre"] = genre
                    
                if not search_terms:
                    # If no search terms, add some random tracks
                    self.mpd_client.add("")
                else:
                    # Perform search and add results to playlist
                    results = self.mpd_client.search(**search_terms)
                    
                    if not results:
                        logger.warning(f"No results found for search: {search_terms}")
                        return False
                        
                    for song in results:
                        self.mpd_client.add(song["file"])
                        
            # Start playback
            self.mpd_client.play()
            return True
            
        except Exception as e:
            logger.error(f"Error playing music on MPD: {e}")
            return False
            
    # Spotify control methods
    def play_spotify(self, artist: str = None, album: str = None, track: str = None,
                   playlist: str = None, genre: str = None) -> bool:
        """
        Play music on Spotify.
        
        Args:
            artist: Artist name to search
            album: Album name to search
            track: Track name to search
            playlist: Playlist to search
            genre: Genre to search
            
        Returns:
            True if successful, False otherwise
        """
        if not self.spotify_client:
            return False
            
        try:
            # Get available devices
            devices = self.spotify_client.devices()
            if not devices or not devices.get("devices"):
                logger.warning("No Spotify devices available")
                return False
                
            # Use the first active device or the first device if none are active
            active_devices = [d for d in devices["devices"] if d["is_active"]]
            target_device = active_devices[0] if active_devices else devices["devices"][0]
            device_id = target_device["id"]
            
            if artist and track:
                # Search for specific track
                query = f"artist:{artist} track:{track}"
                results = self.spotify_client.search(query, type="track", limit=1)
                
                if results and results["tracks"]["items"]:
                    track_uri = results["tracks"]["items"][0]["uri"]
                    self.spotify_client.start_playback(device_id=device_id, uris=[track_uri])
                    return True
                    
            elif artist and album:
                # Search for album
                query = f"artist:{artist} album:{album}"
                results = self.spotify_client.search(query, type="album", limit=1)
                
                if results and results["albums"]["items"]:
                    album_uri = results["albums"]["items"][0]["uri"]
                    self.spotify_client.start_playback(device_id=device_id, context_uri=album_uri)
                    return True
                    
            elif artist:
                # Search for artist
                results = self.spotify_client.search(artist, type="artist", limit=1)
                
                if results and results["artists"]["items"]:
                    artist_uri = results["artists"]["items"][0]["uri"]
                    self.spotify_client.start_playback(device_id=device_id, context_uri=artist_uri)
                    return True
                    
            elif playlist:
                # Search for playlist
                results = self.spotify_client.search(playlist, type="playlist", limit=1)
                
                if results and results["playlists"]["items"]:
                    playlist_uri = results["playlists"]["items"][0]["uri"]
                    self.spotify_client.start_playback(device_id=device_id, context_uri=playlist_uri)
                    return True
                    
            elif genre:
                # Search for genre playlist
                results = self.spotify_client.search(f"genre:{genre}", type="playlist", limit=1)
                
                if results and results["playlists"]["items"]:
                    playlist_uri = results["playlists"]["items"][0]["uri"]
                    self.spotify_client.start_playback(device_id=device_id, context_uri=playlist_uri)
                    return True
                    
            logger.warning(f"No Spotify results found for query")
            return False
            
        except Exception as e:
            logger.error(f"Error playing music on Spotify: {e}")
            return False
            
    # Common control methods that work with either player
    def pause(self) -> bool:
        """Pause playback."""
        if self.mpd_client:
            try:
                self.connect_mpd()
                self.mpd_client.pause(1)
                return True
            except Exception as e:
                logger.error(f"Error pausing MPD: {e}")
                
        if self.spotify_client:
            try:
                self.spotify_client.pause_playback()
                return True
            except Exception as e:
                logger.error(f"Error pausing Spotify: {e}")
                
        return False
        
    def play(self) -> bool:
        """Resume playback."""
        if self.mpd_client:
            try:
                self.connect_mpd()
                self.mpd_client.pause(0)  # Un-pause
                return True
            except Exception as e:
                logger.error(f"Error resuming MPD: {e}")
                
        if self.spotify_client:
            try:
                self.spotify_client.start_playback()
                return True
            except Exception as e:
                logger.error(f"Error resuming Spotify: {e}")
                
        return False
        
    def next(self) -> bool:
        """Skip to next track."""
        if self.mpd_client:
            try:
                self.connect_mpd()
                self.mpd_client.next()
                return True
            except Exception as e:
                logger.error(f"Error skipping to next track on MPD: {e}")
                
        if self.spotify_client:
            try:
                self.spotify_client.next_track()
                return True
            except Exception as e:
                logger.error(f"Error skipping to next track on Spotify: {e}")
                
        return False
        
    def previous(self) -> bool:
        """Go to previous track."""
        if self.mpd_client:
            try:
                self.connect_mpd()
                self.mpd_client.previous()
                return True
            except Exception as e:
                logger.error(f"Error going to previous track on MPD: {e}")
                
        if self.spotify_client:
            try:
                self.spotify_client.previous_track()
                return True
            except Exception as e:
                logger.error(f"Error going to previous track on Spotify: {e}")
                
        return False
        
    def get_volume(self) -> Optional[int]:
        """Get current volume level (0-100)."""
        if self.mpd_client:
            try:
                self.connect_mpd()
                status = self.mpd_client.status()
                if "volume" in status:
                    return int(status["volume"])
            except Exception as e:
                logger.error(f"Error getting MPD volume: {e}")
                
        if self.spotify_client:
            try:
                playback = self.spotify_client.current_playback()
                if playback and "device" in playback:
                    return playback["device"]["volume_percent"]
            except Exception as e:
                logger.error(f"Error getting Spotify volume: {e}")
                
        return None
        
    def set_volume(self, level: int) -> bool:
        """
        Set volume level (0-100).
        
        Args:
            level: Volume level (0-100)
            
        Returns:
            True if successful, False otherwise
        """
        # Ensure level is within valid range
        level = max(0, min(100, level))
        
        if self.mpd_client:
            try:
                self.connect_mpd()
                self.mpd_client.setvol(level)
                return True
            except Exception as e:
                logger.error(f"Error setting MPD volume: {e}")
                
        if self.spotify_client:
            try:
                self.spotify_client.volume(level)
                return True
            except Exception as e:
                logger.error(f"Error setting Spotify volume: {e}")
                
        return False
        
    def set_mute(self, mute: bool) -> bool:
        """
        Mute or unmute playback.
        
        Args:
            mute: True to mute, False to unmute
            
        Returns:
            True if successful, False otherwise
        """
        if self.mpd_client:
            try:
                self.connect_mpd()
                if mute:
                    # Store current volume in client instance
                    status = self.mpd_client.status()
                    if "volume" in status:
                        self._mpd_volume_before_mute = int(status["volume"])
                    self.mpd_client.setvol(0)
                else:
                    # Restore previous volume
                    if hasattr(self, "_mpd_volume_before_mute"):
                        self.mpd_client.setvol(self._mpd_volume_before_mute)
                    else:
                        self.mpd_client.setvol(50)  # Default volume
                return True
            except Exception as e:
                logger.error(f"Error setting MPD mute: {e}")
                
        if self.spotify_client:
            try:
                if mute:
                    # Store current volume in client instance
                    playback = self.spotify_client.current_playback()
                    if playback and "device" in playback:
                        self._spotify_volume_before_mute = playback["device"]["volume_percent"]
                    self.spotify_client.volume(0)
                else:
                    # Restore previous volume
                    if hasattr(self, "_spotify_volume_before_mute"):
                        self.spotify_client.volume(self._spotify_volume_before_mute)
                    else:
                        self.spotify_client.volume(50)  # Default volume
                return True
            except Exception as e:
                logger.error(f"Error setting Spotify mute: {e}")
                
        return False
        
    def set_shuffle(self, shuffle: bool) -> bool:
        """
        Set shuffle mode.
        
        Args:
            shuffle: True to enable shuffle, False to disable
            
        Returns:
            True if successful, False otherwise
        """
        if self.mpd_client:
            try:
                self.connect_mpd()
                self.mpd_client.random(1 if shuffle else 0)
                return True
            except Exception as e:
                logger.error(f"Error setting MPD shuffle: {e}")
                
        if self.spotify_client:
            try:
                self.spotify_client.shuffle(shuffle)
                return True
            except Exception as e:
                logger.error(f"Error setting Spotify shuffle: {e}")
                
        return False
        
    def set_repeat(self, repeat: bool) -> bool:
        """
        Set repeat mode.
        
        Args:
            repeat: True to enable repeat, False to disable
            
        Returns:
            True if successful, False otherwise
        """
        if self.mpd_client:
            try:
                self.connect_mpd()
                self.mpd_client.repeat(1 if repeat else 0)
                return True
            except Exception as e:
                logger.error(f"Error setting MPD repeat: {e}")
                
        if self.spotify_client:
            try:
                self.spotify_client.repeat("context" if repeat else "off")
                return True
            except Exception as e:
                logger.error(f"Error setting Spotify repeat: {e}")
                
        return False
        
    def get_current_track(self) -> Optional[Dict[str, Any]]:
        """
        Get information about the current track.
        
        Returns:
            Dictionary with track information or None if not available
        """
        if self.mpd_client:
            try:
                self.connect_mpd()
                current_song = self.mpd_client.currentsong()
                if current_song:
                    return {
                        "title": current_song.get("title", "Unknown"),
                        "artist": current_song.get("artist", "Unknown"),
                        "album": current_song.get("album", "Unknown"),
                        "duration": int(current_song.get("time", 0)),
                        "source": "mpd"
                    }
            except Exception as e:
                logger.error(f"Error getting current track from MPD: {e}")
                
        if self.spotify_client:
            try:
                current = self.spotify_client.current_playback()
                if current and "item" in current:
                    item = current["item"]
                    artists = ", ".join([artist["name"] for artist in item["artists"]])
                    return {
                        "title": item["name"],
                        "artist": artists,
                        "album": item["album"]["name"],
                        "duration": item["duration_ms"] // 1000,  # Convert to seconds
                        "source": "spotify"
                    }
            except Exception as e:
                logger.error(f"Error getting current track from Spotify: {e}")
                
        return None
