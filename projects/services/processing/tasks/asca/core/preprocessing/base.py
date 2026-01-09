"""
Abstract base class for text processors.
All language-specific processors should inherit from this.
"""
from abc import ABC, abstractmethod
from typing import List
import pandas as pd


class TextProcessor(ABC):
    """Abstract base class for text preprocessing."""
    
    @abstractmethod
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text.
        
        Args:
            text: Raw input text
            
        Returns:
            Cleaned text
        """
        pass
    
    @abstractmethod
    def tokenize(self, text: str) -> str:
        """
        Tokenize/segment text.
        
        Args:
            text: Cleaned text
            
        Returns:
            Tokenized text (words separated by spaces)
        """
        pass
    
    def process(self, text: str) -> str:
        """
        Full processing pipeline: clean + tokenize.
        
        Args:
            text: Raw input text
            
        Returns:
            Fully processed text
        """
        if not isinstance(text, str) or not text.strip():
            return ""
        cleaned = self.clean_text(text)
        tokenized = self.tokenize(cleaned)
        return tokenized
    
    def process_batch(self, texts: List[str]) -> List[str]:
        """
        Process a batch of texts.
        
        Args:
            texts: List of raw texts
            
        Returns:
            List of processed texts
        """
        return [self.process(text) for text in texts]
    
    def process_dataframe(self, df: pd.DataFrame, text_column: str = 'comment',
                          output_column: str = None) -> pd.DataFrame:
        """
        Process a DataFrame column.
        
        Args:
            df: Input DataFrame
            text_column: Column containing text to process
            output_column: Column name for processed text (default: same as text_column)
            
        Returns:
            DataFrame with processed text
        """
        df = df.copy()
        output_column = output_column or text_column
        df[output_column] = df[text_column].apply(self.process)
        return df
