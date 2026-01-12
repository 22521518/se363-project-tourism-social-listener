"""
English text processor for ACSA.
"""
import re
import string
from typing import Optional

from .base import TextProcessor


class EnglishTextProcessor(TextProcessor):
    """English text processor."""
    
    def __init__(self, use_nltk: bool = True):
        """
        Initialize English text processor.
        
        Args:
            use_nltk: Whether to use NLTK for tokenization
        """
        self.use_nltk = use_nltk
        self._tokenizer = None
    
    @property
    def tokenizer(self):
        """Lazy load NLTK tokenizer."""
        if self._tokenizer is None and self.use_nltk:
            try:
                import nltk
                nltk.download('punkt', quiet=True)
                from nltk.tokenize import word_tokenize
                self._tokenizer = word_tokenize
            except ImportError:
                self._tokenizer = None
        return self._tokenizer
    
    def lowercase(self, text: str) -> str:
        """Convert text to lowercase."""
        return text.lower()
    
    def remove_punctuation(self, text: str) -> str:
        """Remove punctuation from text."""
        translator = str.maketrans(string.punctuation, ' ' * len(string.punctuation))
        return text.translate(translator)
    
    def remove_extra_spaces(self, text: str) -> str:
        """Remove extra whitespace."""
        return ' '.join(text.split())
    
    def process_emojis(self, text: str) -> str:
        """Convert common emojis to sentiment labels."""
        emojis_map = {
            ':)': 'positive', ':-)': 'positive', ':(': 'negative',
            ':-(': 'negative', ':D': 'positive', ':-D': 'positive',
            ';)': 'positive', ';-)': 'positive', ':/': 'negative',
            ':-/': 'negative', ':P': 'positive', ':-P': 'positive',
            '<3': 'positive', '</3': 'negative',
            '👍': 'positive', '👎': 'negative', '❤': 'positive',
            '😊': 'positive', '😢': 'negative', '😡': 'negative',
            '😍': 'positive', '😭': 'negative', '🎉': 'positive',
        }
        for emoji, sentiment in emojis_map.items():
            text = text.replace(emoji, f' EMO{sentiment.upper()} ')
        return text
    
    def expand_contractions(self, text: str) -> str:
        """Expand common English contractions."""
        contractions = {
            "won't": "will not", "can't": "cannot", "n't": " not",
            "'re": " are", "'s": " is", "'d": " would", "'ll": " will",
            "'ve": " have", "'m": " am", "ain't": "is not",
            "aren't": "are not", "couldn't": "could not",
            "didn't": "did not", "doesn't": "does not",
            "don't": "do not", "hadn't": "had not", "hasn't": "has not",
            "haven't": "have not", "isn't": "is not",
        }
        for contraction, expansion in contractions.items():
            text = re.sub(re.escape(contraction), expansion, text, flags=re.IGNORECASE)
        return text
    
    def clean_text(self, text: str) -> str:
        """Full text cleaning pipeline."""
        if not isinstance(text, str):
            return ""
        
        text = self.lowercase(text)
        text = self.process_emojis(text)
        text = self.expand_contractions(text)
        text = self.remove_punctuation(text)
        text = self.remove_extra_spaces(text)
        
        return text.strip()
    
    def tokenize(self, text: str) -> str:
        """Tokenize text using NLTK or simple split."""
        if not text.strip():
            return ""
        
        if self.tokenizer:
            try:
                tokens = self.tokenizer(text)
                return ' '.join(tokens)
            except Exception:
                pass
        
        # Fallback to simple split
        return ' '.join(text.split())
