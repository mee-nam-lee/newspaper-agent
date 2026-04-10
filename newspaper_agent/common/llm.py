from functools import cached_property

from google import genai
from google.adk.models.google_llm import Gemini
from pydantic import Field


class GeminiWithLocation(Gemini):
    """Subclass of Gemini to ensure location is passed to the internal Client."""

    location: str = Field(default="global", description="Vertex AI location")

    @cached_property
    def api_client(self) -> genai.Client:
        client = genai.Client(
            location=self.location,
            http_options=genai.types.HttpOptions(
                headers=self._tracking_headers(),
                retry_options=self.retry_options,
                base_url=self.base_url,
            ),
        )
        
        # Wrap generate_content with retry logic for 429 errors
        original_generate_content = client.models.generate_content
        
        def generate_content_with_retry(*args, **kwargs):
            import time
            
            max_retries = 5
            base_delay = 2
            
            for attempt in range(max_retries):
                try:
                    return original_generate_content(*args, **kwargs)
                except Exception as e:
                    err_str = str(e)
                    if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                        delay = base_delay * (2 ** attempt)
                        print(f"\n⚠️ 429 Resource Exhausted in LLM. Retrying in {delay}s... (Attempt {attempt+1}/{max_retries})")
                        time.sleep(delay)
                    else:
                        raise e
            
            # Final attempt
            return original_generate_content(*args, **kwargs)
            
        client.models.generate_content = generate_content_with_retry
        return client
