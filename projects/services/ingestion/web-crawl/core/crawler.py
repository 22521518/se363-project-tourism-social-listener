"""
Tourism Crawler - Wrapper around Crawl4AI for tourism content extraction.

Uses AsyncWebCrawler with LLMExtractionStrategy to extract structured
tourism data from web pages.
"""
import os
import json
import time
import asyncio
from typing import Optional
from pydantic import BaseModel, Field
from typing import List
from collections import deque

from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CrawlerRunConfig,
    CacheMode,
    LLMConfig,
)
from crawl4ai import LLMExtractionStrategy

from .extraction_router import ExtractionConfig


class RateLimiter:
    """
    Simple rate limiter to limit API requests per minute.
    
    Uses a sliding window to track request timestamps.
    """
    
    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum requests allowed in the window (default: 10)
            window_seconds: Time window in seconds (default: 60)
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.request_times: deque = deque()
    
    async def wait_if_needed(self):
        """Wait if we've exceeded the rate limit."""
        now = time.time()
        
        # Remove old requests outside the window
        while self.request_times and self.request_times[0] < now - self.window_seconds:
            self.request_times.popleft()
        
        # Check if we need to wait
        if len(self.request_times) >= self.max_requests:
            oldest = self.request_times[0]
            wait_time = oldest + self.window_seconds - now + 0.1  # Add a small buffer
            if wait_time > 0:
                print(f"[RATE LIMIT] Waiting {wait_time:.1f}s to stay under {self.max_requests} req/min...")
                await asyncio.sleep(wait_time)
                # Clean up again after waiting
                now = time.time()
                while self.request_times and self.request_times[0] < now - self.window_seconds:
                    self.request_times.popleft()
        
        # Record this request
        self.request_times.append(time.time())
        print(f"[RATE LIMIT] Request {len(self.request_times)}/{self.max_requests} in current window")


class ModelFallbackChain:
    """
    Manages model fallback when rate limits are hit.
    
    Uses Gemini models with automatic fallback on rate limit errors.
    Tracks rate limit errors per model with a cooldown period.
    """
    
    # Gemini models ordered by quality (best first), fall back to smaller models
    MODELS = [
        {"name": "gemini/gemini-2.5-flash", "rpm": 5, "tpm": 250000, "rpd": 20, "provider": "gemini"},
        {"name": "gemini/gemini-2.5-flash-lite", "rpm": 10, "tpm": 250000, "rpd": 20, "provider": "gemini"},
        # {"name": "gemini/gemma-3-27b-it", "rpm": 30, "tpm": 10000, "rpd": 14400, "provider": "gemini"},
        # {"name": "gemini/gemma-3-27b-it", "rpm": 30, "tpm": 10000, "rpd": 14400, "provider": "gemini"},
        # {"name": "gemini/gemini-2.0-flash-lite-preview-02-05", "rpm": 30, "tpm": 10000, "rpd": 14400, "provider": "gemini"},
    ]
    
    # Cooldown period in seconds after a rate limit error
    COOLDOWN_SECONDS = 60
    
    def __init__(self):
        # Track when each model was rate limited: {model_name: timestamp}
        self.rate_limited_until: dict = {}
        # Active models
        self.active_models = self.MODELS.copy()
    
    def filter_models(self, has_gemini: bool):
        """
        Filter available models based on configured API keys.
        
        Args:
            has_gemini: Whether Gemini API key is available
        """
        if has_gemini:
            self.active_models = self.MODELS.copy()
            print(f"[INFO] Using Gemini models ({len(self.active_models)} models)")
        else:
            raise ValueError("No models available. Configure GEMINI_API_KEY.")
    
    def get_available_models(self) -> list:
        """Get list of models not currently in cooldown."""
        now = time.time()
        available = []
        for model in self.active_models:
            cooldown_until = self.rate_limited_until.get(model["name"], 0)
            if now >= cooldown_until:
                available.append(model)
            else:
                remaining = int(cooldown_until - now)
                print(f"[FALLBACK] Model {model['name']} in cooldown for {remaining}s")
        return available
    
    def mark_rate_limited(self, model_name: str):
        """Mark a model as rate limited for the cooldown period."""
        self.rate_limited_until[model_name] = time.time() + self.COOLDOWN_SECONDS
        print(f"[FALLBACK] Model {model_name} marked as rate limited for {self.COOLDOWN_SECONDS}s")
    
    def get_best_model(self) -> Optional[dict]:
        """Get the best available model (first in priority that's not in cooldown)."""
        available = self.get_available_models()
        if available:
            return available[0]
        return None
    
    def get_max_content_for_model(self, model_info: dict) -> int:
        """
        Calculate max content length based on model's TPM limit.
        
        Uses ~80% of TPM to leave room for output tokens.
        Assumes 1 token ≈ 4 characters.
        
        Args:
            model_info: Model dict with 'tpm' key
            
        Returns:
            Maximum content length in characters
        """
        tpm = model_info.get("tpm", 10000)
        # Use 80% of TPM for input, leave 20% for output
        input_tokens = int(tpm * 0.8)
        # 1 token ≈ 4 characters
        max_chars = input_tokens * 4
        print(f"[INFO] Model {model_info['name']}: TPM={tpm}, max_content={max_chars} chars")
        return max_chars
    
    async def wait_for_available_model(self) -> dict:
        """Wait until at least one model becomes available."""
        while True:
            model = self.get_best_model()
            if model:
                return model
            
            # Find the soonest model to become available
            now = time.time()
            soonest = min(self.rate_limited_until.values())
            wait_time = max(0, soonest - now) + 1
            print(f"[FALLBACK] All models rate limited. Waiting {wait_time:.1f}s...")
            await asyncio.sleep(wait_time)


