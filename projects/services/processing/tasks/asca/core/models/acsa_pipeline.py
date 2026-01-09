"""
Complete ACSA Pipeline combining ACD and ASC stages.
"""
import json
import pickle
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any, Union
import pandas as pd

from .components import AspectCategoryDetector, AspectSentimentClassifier


class ACSAPipeline:
    """
    Complete 2-stage pipeline for Aspect Category Sentiment Analysis.
    
    Stage 1: Aspect Category Detection (ACD) - Multi-label classification
    Stage 2: Aspect Sentiment Classification (ASC) - Multi-class classification
    """
    
    def __init__(self, 
                 max_features_acd: int = 5000, 
                 max_features_asc: int = 5000):
        self.acd = AspectCategoryDetector(max_features=max_features_acd)
        self.asc = AspectSentimentClassifier(max_features=max_features_asc)
        self.training_history: Dict[str, Any] = {
            'train_time': None,
            'acd_best_params': {},
            'asc_best_params': {},
            'val_scores': {},
            'test_scores': {}
        }
    
    def fit(self, 
            train_df: pd.DataFrame, 
            val_df: Optional[pd.DataFrame] = None,
            tune_hyperparameters: bool = False,
            train_acd: bool = True,
            train_asc: bool = True) -> 'ACSAPipeline':
        """Train pipeline stages."""
        import time
        
        if not train_acd and not train_asc:
            print("Warning: Both stages are frozen. Nothing to train.")
            return self
        
        start_time = time.time()
        
        if train_acd:
            print("=" * 50)
            print("TRAINING STAGE 1: Aspect Category Detection")
            print("=" * 50)
            self.acd.fit(train_df, tune_hyperparameters=tune_hyperparameters)
        
        if train_asc:
            print("\n" + "=" * 50)
            print("TRAINING STAGE 2: Aspect Sentiment Classification")
            print("=" * 50)
            self.asc.fit(train_df, tune_hyperparameters=tune_hyperparameters)
        
        self.training_history['train_time'] = time.time() - start_time
        print(f"\n✓ Training completed in {self.training_history['train_time']:.2f} seconds")
        
        return self
    
    def predict(self, comments: Union[str, List[str]]) -> List[List[Tuple[str, str]]]:
        """
        Predict (category, sentiment) pairs for each comment.
        
        Args:
            comments: Single comment or list of comments
            
        Returns:
            List of lists containing (category, sentiment) tuples
        """
        if isinstance(comments, str):
            comments = [comments]
        
        # Stage 1: Detect categories
        detected_categories = self.acd.predict(comments)
        
        # Stage 2: Classify sentiment for each detected category
        results = []
        for comment, categories in zip(comments, detected_categories):
            pairs = []
            if len(categories) > 0:
                comments_repeated = [comment] * len(categories)
                sentiments = self.asc.predict(comments_repeated, categories)
                pairs = list(zip(categories, sentiments))
            results.append(pairs)
        
        return results
    
    def predict_single(self, comment: str) -> List[Tuple[str, str]]:
        """Predict for a single comment."""
        results = self.predict([comment])
        return results[0] if results else []
    
    def save(self, filepath: Union[str, Path]) -> None:
        """Save trained pipeline to file."""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'wb') as f:
            pickle.dump(self, f)
        print(f"\n✓ Pipeline saved to {filepath}")
    
    @staticmethod
    def load(filepath: Union[str, Path]) -> 'ACSAPipeline':
        """Load trained pipeline from file.
        
        Handles models trained with 'src.*' imports by creating module aliases.
        """
        import sys
        import types
        
        # Create module aliases for 'src' to handle pickles trained with src.* imports
        # This allows pickle.load to find the classes in the correct location
        if 'src' not in sys.modules:
            src_module = types.ModuleType('src')
            sys.modules['src'] = src_module
        else:
            src_module = sys.modules['src']
        
        # Import using relative imports from the core module
        # . = models, .. = core
        from . import components
        from .. import models as core_models
        from .. import preprocessing as core_preprocessing
        
        # Alias src.models -> core/models module
        sys.modules['src.models'] = core_models
        sys.modules['src.models.components'] = components
        sys.modules['src.models.acsa_pipeline'] = sys.modules[__name__]
        if not hasattr(src_module, 'models'):
            src_module.models = core_models
        
        # Alias src.preprocessing -> core/preprocessing module
        sys.modules['src.preprocessing'] = core_preprocessing
        if not hasattr(src_module, 'preprocessing'):
            src_module.preprocessing = core_preprocessing
        
        with open(filepath, 'rb') as f:
            pipeline = pickle.load(f)
        print(f"✓ Pipeline loaded from {filepath}")
        return pipeline
    
    @property
    def categories(self) -> List[str]:
        """Get detected categories."""
        return list(self.acd.categories) if self.acd.categories is not None else []
    
    @property
    def sentiments(self) -> List[str]:
        """Get sentiment labels."""
        return list(self.asc.label_encoder.classes_) if self.asc.label_encoder else []
