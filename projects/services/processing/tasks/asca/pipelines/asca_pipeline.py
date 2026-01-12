"""
ASCA Extraction Pipeline.

Orchestrates the ASCA extraction process with language detection and batch support.
Uses the local core module for predictor and preprocessing.
"""

import sys
import logging
from pathlib import Path
from typing import List, Optional

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


class ASCAExtractionPipeline:
    """
    Main ASCA extraction pipeline with language detection.
    
    Uses the local core module (ACSAPredictor) which loads the trained model
    and provides preprocessing and inference.
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
        
        # Lazy initialization
        self._predictor = None
        self._predictor_language = None
        self._predictor_initialized = False
        
        logger.info(f"ASCAExtractionPipeline initialized - model: {self.model_path}, auto_detect: {self.auto_detect_language}")
    
    def _get_predictor(self, language: str):
        """
        Get or initialize the ASCA predictor.
        
        Re-initializes if language changes (different preprocessor needed).
        """
        if self._predictor is not None and self._predictor_language == language:
            return self._predictor
        
        if not self._predictor_initialized or self._predictor_language != language:
            self._predictor_initialized = True
            self._predictor_language = language
            
            try:
                # Check if model file exists
                model_file = Path(self.model_path)
                if not model_file.exists():
                    logger.error(f"{'='*50}")
                    logger.error(f"❌ MODEL FILE NOT FOUND!")
                    logger.error(f"❌ Path: {self.model_path}")
                    logger.error(f"{'='*50}")
                    self._predictor = None
                    return None
                
                logger.info(f"Loading ASCA model from: {self.model_path}")
                
                self._predictor = ACSAPredictor(
                    model_path=self.model_path,
                    language=language,
                    vncorenlp_path=self.vncorenlp_path if language == 'vi' else None
                )
                logger.info(f"✅ ASCA predictor initialized for language: {language}")
                
            except ImportError as e:
                logger.error(f"{'='*50}")
                logger.error(f"❌ FAILED TO IMPORT ASCA PREDICTOR")
                logger.error(f"❌ Error: {e}")
                logger.error(f"{'='*50}")
                self._predictor = None
            except Exception as e:
                logger.error(f"{'='*50}")
                logger.error(f"❌ FAILED TO INITIALIZE ASCA PREDICTOR")
                logger.error(f"❌ Error: {e}")
                logger.error(f"{'='*50}")
                self._predictor = None
        
        return self._predictor
    
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
        """Clean up resources."""
        if self._predictor and hasattr(self._predictor, 'close'):
            self._predictor.close()
            self._predictor = None


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
