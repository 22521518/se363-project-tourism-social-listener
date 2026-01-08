"""
Classifier for intention classification
"""
import os
import json
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification, AutoConfig
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
        # Clean up the path
        model_path = model_path.rstrip('/')
        
        # Verify path exists
        if not os.path.exists(model_path):
            raise ValueError(f"Model path does not exist: {model_path}")
        
        # Check for required files
        config_file = os.path.join(model_path, "config.json")
        if not os.path.exists(config_file):
            raise ValueError(f"config.json not found in {model_path}")
        
        self.device = device if device else ('cuda' if torch.cuda.is_available() else 'cpu')
        print(f"Loading intention model from {model_path} on device: {self.device}")
        
        try:
            # Set environment variables to force offline mode
            os.environ['HF_HUB_OFFLINE'] = '1'
            os.environ['TRANSFORMERS_OFFLINE'] = '1'
            
            # Load config first
            with open(config_file, 'r') as f:
                config_dict = json.load(f)
            
            # Create config object
            config = AutoConfig.from_pretrained(model_path, local_files_only=True)
            
            # Load tokenizer with config
            self.tokenizer = AutoTokenizer.from_pretrained(
                model_path,
                config=config,
                local_files_only=True,
                use_fast=True
            )
            
            # Load model with config
            self.model = AutoModelForSequenceClassification.from_pretrained(
                model_path,
                config=config,
                local_files_only=True
            )
            
        except Exception as e:
            print(f"Error loading model: {e}")
            print("Attempting alternative loading method...")
            
            # Alternative: Load components directly
            try:
                # Read config manually
                with open(config_file, 'r') as f:
                    config_dict = json.load(f)
                
                # Determine model architecture from config
                model_type = config_dict.get('model_type', 'bert')
                
                # Load using specific model class if available
                from transformers import BertTokenizer, BertForSequenceClassification
                from transformers import RobertaTokenizer, RobertaForSequenceClassification
                from transformers import DistilBertTokenizer, DistilBertForSequenceClassification
                
                if model_type == 'bert':
                    self.tokenizer = BertTokenizer.from_pretrained(model_path, local_files_only=True)
                    self.model = BertForSequenceClassification.from_pretrained(model_path, local_files_only=True)
                elif model_type == 'roberta':
                    self.tokenizer = RobertaTokenizer.from_pretrained(model_path, local_files_only=True)
                    self.model = RobertaForSequenceClassification.from_pretrained(model_path, local_files_only=True)
                elif model_type == 'distilbert':
                    self.tokenizer = DistilBertTokenizer.from_pretrained(model_path, local_files_only=True)
                    self.model = DistilBertForSequenceClassification.from_pretrained(model_path, local_files_only=True)
                else:
                    # Fallback to Auto classes
                    self.tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True)
                    self.model = AutoModelForSequenceClassification.from_pretrained(model_path, local_files_only=True)
                    
            except Exception as e2:
                raise RuntimeError(f"Failed to load model from {model_path}. Error: {e2}")
        
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