class TourismReview(BaseModel):
    """Schema for extracted reviews."""
    author: Optional[str] = Field(None, description="Review author name")
    text: str = Field(..., description="Review text content")
    rating: Optional[float] = Field(None, description="Numeric rating if available")


class TourismComment(BaseModel):
    """Schema for extracted comments."""
    author: Optional[str] = Field(None, description="Comment author name")
    text: str = Field(..., description="Comment text content")


class TourismBlogSection(BaseModel):
    """Schema for blog sections."""
    heading: str = Field(..., description="Section heading")
    text: str = Field(..., description="Section content")


class TourismAgencyInfo(BaseModel):
    """Schema for agency/tour information."""
    tour_name: Optional[str] = Field(None, description="Name of the tour")
    price: Optional[str] = Field(None, description="Tour price")
    duration: Optional[str] = Field(None, description="Tour duration")
    included_services: List[str] = Field(default_factory=list, description="List of included services")


class TourismContent(BaseModel):
    """Complete tourism content schema for LLM extraction."""
    title: Optional[str] = Field(None, description="Page or location title")
    information: Optional[str] = Field(None, description="General tourism information")
    reviews: List[TourismReview] = Field(default_factory=list, description="List of reviews")
    comments: List[TourismComment] = Field(default_factory=list, description="List of comments")
    blog_sections: List[TourismBlogSection] = Field(default_factory=list, description="Blog content sections")
    agency_info: Optional[TourismAgencyInfo] = Field(None, description="Tour agency information")


