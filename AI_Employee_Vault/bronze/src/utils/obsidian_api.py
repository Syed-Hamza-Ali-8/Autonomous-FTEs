"""
Obsidian Local REST API client.

Enables direct interaction with Obsidian for creating notes,
adding wikilinks, and building a rich graph view.
"""

import os
import requests
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging
from dotenv import load_dotenv


class ObsidianAPI:
    """Client for Obsidian Local REST API."""

    def __init__(self, vault_path: Path):
        """
        Initialize Obsidian API client.

        Args:
            vault_path: Path to the vault root directory
        """
        self.vault_path = Path(vault_path)
        self.logger = logging.getLogger(__name__)
        
        # Load environment variables
        env_path = self.vault_path / ".env"
        if env_path.exists():
            load_dotenv(env_path)
        
        # Get API configuration
        self.api_key = os.getenv("OBSIDIAN_API_KEY")
        self.api_url = os.getenv("OBSIDIAN_API_URL", "http://localhost:27123")
        self.vault_name = os.getenv("OBSIDIAN_VAULT_NAME", "bronze")
        
        # Check if API is configured
        self.enabled = self.api_key is not None
        
        if not self.enabled:
            self.logger.warning(
                "Obsidian API not configured. Create .env file with OBSIDIAN_API_KEY. "
                "Graph view connections will be limited."
            )
    
    def _headers(self) -> Dict[str, str]:
        """Get request headers with API key."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def is_available(self) -> bool:
        """
        Check if Obsidian API is available.

        Returns:
            True if API is reachable, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            response = requests.get(
                f"{self.api_url}/",
                headers=self._headers(),
                timeout=2
            )
            return response.status_code == 200
        except Exception as e:
            self.logger.debug(f"Obsidian API not available: {e}")
            return False
    
    def create_note(
        self,
        path: str,
        content: str,
        tags: Optional[List[str]] = None,
        overwrite: bool = False
    ) -> bool:
        """
        Create a note in Obsidian.

        Args:
            path: Relative path from vault root (e.g., "Done/note.md")
            content: Note content (markdown)
            tags: Optional list of tags to add
            overwrite: Whether to overwrite if file exists

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            # Add tags to content if provided
            if tags:
                tag_line = " ".join([f"#{tag}" for tag in tags])
                content = f"{tag_line}\n\n{content}"
            
            endpoint = f"{self.api_url}/vault/{path}"
            
            response = requests.put(
                endpoint,
                headers=self._headers(),
                json={"content": content},
                timeout=5
            )
            
            if response.status_code in [200, 201]:
                self.logger.info(f"Created note via Obsidian API: {path}")
                return True
            else:
                self.logger.warning(f"Failed to create note: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error creating note via Obsidian API: {e}")
            return False
    
    def update_note(
        self,
        path: str,
        content: str
    ) -> bool:
        """
        Update an existing note in Obsidian.

        Args:
            path: Relative path from vault root
            content: New note content

        Returns:
            True if successful, False otherwise
        """
        return self.create_note(path, content, overwrite=True)
    
    def append_to_note(
        self,
        path: str,
        content: str
    ) -> bool:
        """
        Append content to an existing note.

        Args:
            path: Relative path from vault root
            content: Content to append

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            endpoint = f"{self.api_url}/vault/{path}"
            
            response = requests.patch(
                endpoint,
                headers=self._headers(),
                json={"content": content},
                timeout=5
            )
            
            return response.status_code == 204
            
        except Exception as e:
            self.logger.error(f"Error appending to note: {e}")
            return False
    
    def search(self, query: str) -> List[Dict[str, Any]]:
        """
        Search vault for notes matching query.

        Args:
            query: Search query

        Returns:
            List of matching notes with metadata
        """
        if not self.enabled:
            return []
        
        try:
            endpoint = f"{self.api_url}/search/simple/"
            
            response = requests.post(
                endpoint,
                headers=self._headers(),
                json={"query": query},
                timeout=5
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return []
                
        except Exception as e:
            self.logger.error(f"Error searching vault: {e}")
            return []
    
    def get_active_file(self) -> Optional[str]:
        """
        Get the currently active file in Obsidian.

        Returns:
            Path to active file or None
        """
        if not self.enabled:
            return None
        
        try:
            endpoint = f"{self.api_url}/active/"
            
            response = requests.get(
                endpoint,
                headers=self._headers(),
                timeout=2
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("path")
            else:
                return None
                
        except Exception as e:
            self.logger.debug(f"Error getting active file: {e}")
            return None
    
    def open_file(self, path: str) -> bool:
        """
        Open a file in Obsidian.

        Args:
            path: Relative path from vault root

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            endpoint = f"{self.api_url}/open/{path}"
            
            response = requests.post(
                endpoint,
                headers=self._headers(),
                timeout=2
            )
            
            return response.status_code == 200
            
        except Exception as e:
            self.logger.error(f"Error opening file: {e}")
            return False


def create_wikilink(note_name: str, display_text: Optional[str] = None) -> str:
    """
    Create a wikilink for Obsidian graph view.

    Args:
        note_name: Name of the note to link to (without .md extension)
        display_text: Optional display text for the link

    Returns:
        Formatted wikilink string
    """
    # Remove .md extension if present
    note_name = note_name.replace(".md", "")
    
    if display_text:
        return f"[[{note_name}|{display_text}]]"
    else:
        return f"[[{note_name}]]"


def create_tag(tag_name: str) -> str:
    """
    Create a tag for Obsidian.

    Args:
        tag_name: Tag name (without # prefix)

    Returns:
        Formatted tag string
    """
    # Remove # prefix if present
    tag_name = tag_name.lstrip("#")
    
    return f"#{tag_name}"
