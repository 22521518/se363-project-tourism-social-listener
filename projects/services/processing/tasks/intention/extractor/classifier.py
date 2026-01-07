"""
Classifier for intention classification
"""

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from typing import List, Tuple, Optional


class IntentionClassifier:
    """Classifier for intention types"""
    
    def __init__(self, model_path: str = "models/intention_classifier", device: Optional[str] = None):
        """
        Initialize intention classifier with trained model.
        
        Args:
            model_path: Path to the trained model directory
            device: 'cuda', 'cpu', or None (auto-detect)
        """
        self.device = device or torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        print(f"Loading intention model from {model_path} on device: {self.device}")
        
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_path)
        self.model.to(self.device)
        self.model.eval()
        
        # Get id2label mapping
        self.id2label = {int(k): v for k, v in self.model.config.id2label.items()}
        
        print(f"Intention model loaded successfully with {len(self.id2label)} classes")
    
    def predict(self, text: str, max_length: int = 128) -> Tuple[str, float]:
        """
        Predict intention class for a single text.
        
        Args:
            text: Input text
            max_length: Maximum sequence length
            
        Returns:
            Tuple of (predicted_label, confidence)
        """
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=max_length,
            padding=True
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            probs = torch.softmax(outputs.logits, dim=1)
            pred_id = torch.argmax(probs).item()
            confidence = probs[0][pred_id].item()
        
        label = self.id2label[pred_id].lower()
        return label, confidence
    
    def predict_batch(
        self, 
        texts: List[str], 
        max_length: int = 128
    ) -> List[Tuple[str, float]]:
        """
        Predict intention classes for a batch of texts.
        
        Args:
            texts: List of input texts
            max_length: Maximum sequence length
            
        Returns:
            List of (predicted_label, confidence) tuples
        """
        if not texts:
            return []
        
        inputs = self.tokenizer(
            texts,
            return_tensors="pt",
            truncation=True,
            max_length=max_length,
            padding=True
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            probs = torch.softmax(outputs.logits, dim=1)
            pred_ids = torch.argmax(probs, dim=1).cpu().numpy()
            confidences = torch.max(probs, dim=1).values.cpu().numpy()
        
        results = []
        for pred_id, confidence in zip(pred_ids, confidences):
            label = self.id2label[int(pred_id)].lower()
            results.append((label, float(confidence)))
        
        return results


# Example usage
if __name__ == "__main__":
    # Initialize classifier
    intention_clf = IntentionClassifier()
    
    # Single prediction
    text = "How do I book a flight?"
    intention, conf = intention_clf.predict(text)
    print(f"Text: {text}")
    print(f"Intention: {intention} (confidence: {conf:.3f})\n")
    
    # Batch prediction
    texts = [
        "How do I book a flight?",
        "Your service is terrible!",
        "Thank you for helping me"
    ]
    
    print("Batch predictions:")
    results = intention_clf.predict_batch(texts)
    for text, (label, conf) in zip(texts, results):
        print(f"  {text[:40]:40s} → {label:12s} ({conf:.3f})")