class TourismCrawler:
    """
    Wrapper around Crawl4AI for extracting tourism content.
    
    Uses LLMExtractionStrategy with Gemini to extract structured data.
    Supports model fallback chain for handling rate limits.
    """
    
    def __init__(
        self,
        gemini_api_key: Optional[str] = None,
        headless: bool = True,
        max_content_length: int = 100000,
        rate_limit_per_min: int = 3,
    ):
        """
        Initialize the crawler.
        
        Args:
            gemini_api_key: Gemini API key. Defaults to GEMINI_API_KEY env var.
            headless: Whether to run browser in headless mode.
            max_content_length: Maximum content length to send to LLM (chars).
                               Limits API token usage to stay within rate limits.
            rate_limit_per_min: Maximum LLM API requests per minute (default: 3).
        """
        self.gemini_api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
        
        if not self.gemini_api_key:
            raise ValueError(
                "API key required. Set GEMINI_API_KEY "
                "environment variable, or pass gemini_api_key parameter."
            )
        
        print("[INFO] Using Gemini API as LLM provider")
        
        self.headless = headless
        self.max_content_length = max_content_length
        self.rate_limiter = RateLimiter(max_requests=rate_limit_per_min, window_seconds=60)
        self.fallback_chain = ModelFallbackChain()
        
        # Filter available models based on configured API keys
        self.fallback_chain.filter_models(
            has_gemini=bool(self.gemini_api_key)
        )
        
        # Browser configuration
        self.browser_config = BrowserConfig(
            headless=headless,
            verbose=False,
        )
    
    def _get_api_key_for_model(self, model: str) -> str:
        """
        Get the appropriate API key for the given model.
        
        Args:
            model: Model name (e.g., 'gemini/gemini-2.5-flash')
            
        Returns:
            The Gemini API key
        """
        if not self.gemini_api_key:
            raise ValueError(f"Gemini API key required for model {model}")
        return self.gemini_api_key
    
    def _create_extraction_strategy(
        self, 
        extraction_config: ExtractionConfig,
        model: str,
        batch_mode: bool = False,
        batch_urls: Optional[List[str]] = None,
    ) -> LLMExtractionStrategy:
        """Create LLM extraction strategy with tourism-focused instructions.
        
        Args:
            extraction_config: Extraction configuration with instructions
            model: The LLM model to use
            batch_mode: If True, modify instruction for batch extraction
            batch_urls: List of URLs being processed in batch mode
        """
        instruction = extraction_config.llm_instruction
        
        # Modify instruction for batch mode
        if batch_mode and batch_urls:
            instruction = f"""
{instruction}

IMPORTANT: This content contains multiple pages separated by "=== URL: <url> ===" markers.
Extract data for EACH page separately and return a JSON object with URLs as keys:
{{
  "<url1>": {{ extracted data for url1 }},
  "<url2>": {{ extracted data for url2 }},
  ...
}}
"""
        
        # Get the appropriate API key for this model
        api_key = self._get_api_key_for_model(model)
        
        return LLMExtractionStrategy(
            llm_config=LLMConfig(
                provider=model,
                api_token=api_key,
            ),
            schema=TourismContent.model_json_schema(),
            extraction_type="schema",
            instruction=instruction,
            # Limit content to reduce API token usage and avoid rate limits
            chunk_token_threshold=2000,  # Max tokens per chunk
            overlap_rate=0.0,  # No overlap to save tokens
            apply_chunking=False,  # Disable chunking, use truncation instead
            input_format="markdown",  # Use markdown for efficiency
        )
    
    async def crawl(
        self,
        url: str,
        extraction_config: ExtractionConfig,
    ) -> dict:
        """
        Crawl a URL and extract tourism content.
        
        Args:
            url: The URL to crawl
            extraction_config: Configuration from extraction_router
            
        Returns:
            Extracted content as dictionary
        """
        # First, fetch the page WITHOUT LLM extraction
        # This allows us to truncate content before sending to LLM
        fetch_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            word_count_threshold=10,
            only_text=True,  # Extract only text content
        )
        
        # Perform initial crawl to get markdown content
        async with AsyncWebCrawler(config=self.browser_config) as crawler:
            result = await crawler.arun(url=url, config=fetch_config)
            
            if not result.success:
                print(f"[ERROR] Crawl failed: {result.error_message}")
                return self._empty_content()
            
            # Get markdown content
            markdown_content = ""
            if result.markdown and result.markdown.raw_markdown:
                markdown_content = result.markdown.raw_markdown
            
            print(f"\n[DEBUG] Crawl success: {result.success}")
            print(f"[DEBUG] Original markdown length: {len(markdown_content)} chars")
            
            # Skip very short content
            if len(markdown_content) < 100:
                print("[WARNING] Content too short for extraction")
                return self._empty_content()
            
            # Apply rate limiting before making LLM request
            await self.rate_limiter.wait_if_needed()
            
            # Pass full content - truncation will be done per model in fallback
            return await self._extract_with_fallback(
                url=url,
                html=result.html if result.html else "",
                markdown=markdown_content,
                extraction_config=extraction_config,
            )
    
    async def _extract_with_fallback(
        self,
        url: str,
        html: str,
        markdown: str,
        extraction_config: ExtractionConfig,
    ) -> dict:
        """
        Run LLM extraction with automatic model fallback on rate limit errors.
        Content is truncated dynamically based on each model's TPM limit.
        """
        last_error = None
        
        while True:
            # Get best available model
            model_info = await self.fallback_chain.wait_for_available_model()
            model_name = model_info["name"]
            
            print(f"[FALLBACK] Using model: {model_name}")
            
            # Calculate max content length for this model's TPM
            max_content = self.fallback_chain.get_max_content_for_model(model_info)
            
            # Truncate content for this model
            truncated_markdown = markdown[:max_content] if len(markdown) > max_content else markdown
            if len(markdown) > max_content:
                print(f"[DEBUG] Truncated content from {len(markdown)} to {len(truncated_markdown)} chars for {model_name}")
            
            extraction_strategy = self._create_extraction_strategy(
                extraction_config, 
                model=model_name
            )
            
            # Create run config with extraction strategy
            run_config = CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
                extraction_strategy=extraction_strategy,
                word_count_threshold=10,
            )
            
            print("[INFO] Running LLM extraction...")
            try:
                async with AsyncWebCrawler(config=self.browser_config) as crawler:
                    result = await crawler.arun(url=url, config=run_config)
                    
                    if not result.success:
                        print(f"[ERROR] Crawl failed: {result.error_message}")
                        return self._empty_content()
                    
                    extracted_content = result.extracted_content
                    print(f"[DEBUG] Extracted content: {str(extracted_content)[:500]}...")
                    
                    # Parse the extraction result
                    return self._parse_extraction_result(extracted_content)
                
            except Exception as e:
                error_str = str(e).lower()
                
                # Print full error for debugging
                print(f"\n{'='*60}")
                print(f"[ERROR DETAILS] Model: {model_name}")
                print(f"[ERROR DETAILS] Error Type: {type(e).__name__}")
                print(f"[ERROR DETAILS] Error Message: {e}")
                print(f"{'='*60}\n")
                
                # Check if it's a rate limit error
                if "rate" in error_str or "quota" in error_str or "429" in error_str or "resource_exhausted" in error_str:
                    print(f"[FALLBACK] ⚠️ Rate limit hit for {model_name}")
                    print(f"[FALLBACK] Switching to next available model...")
                    self.fallback_chain.mark_rate_limited(model_name)
                    last_error = e
                    continue
                else:
                    # Not a rate limit error, re-raise with full traceback
                    import traceback
                    print(f"[ERROR] ❌ LLM extraction failed (non-rate-limit error):")
                    traceback.print_exc()
                    raise
    
    def _parse_extraction_result(self, extracted_content) -> dict:
        """Parse the LLM extraction result into a dictionary."""
        if not extracted_content:
            return self._empty_content()
        
        if isinstance(extracted_content, str):
            try:
                extracted = json.loads(extracted_content)
            except json.JSONDecodeError:
                return self._empty_content()
        else:
            extracted = extracted_content
        
        # Check for errors
        if isinstance(extracted, list) and len(extracted) > 0:
            first_item = extracted[0]
            if isinstance(first_item, dict) and first_item.get("error"):
                error_msg = first_item.get("content", "Unknown LLM extraction error")
                raise RuntimeError(f"LLM Extraction Error: {error_msg}")
            return first_item
        elif isinstance(extracted, dict):
            if extracted.get("error"):
                error_msg = extracted.get("content", "Unknown LLM extraction error")
                raise RuntimeError(f"LLM Extraction Error: {error_msg}")
            return extracted
        else:
            return self._empty_content()
    
    async def crawl_batch(
        self,
        urls: List[str],
        extraction_config: ExtractionConfig,
        batch_size: int = 3,
    ) -> List[dict]:
        """
        Crawl multiple URLs and extract content in batches.
        
        Combines multiple pages into a single LLM call to reduce RPM usage.
        
        Args:
            urls: List of URLs to crawl
            extraction_config: Configuration from extraction_router
            batch_size: Number of URLs per LLM call (default: 3)
            
        Returns:
            List of extracted content dictionaries (same order as input URLs)
        """
        results = []
        
        # First, crawl all pages to get their content (parallel)
        page_contents = await self._fetch_pages_content(urls)
        
        # Process in batches
        for i in range(0, len(urls), batch_size):
            batch_urls = urls[i:i + batch_size]
            batch_contents = page_contents[i:i + batch_size]
            
            # Filter out failed pages
            valid_batch = [
                (url, content) for url, content in zip(batch_urls, batch_contents)
                if content and len(content) >= 100
            ]
            
            if not valid_batch:
                # All pages in batch failed, add empty results
                results.extend([self._empty_content() for _ in batch_urls])
                continue
            
            # Combine content with URL markers
            combined_markdown = ""
            valid_urls = []
            for url, content in valid_batch:
                combined_markdown += f"\n=== URL: {url} ===\n{content}\n"
                valid_urls.append(url)
            
            # Apply rate limiting
            await self.rate_limiter.wait_if_needed()
            
            # Extract with fallback (batch mode)
            batch_result = await self._extract_batch_with_fallback(
                urls=valid_urls,
                markdown=combined_markdown,
                extraction_config=extraction_config,
            )
            
            # Map results back to original URLs
            for url in batch_urls:
                if url in batch_result:
                    results.append(batch_result[url])
                else:
                    results.append(self._empty_content())
        
        return results
    
    async def _fetch_pages_content(self, urls: List[str]) -> List[str]:
        """Fetch markdown content from multiple URLs in parallel."""
        fetch_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            word_count_threshold=10,
            only_text=True,
        )
        
        contents = []
        
        async with AsyncWebCrawler(config=self.browser_config) as crawler:
            # Crawl all URLs
            for url in urls:
                try:
                    result = await crawler.arun(url=url, config=fetch_config)
                    
                    if result.success and result.markdown and result.markdown.raw_markdown:
                        content = result.markdown.raw_markdown
                        # Truncate to save tokens
                        if len(content) > self.max_content_length:
                            content = content[:self.max_content_length]
                        contents.append(content)
                    else:
                        contents.append("")
                        print(f"[WARNING] Failed to fetch {url}")
                except Exception as e:
                    print(f"[ERROR] Error fetching {url}: {e}")
                    contents.append("")
        
        return contents
    
    async def _extract_batch_with_fallback(
        self,
        urls: List[str],
        markdown: str,
        extraction_config: ExtractionConfig,
    ) -> dict:
        """
        Run batch LLM extraction with automatic model fallback.
        
        Note: Due to Crawl4AI API limitations, batch mode extracts each URL 
        individually but with fallback chain support.
        
        Returns a dictionary mapping URL -> extracted content.
        """
        results = {}
        
        for url in urls:
            # Extract single URL from combined markdown
            url_marker = f"=== URL: {url} ==="
            url_content = ""
            
            # Find content for this URL in combined markdown
            if url_marker in markdown:
                start_idx = markdown.find(url_marker) + len(url_marker)
                # Find next URL marker or end
                next_marker_idx = markdown.find("=== URL:", start_idx)
                if next_marker_idx == -1:
                    url_content = markdown[start_idx:].strip()
                else:
                    url_content = markdown[start_idx:next_marker_idx].strip()
            
            if not url_content or len(url_content) < 100:
                results[url] = self._empty_content()
                continue
            
            # Extract with fallback for this URL
            while True:
                model_info = await self.fallback_chain.wait_for_available_model()
                model_name = model_info["name"]
                
                print(f"[FALLBACK] Using model for {url}: {model_name}")
                
                extraction_strategy = self._create_extraction_strategy(
                    extraction_config,
                    model=model_name,
                )
                
                run_config = CrawlerRunConfig(
                    cache_mode=CacheMode.BYPASS,
                    extraction_strategy=extraction_strategy,
                    word_count_threshold=10,
                )
                
                print(f"[INFO] Extracting: {url}")
                try:
                    async with AsyncWebCrawler(config=self.browser_config) as crawler:
                        result = await crawler.arun(url=url, config=run_config)
                        
                        if not result.success:
                            print(f"[WARNING] Crawl failed for {url}: {result.error_message}")
                            results[url] = self._empty_content()
                            break
                        
                        extracted_content = result.extracted_content
                        results[url] = self._parse_extraction_result(extracted_content)
                        break  # Success, move to next URL
                        
                except Exception as e:
                    error_str = str(e).lower()
                    
                    # Print full exception details
                    import traceback
                    print(f"\n{'='*60}")
                    print(f"[EXCEPTION] Model: {model_name}")
                    print(f"[EXCEPTION] Type: {type(e).__name__}")
                    print(f"[EXCEPTION] Message: {e}")
                    print(f"[EXCEPTION] Traceback:")
                    traceback.print_exc()
                    print(f"{'='*60}\n")
                    
                    if "rate" in error_str or "quota" in error_str or "429" in error_str or "resource_exhausted" in error_str:
                        print(f"[FALLBACK] ⚠️ Rate limit hit for {model_name}")
                        print(f"[FALLBACK] Switching to next available model...")
                        self.fallback_chain.mark_rate_limited(model_name)
                        continue
                    else:
                        print(f"[ERROR] ❌ Extraction failed for {url}")
                        results[url] = self._empty_content()
                        break  # Non-rate-limit error, move to next URL
        
        return results
    
    def _empty_content(self) -> dict:
        """Return empty content structure."""
        return {
            "title": None,
            "information": None,
            "reviews": [],
            "comments": [],
            "blog_sections": [],
            "agency_info": None,
        }
