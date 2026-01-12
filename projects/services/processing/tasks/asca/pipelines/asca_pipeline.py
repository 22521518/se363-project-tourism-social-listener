"""
ASCA Extraction Pipeline.

Orchestrates the ASCA extraction process with language detection and batch support.
Uses the local core module for predictor and preprocessing.
"""

import sys
import logging
import threading
from pathlib import Path
from typing import List, Optional, Dict

# Setup path for imports
project_root = Path(__file__).resolve().parents[5]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

# Load .env from projects/.env
projects_env = project_root / "projects" / ".env"
if projects_env.exists():
    load_dotenv(projects_env)
else:
    docker_env = Path("/opt/airflow/projects/.env")
    if docker_env.exists():
        load_dotenv(docker_env)
    else:
        load_dotenv()

# Use absolute imports for Airflow compatibility
from projects.services.processing.tasks.asca.dto import UnifiedTextEvent, ASCAExtractionResult
from projects.services.processing.tasks.asca.config import settings, detect_language
from projects.services.processing.tasks.asca.core import ACSAPredictor

logger = logging.getLogger(__name__)

# Singleton instance and lock for thread-safe singleton pattern
_pipeline_instance: Optional['ASCAExtractionPipeline'] = None
_pipeline_lock = threading.Lock()


def get_pipeline_instance(
    model_path: Optional[str] = None,
    language: Optional[str] = None,
    auto_detect_language: Optional[bool] = None,
    vncorenlp_path: Optional[str] = None
) -> 'ASCAExtractionPipeline':
    """
    Get the singleton ASCAExtractionPipeline instance (thread-safe).
    
    This ensures only ONE pipeline instance (and ONE VnCoreNLP server) exists
    across the entire application, regardless of how many times this is called.
    
    Args:
        model_path: Path to the ASCA model (only used on first call)
        language: Default language (only used on first call)
        auto_detect_language: Whether to auto-detect language (only used on first call)
        vncorenlp_path: Path to VnCoreNLP JAR (only used on first call)
    
    Returns:
        The singleton ASCAExtractionPipeline instance
    """
    global _pipeline_instance
    
    # Fast path: return existing instance (no lock needed)
    if _pipeline_instance is not None:
        return _pipeline_instance
    
    # Slow path: create instance (requires lock)
    with _pipeline_lock:
        # Double-check after acquiring lock
        if _pipeline_instance is not None:
            return _pipeline_instance
        
        logger.info("🔧 Creating singleton ASCAExtractionPipeline instance...")
        _pipeline_instance = ASCAExtractionPipeline(
            model_path=model_path,
            language=language,
            auto_detect_language=auto_detect_language,
            vncorenlp_path=vncorenlp_path
        )
        logger.info("✅ Singleton ASCAExtractionPipeline created successfully")
        return _pipeline_instance


