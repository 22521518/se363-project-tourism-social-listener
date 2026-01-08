"""
Intention Extractor - Manages intention classification backends
Acts as a middle-man/orchestrator for intention classification only
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from enum import Enum

from  projects.services.processing.tasks.traveling_type.dto import ModelTravelingTypeDTO


class ExtractorBackend(str, Enum):
    """Available extraction backends"""
    LANGCHAIN = "langchain"
    TRANSFORMER = "transformer"


class BaseTravelingTypeExtractor(ABC):
    """Base class for traveling type extractors"""
    
    @abstractmethod
    def batch_extract_traveling_types(
        self, 
        items: List[ModelTravelingTypeDTO]
    ) -> List[Dict[str, str]]:
        """
        Extract traveling types from a batch of items.
        
        Returns:
            List of dicts with key: 'traveling_type'
        """
        pass


class LangChainTravelingTypeExtractor(BaseTravelingTypeExtractor):
    """Traveling type extractor using LangChain LLM service"""
    
    def __init__(self, model_config):
        from projects.services.processing.tasks.traveling_type.langchain.langchain import TravelingTypeExtractionService
        self.service = TravelingTypeExtractionService(model_config=model_config)
        print("LangChainTravelingTypeExtractor initialized")
    
    def batch_extract_traveling_types(
        self, 
        items: List[ModelTravelingTypeDTO]
    ) -> List[Dict[str, str]]:
        """Use LangChain to extract traveling types"""
        results = self.service.batch_extract_traveling_types(items)
        # Filter to only return traveling_type
        return [{"traveling_type": r.get("traveling_type")} for r in results]


class TransformerTravelingTypeExtractor(BaseTravelingTypeExtractor):
    """
    Traveling type extractor using trained transformer models.
    Acts as a manager for TravelingTypeClassifier.
    """
    
    def __init__(
        self, 
        model_path: str = "models/traveling_type_classifier",
        device: Optional[str] = None
    ):
        """
        Initialize transformer-based intention extractor.
        
        Args:
            model_path: Path to intention classifier model
            device: 'cuda', 'cpu', or None (auto-detect)
        """
        from projects.services.processing.tasks.traveling_type.extractor.classifier import TravelingTypeClassifier

        print("Initializing TransformerTravelingTypeExtractor...")
        self.classifier = TravelingTypeClassifier(
            model_path=model_path,
            device=device
        )
        print("TransformerTravelingTypeExtractor initialized successfully")
    
    def batch_extract_traveling_types(
        self, 
        items: List[ModelTravelingTypeDTO]
    ) -> List[Dict[str, str]]:
        """
        Extract traveling types using transformer model.
        
        Args:
            items: List of items to classify
            
        Returns:
            List of dicts with 'traveling_type'
        """
        if not items:
            return []
        
        # Extract texts from items
        texts = [item.text for item in items]
        
        # Predict traveling types (batch)
        results = self.classifier.predict_batch(texts)
        traveling_types = [label for label, conf in results]
        
        # Build results
        return [{"traveling_type": traveling_type} for traveling_type in traveling_types]
    
    def get_confidence_batch(self, items: List[ModelTravelingTypeDTO]) -> List[float]:
        """Get confidence scores for batch predictions"""
        if not items:
            return []
        
        texts = [item.text for item in items]
        results = self.classifier.predict_batch(texts)
        return [conf for label, conf in results]


class HybridTravelingTypeExtractor(BaseTravelingTypeExtractor):
    """
    Hybrid traveling type extractor that uses transformer for fast prediction
    and falls back to LangChain for low-confidence cases.
    """
    
    def __init__(
        self,
        model_config,
        model_path: str = "models/traveling_type_classifier",
        confidence_threshold: float = 0.7,
        device: Optional[str] = None
    ):
        """
        Initialize hybrid traveling type extractor.
        
        Args:
            model_config: Config for LangChain fallback
            model_path: Path to traveling type classifier
            confidence_threshold: Minimum confidence to trust transformer
            device: Device to use for transformers
        """
        print("Initializing HybridIntentionExtractor...")
        
        self.transformer = TransformerTravelingTypeExtractor(
            model_path=model_path,
            device=device
        )
        self.langchain = LangChainTravelingTypeExtractor(model_config)
        self.confidence_threshold = confidence_threshold
        
        print(f"HybridIntentionExtractor initialized with threshold: {confidence_threshold}")
    
    def batch_extract_traveling_types(
        self, 
        items: List[ModelTravelingTypeDTO]
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
            langchain_results = self.langchain.batch_extract_traveling_types(low_confidence_items)
            
            # Replace low confidence predictions
            for idx, langchain_result in zip(low_confidence_indices, langchain_results):
                transformer_results[idx] = langchain_result
        
        return transformer_results


class TravelingTypeExtractorFactory:
    """Factory to create traveling type extractors based on configuration"""
    
    @staticmethod
    def create(
        backend: ExtractorBackend,
        model_config=None,
        model_path: str = "models/traveling_type_classifier",
        confidence_threshold: float = 0.7,
        device: Optional[str] = None
    ) -> BaseTravelingTypeExtractor:
        """
        Create a traveling type extractor instance.
        
        Args:
            backend: Which backend to use
            model_config: Config for LangChain (required for langchain/hybrid)
            model_path: Path to traveling type model (for transformer/hybrid)
            confidence_threshold: For hybrid mode
            device: Device for transformers ('cuda' or 'cpu')
        
        Returns:
            A traveling type extractor instance
        """
        if backend == ExtractorBackend.LANGCHAIN:
            if not model_config:
                raise ValueError("model_config required for LangChain backend")
            return LangChainTravelingTypeExtractor(model_config)
        
        elif backend == ExtractorBackend.TRANSFORMER:
            return TransformerTravelingTypeExtractor(
                model_path=model_path,
                device=device
            )
        
        elif backend == "hybrid":
            if not model_config:
                raise ValueError("model_config required for Hybrid backend")
            return HybridTravelingTypeExtractor(
                model_config=model_config,
                model_path=model_path,
                confidence_threshold=confidence_threshold,
                device=device
            )
        
        else:
            raise ValueError(f"Unknown backend: {backend}")


def create_traveling_type_extractor(
    backend: str = "transformer",
    **kwargs
) -> BaseTravelingTypeExtractor:
    """
    Convenience function to create a traveling type extractor.
    
    Examples:
        # Use transformer model
        extractor = create_traveling_type_extractor("transformer")
        
        # Use LangChain
        extractor = create_traveling_type_extractor("langchain", model_config=config)
        
        # Use hybrid approach
        extractor = create_traveling_type_extractor(
            "hybrid", 
            model_config=config,
            confidence_threshold=0.8
        )
    """
    backend_enum = ExtractorBackend(backend) if backend != "hybrid" else "hybrid"
    return TravelingTypeExtractorFactory.create(backend_enum, **kwargs)