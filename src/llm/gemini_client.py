import os
import logging
from typing import Optional
from google import genai

logger = logging.getLogger(__name__)

class GeminiClient:
    """
    A safe wrapper around Google's GenAI SDK (google-genai) client.
    Handles environment configuration checks and prevents unintended external requests.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        if api_key is not None:
            self.api_key = api_key
        else:
            self.api_key = os.getenv("GEMINI_API_KEY", "")
            
        # Ignore placeholder keys
        if self.api_key.lower().strip() in {
            "your_actual_key_here",
            "your_gemini_api_key_here",
            "your_api_key_here",
            ""
        }:
            self.api_key = ""
            
        self._client = None
        
        if self.api_key:
            logger.info("Initializing Google GenAI client...")
            self._client = genai.Client(api_key=self.api_key)
        else:
            logger.warning("GEMINI_API_KEY is not set or is a placeholder. GeminiClient will run in unconfigured mode.")
            
    def is_configured(self) -> bool:
        """Returns True if the client is initialized with an API key."""
        return self._client is not None
        
    def generate_text(self, prompt: str) -> str:
        """
        Generates text content using Gemini.
        Raises ValueError if the client is not configured.
        """
        if not self.is_configured():
            raise ValueError(
                "Gemini API key is not configured. "
                "Please configure GEMINI_API_KEY in your .env file or environment."
            )
        
        logger.info("Sending content generation request to Gemini (gemini-2.5-flash)...")
        # In Phase 2/3, this uses gemini-2.5-flash for reasoning/text generation
        response = self._client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return response.text