class ASCAExtractionPipeline:
    """
    Main ASCA extraction pipeline with language detection.
    
    Uses the local core module (ACSAPredictor) which loads the trained model
    and provides preprocessing and inference.
    
    NOTE: Use get_pipeline_instance() to get the singleton instance instead of
    creating this class directly, to avoid multiple VnCoreNLP servers.
    """
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        language: Optional[str] = None,
        auto_detect_language: Optional[bool] = None,
        vncorenlp_path: Optional[str] = None
    ):
        """
        Initialize the ASCA extraction pipeline.
        
        Args:
            model_path: Path to the ASCA model (defaults to settings)
            language: Default language for preprocessing ('vi' or 'en')
            auto_detect_language: Whether to auto-detect language from text
            vncorenlp_path: Path to VnCoreNLP JAR for Vietnamese
        """
        self.model_path = model_path or settings.asca_model_path
        self.default_language = language or settings.asca_language
        self.auto_detect_language = auto_detect_language if auto_detect_language is not None else settings.asca_auto_detect_language
        self.vncorenlp_path = vncorenlp_path or settings.vncorenlp_path
        
        # DUAL-PREDICTOR CACHE: Cache both vi and en predictors to avoid recreation
        # This prevents VnCoreNLP server from being restarted on every language switch
        self._predictors: Dict[str, ACSAPredictor] = {}  # {language: predictor}
        self._lock = threading.Lock()  # Thread lock to prevent race conditions
        
        logger.info(f"ASCAExtractionPipeline initialized - model: {self.model_path}, auto_detect: {self.auto_detect_language}")
    
    def _get_predictor(self, language: str):
        """
        Get or initialize the ASCA predictor for the given language (thread-safe).
        
        Uses dual-predictor caching: caches BOTH vi and en predictors so they're
        created only once and reused. This eliminates constant recreation on
        language switches.
        """
        # Fast path: return cached predictor if exists (no lock needed for read)
        if language in self._predictors:
            return self._predictors[language]
        
        # Slow path: need to create predictor for this language (requires lock)
        with self._lock:
            # Double-check after acquiring lock
            if language in self._predictors:
                return self._predictors[language]
            
            try:
                # Check if model file exists
                model_file = Path(self.model_path)
                if not model_file.exists():
                    logger.error(f"{'='*50}")
                    logger.error(f"❌ MODEL FILE NOT FOUND!")
                    logger.error(f"❌ Path: {self.model_path}")
                    logger.error(f"{'='*50}")
                    return None
                
                logger.info(f"🔧 Creating predictor for language: {language}")
                logger.info(f"Loading ASCA model from: {self.model_path}")
                
                predictor = ACSAPredictor(
                    model_path=self.model_path,
                    language=language,
                    vncorenlp_path=self.vncorenlp_path if language == 'vi' else None
                )
                
                # Cache the predictor for reuse
                self._predictors[language] = predictor
                logger.info(f"✅ ASCA predictor for '{language}' created and cached (total cached: {len(self._predictors)})")
                
                return predictor
                
            except ImportError as e:
                logger.error(f"{'='*50}")
                logger.error(f"❌ FAILED TO IMPORT ASCA PREDICTOR")
                logger.error(f"❌ Error: {e}")
                logger.error(f"{'='*50}")
                return None
            except Exception as e:
                logger.error(f"{'='*50}")
                logger.error(f"❌ FAILED TO INITIALIZE ASCA PREDICTOR")
                logger.error(f"❌ Error: {e}")
                logger.error(f"{'='*50}")
                return None
    
    def _detect_language(self, text: str) -> str:
        """Detect language from text."""
        if self.auto_detect_language:
            return detect_language(text)
        return self.default_language
    
    def process(self, event: UnifiedTextEvent) -> ASCAExtractionResult:
        """
        Process a UnifiedTextEvent and extract aspects.
        
        Args:
            event: The input event to process.
            
        Returns:
            ASCAExtractionResult with extracted aspect-sentiment pairs.
        """
        # Check if record is already validated - skip processing
        if event.validated:
            logger.info(f"Skipping validated record: {event.external_id}")
            return ASCAExtractionResult.empty(extractor="asca")
        
        # Get text
        text = event.text.strip() if event.text else ""
        
        if not text:
            logger.debug(f"Empty text for record: {event.external_id}")
            return ASCAExtractionResult.empty(extractor="asca")
        
        # Detect or use provided language
        language = event.language or self._detect_language(text)
        
        # Get predictor for this language
        predictor = self._get_predictor(language)
        
        if predictor is None:
            logger.warning(f"ASCA predictor not available")
            return ASCAExtractionResult.empty(extractor="asca", language=language)
        
        try:
            # Get predictions
            predictions = predictor.predict_single(text, preprocess=True)
            
            # Convert to result
            result = ASCAExtractionResult.from_predictor_output(predictions, language=language)
            
            logger.debug(f"Extracted {len(result.aspects)} aspects for {event.external_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing event {event.external_id}: {e}", exc_info=True)
            return ASCAExtractionResult.empty(extractor="asca", language=language)
    
    def process_batch(
        self,
        events: List[UnifiedTextEvent],
        show_progress: bool = False
    ) -> List[ASCAExtractionResult]:
        """
        Process a batch of events.
        
        Args:
            events: List of input events
            show_progress: Whether to show progress bar
            
        Returns:
            List of ASCAExtractionResult for each event
        """
        results = []
        
        if show_progress:
            try:
                from tqdm import tqdm
                events = tqdm(events, desc="Processing ASCA")
            except ImportError:
                pass
        
        for event in events:
            result = self.process(event)
            results.append(result)
        
        return results
    
    def process_texts(
        self,
        texts: List[str],
        language: Optional[str] = None
    ) -> List[ASCAExtractionResult]:
        """
        Process a list of raw texts.
        
        Args:
            texts: List of text strings
            language: Language override (None = auto-detect per text)
            
        Returns:
            List of ASCAExtractionResult
        """
        events = [
            UnifiedTextEvent(
                source="direct",
                source_type="text",
                external_id=f"text-{i}",
                text=text,
                language=language
            )
            for i, text in enumerate(texts)
        ]
        
        return self.process_batch(events)
    
    def close(self):
        """Clean up all cached predictors (including VnCoreNLP servers)."""
        with self._lock:
            for language, predictor in self._predictors.items():
                try:
                    if hasattr(predictor, 'close'):
                        predictor.close()
                        logger.info(f"✅ Closed predictor for language: {language}")
                except Exception as e:
                    logger.warning(f"⚠️ Error closing predictor for {language}: {e}")
            self._predictors.clear()
            logger.info("✅ All cached predictors closed")


def extract_aspects(event: UnifiedTextEvent) -> ASCAExtractionResult:
    """Convenience function to extract aspects from an event."""
    pipeline = ASCAExtractionPipeline()
    return pipeline.process(event)


def extract_aspects_from_text(text: str, language: Optional[str] = None) -> ASCAExtractionResult:
    """Convenience function to extract aspects from raw text."""
    event = UnifiedTextEvent(
        source="direct",
        source_type="text",
        external_id="direct-input",
        text=text,
        language=language
    )
    return extract_aspects(event)
