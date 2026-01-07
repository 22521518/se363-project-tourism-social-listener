"""
Intention Extractor - Manages intention classification backends
Acts as a middle-man/orchestrator for intention classification only
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from enum import Enum

from projects.services.processing.tasks.intention.dto import ModelIntentionDTO


class ExtractorBackend(str, Enum):
    """Available extraction backends"""
    LANGCHAIN = "langchain"
    TRANSFORMER = "transformer"


class BaseIntentionExtractor(ABC):
    """Base class for intention extractors"""
    
    @abstractmethod
    def batch_extract_intentions(
        self, 
        items: List[ModelIntentionDTO]
    ) -> List[Dict[str, str]]:
        """
        Extract intentions from a batch of items.
        
        Returns:
            List of dicts with key: 'intention_type'
        """
        pass


class LangChainIntentionExtractor(BaseIntentionExtractor):
    """Intention extractor using LangChain LLM service"""
    
    def __init__(self, model_config):
        from projects.services.processing.tasks.intention.langchain.langchain import IntentionExtractionService
        self.service = IntentionExtractionService(model_config=model_config)
        print("LangChainIntentionExtractor initialized")
    
    def batch_extract_intentions(
        self, 
        items: List[ModelIntentionDTO]
    ) -> List[Dict[str, str]]:
        """Use LangChain to extract intentions"""
        results = self.service.batch_extract_intentions(items)
        # Filter to only return intention_type
        return [{"intention_type": r.get("intention_type")} for r in results]


class TransformerIntentionExtractor(BaseIntentionExtractor):
    """
    Intention extractor using trained transformer models.
    Acts as a manager for IntentionClassifier.
    """
    
    def __init__(
        self, 
        model_path: str = "models/intention_classifier",
        device: Optional[str] = None
    ):
        """
        Initialize transformer-based intention extractor.
        
        Args:
            model_path: Path to intention classifier model
            device: 'cuda', 'cpu', or None (auto-detect)
        """
        from projects.services.processing.tasks.intention.classifier import IntentionClassifier
        
        print("Initializing TransformerIntentionExtractor...")
        self.classifier = IntentionClassifier(
            model_path=model_path,
            device=device
        )
        print("TransformerIntentionExtractor initialized successfully")
    
    def batch_extract_intentions(
        self, 
        items: List[ModelIntentionDTO]
    ) -> List[Dict[str, str]]:
        """
        Extract intentions using transformer model.
        
        Args:
            items: List of items to classify
            
        Returns:
            List of dicts with 'intention_type'
        """
        if not items:
            return []
        
        # Extract texts from items
        texts = [item.text for item in items]
        
        # Predict intentions (batch)
        results = self.classifier.predict_batch(texts)
        intentions = [label for label, conf in results]
        
        # Build results
        return [{"intention_type": intention} for intention in intentions]
    
    def get_confidence_batch(self, items: List[ModelIntentionDTO]) -> List[float]:
        """Get confidence scores for batch predictions"""
        if not items:
            return []
        
        texts = [item.text for item in items]
        results = self.classifier.predict_batch(texts)
        return [conf for label, conf in results]


class HybridIntentionExtractor(BaseIntentionExtractor):
    """
    Hybrid intention extractor that uses transformer for fast prediction
    and falls back to LangChain for low-confidence cases.
    """
    
    def __init__(
        self,
        model_config,
        model_path: str = "models/intention_classifier",
        confidence_threshold: float = 0.7,
        device: Optional[str] = None
    ):
        """
        Initialize hybrid intention extractor.
        
        Args:
            model_config: Config for LangChain fallback
            model_path: Path to intention classifier
            confidence_threshold: Minimum confidence to trust transformer
            device: Device to use for transformers
        """
        print("Initializing HybridIntentionExtractor...")
        
        self.transformer = TransformerIntentionExtractor(
            model_path=model_path,
            device=device
        )
        self.langchain = LangChainIntentionExtractor(model_config)
        self.confidence_threshold = confidence_threshold
        
        print(f"HybridIntentionExtractor initialized with threshold: {confidence_threshold}")
    
    def batch_extract_intentions(
        self, 
        items: List[ModelIntentionDTO]
    ) -> List[Dict[str, str]]:
        """
        Use transformer first, fall back to LangChain for low confidence.
        """
        if not items:
            return []
        
        # Get transformer predictions
        transformer_results = self.transformer.batch_extract_intentions(items)
        confidences = self.transformer.get_confidence_batch(items)
        
        # Identify low confidence items
        low_confidence_items = []
        low_confidence_indices = []
        
        for i, confidence in enumerate(confidences):
            if confidence < self.confidence_threshold:
                low_confidence_items.append(items[i])
                low_confidence_indices.append(i)
        
        # Use LangChain for low confidence items
        if low_confidence_items:
            print(f"Using LangChain fallback for {len(low_confidence_items)} low-confidence items")
            langchain_results = self.langchain.batch_extract_intentions(low_confidence_items)
            
            # Replace low confidence predictions
            for idx, langchain_result in zip(low_confidence_indices, langchain_results):
                transformer_results[idx] = langchain_result
        
        return transformer_results


class IntentionExtractorFactory:
    """Factory to create intention extractors based on configuration"""
    
    @staticmethod
    def create(
        backend: ExtractorBackend,
        model_config=None,
        model_path: str = "models/intention_classifier",
        confidence_threshold: float = 0.7,
        device: Optional[str] = None
    ) -> BaseIntentionExtractor:
        """
        Create an intention extractor instance.
        
        Args:
            backend: Which backend to use
            model_config: Config for LangChain (required for langchain/hybrid)
            model_path: Path to intention model (for transformer/hybrid)
            confidence_threshold: For hybrid mode
            device: Device for transformers ('cuda' or 'cpu')
        
        Returns:
            An intention extractor instance
        """
        if backend == ExtractorBackend.LANGCHAIN:
            if not model_config:
                raise ValueError("model_config required for LangChain backend")
            return LangChainIntentionExtractor(model_config)
        
        elif backend == ExtractorBackend.TRANSFORMER:
            return TransformerIntentionExtractor(
                model_path=model_path,
                device=device
            )
        
        elif backend == "hybrid":
            if not model_config:
                raise ValueError("model_config required for Hybrid backend")
            return HybridIntentionExtractor(
                model_config=model_config,
                model_path=model_path,
                confidence_threshold=confidence_threshold,
                device=device
            )
        
        else:
            raise ValueError(f"Unknown backend: {backend}")


def create_intention_extractor(
    backend: str = "transformer",
    **kwargs
) -> BaseIntentionExtractor:
    """
    Convenience function to create an intention extractor.
    
    Examples:
        # Use transformer model
        extractor = create_intention_extractor("transformer")
        
        # Use LangChain
        extractor = create_intention_extractor("langchain", model_config=config)
        
        # Use hybrid approach
        extractor = create_intention_extractor(
            "hybrid", 
            model_config=config,
            confidence_threshold=0.8
        )
    """
    backend_enum = ExtractorBackend(backend) if backend != "hybrid" else "hybrid"
    return IntentionExtractorFactory.create(backend_enum, **kwargs)