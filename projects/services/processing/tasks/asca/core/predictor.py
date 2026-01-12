"""
High-level inference module for ACSA.
"""
import json
from pathlib import Path
from typing import List, Dict, Optional, Union, Tuple, Any
import pandas as pd

from .models import ACSAPipeline
from .preprocessing import VietnameseTextProcessor, EnglishTextProcessor, TextProcessor


class ACSAPredictor:
    """
    High-level predictor for ACSA inference.
    Combines preprocessing and model inference in one interface.
    """
    
    def __init__(self,
                 model_path: Optional[Union[str, Path]] = None,
                 pipeline: Optional[ACSAPipeline] = None,
                 language: str = 'vi',
                 vncorenlp_path: Optional[str] = None):
        """
        Initialize predictor.
        
        Args:
            model_path: Path to saved ACSAPipeline
            pipeline: Pre-loaded ACSAPipeline (alternative to model_path)
            language: Language for preprocessing ('vi' or 'en')
            vncorenlp_path: Path to VnCoreNLP JAR (for Vietnamese)
        """
        if pipeline is not None:
            self.pipeline = pipeline
        elif model_path is not None:
            self.pipeline = ACSAPipeline.load(model_path)
        else:
            raise ValueError("Either model_path or pipeline must be provided")
        
        self.language = language
        self.preprocessor = self._create_preprocessor(language, vncorenlp_path)
    
    def _create_preprocessor(self, language: str, vncorenlp_path: Optional[str]) -> TextProcessor:
        """Create appropriate text preprocessor."""
        if language == 'vi':
            return VietnameseTextProcessor(vncorenlp_path=vncorenlp_path)
        elif language == 'en':
            return EnglishTextProcessor()
        else:
            raise ValueError(f"Unsupported language: {language}")
    
    def preprocess(self, text: str) -> str:
        """Preprocess a single text."""
        return self.preprocessor.process(text)
    
    def predict(self, 
                text: Union[str, List[str]], 
                preprocess: bool = True) -> List[List[Tuple[str, str]]]:
        """
        Predict aspect categories and sentiments.
        
        Args:
            text: Single text or list of texts
            preprocess: Whether to preprocess input
            
        Returns:
            List of lists containing (category, sentiment) tuples
        """
        if isinstance(text, str):
            texts = [text]
        else:
            texts = text
        
        if preprocess:
            texts = [self.preprocessor.process(t) for t in texts]
        
        return self.pipeline.predict(texts)
    
    def predict_single(self, 
                       text: str, 
                       preprocess: bool = True) -> List[Tuple[str, str]]:
        """Predict for a single text."""
        results = self.predict([text], preprocess=preprocess)
        return results[0] if results else []
    
    def predict_with_details(self, 
                             text: str, 
                             preprocess: bool = True) -> Dict[str, Any]:
        """Predict with detailed output."""
        processed = self.preprocessor.process(text) if preprocess else text
        predictions = self.pipeline.predict([processed])[0]
        
        return {
            'original_text': text,
            'processed_text': processed,
            'predictions': predictions,
            'categories': [p[0] for p in predictions],
            'sentiments': [p[1] for p in predictions],
            'summary': self._format_predictions(predictions)
        }
    
    def _format_predictions(self, predictions: List[Tuple[str, str]]) -> str:
        """Format predictions as human-readable string."""
        if not predictions:
            return "No aspects detected"
        
        lines = []
        for category, sentiment in predictions:
            emoji = "😊" if sentiment == "positive" else "😞" if sentiment == "negative" else "😐"
            lines.append(f"{emoji} {category}: {sentiment}")
        return "\n".join(lines)
    
    def predict_batch(self, 
                      texts: List[str], 
                      preprocess: bool = True,
                      show_progress: bool = False) -> List[List[Tuple[str, str]]]:
        """Predict for a batch of texts."""
        if preprocess:
            if show_progress:
                try:
                    from tqdm import tqdm
                    texts = [self.preprocessor.process(t) for t in tqdm(texts, desc="Preprocessing")]
                except ImportError:
                    texts = [self.preprocessor.process(t) for t in texts]
            else:
                texts = [self.preprocessor.process(t) for t in texts]
        
        return self.pipeline.predict(texts)
    
    def close(self):
        """Clean up resources."""
        if hasattr(self.preprocessor, 'close'):
            self.preprocessor.close()
    
    @property
    def categories(self) -> List[str]:
        """Get supported categories."""
        return self.pipeline.categories
    
    @property
    def sentiments(self) -> List[str]:
        """Get supported sentiments."""
        return self.pipeline.sentiments
