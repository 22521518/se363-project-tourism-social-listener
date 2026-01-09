"""
ACSA model components: Aspect Category Detector and Aspect Sentiment Classifier.
"""
import numpy as np
import pickle
from typing import List, Dict, Optional, Tuple, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.preprocessing import MultiLabelBinarizer, LabelEncoder
from sklearn.metrics import (
    classification_report, accuracy_score, f1_score,
    hamming_loss, jaccard_score
)
from sklearn.model_selection import GridSearchCV


class AspectCategoryDetector:
    """
    Multi-label classifier for detecting aspect categories in reviews.
    Uses Binary SVM (One-vs-Rest) for each category.
    """
    
    def __init__(self, 
                 max_features: int = 5000, 
                 C: float = 1.0, 
                 class_weight: Optional[str] = None):
        self.vectorizer = TfidfVectorizer(
            max_features=max_features,
            ngram_range=(1, 2),
            lowercase=True,
            strip_accents='unicode'
        )
        self.mlb = MultiLabelBinarizer()
        self.classifiers: Dict[str, LinearSVC] = {}
        self.categories: Optional[np.ndarray] = None
        self.C = C
        self.class_weight = class_weight
        self.best_params: Dict[str, Dict] = {}
    
    def prepare_data(self, df) -> 'pd.DataFrame':
        """Group categories by comment for multi-label training."""
        import pandas as pd
        grouped = df.groupby('comment')['categories'].apply(list).reset_index()
        grouped.columns = ['comment', 'category_list']
        return grouped
    
    def fit(self, df, 
            tune_hyperparameters: bool = False,
            param_grid: Optional[Dict] = None) -> 'AspectCategoryDetector':
        """Train binary classifier for each category."""
        data = self.prepare_data(df)
        X = self.vectorizer.fit_transform(data['comment'])
        y = self.mlb.fit_transform(data['category_list'])
        self.categories = self.mlb.classes_
        
        print(f"Training ACD for categories: {self.categories}")
        
        if param_grid is None:
            param_grid = {'C': [0.1, 1.0, 10.0], 'class_weight': [None, 'balanced']}
        
        for idx, category in enumerate(self.categories):
            print(f"  Training classifier for {category}...")
            
            if tune_hyperparameters:
                base_clf = LinearSVC(max_iter=5000, random_state=42)
                grid_search = GridSearchCV(base_clf, param_grid, cv=3, scoring='f1', n_jobs=-1, verbose=0)
                grid_search.fit(X, y[:, idx])
                clf = grid_search.best_estimator_
                self.best_params[category] = grid_search.best_params_
            else:
                clf = LinearSVC(C=self.C, class_weight=self.class_weight, max_iter=5000, random_state=42)
                clf.fit(X, y[:, idx])
            
            self.classifiers[category] = clf
        
        return self
    
    def predict(self, comments: List[str]) -> List[List[str]]:
        """Predict categories for comments."""
        X = self.vectorizer.transform(comments)
        predictions = []
        
        for i in range(X.shape[0]):
            detected = []
            for category in self.categories:
                pred = self.classifiers[category].predict(X[i])
                if pred[0] == 1:
                    detected.append(category)
            
            if len(detected) == 0:
                detected = ['GENERAL']
            
            predictions.append(detected)
        
        return predictions
    
    def get_scores(self, df) -> Dict[str, float]:
        """Get evaluation scores as dictionary."""
        data = self.prepare_data(df)
        y_true = self.mlb.transform(data['category_list'])
        X = self.vectorizer.transform(data['comment'])
        y_pred = np.zeros_like(y_true)
        
        for idx, category in enumerate(self.categories):
            y_pred[:, idx] = self.classifiers[category].predict(X)
        
        return {
            'hamming_loss': hamming_loss(y_true, y_pred),
            'jaccard_micro': jaccard_score(y_true, y_pred, average='micro'),
            'jaccard_macro': jaccard_score(y_true, y_pred, average='macro')
        }
    
    def evaluate(self, df) -> Tuple[np.ndarray, np.ndarray]:
        """
        Evaluate ACD performance.
        
        Args:
            df: Test DataFrame
            
        Returns:
            Tuple of (y_true, y_pred)
        """
        data = self.prepare_data(df)
        y_true = self.mlb.transform(data['category_list'])
        
        X = self.vectorizer.transform(data['comment'])
        y_pred = np.zeros_like(y_true)
        
        for idx, category in enumerate(self.categories):
            y_pred[:, idx] = self.classifiers[category].predict(X)
        
        print("\n=== ACD Evaluation ===")
        print(f"Hamming Loss: {hamming_loss(y_true, y_pred):.4f}")
        print(f"Jaccard Score (micro): {jaccard_score(y_true, y_pred, average='micro'):.4f}")
        print(f"Jaccard Score (macro): {jaccard_score(y_true, y_pred, average='macro'):.4f}")
        
        return y_true, y_pred


class AspectSentimentClassifier:
    """
    Multi-class classifier for aspect sentiment classification.
    Classifies sentiment for (comment, category) pairs.
    """
    
    def __init__(self, 
                 max_features: int = 5000, 
                 C: float = 1.0, 
                 class_weight: Optional[str] = None):
        self.vectorizer = TfidfVectorizer(
            max_features=max_features,
            ngram_range=(1, 2),
            lowercase=True,
            strip_accents='unicode'
        )
        self.label_encoder = LabelEncoder()
        self.classifier: Optional[LinearSVC] = None
        self.C = C
        self.class_weight = class_weight
        self.best_params: Dict = {}
    
    def prepare_features(self, comments: List[str], categories: List[str]) -> List[str]:
        """Create features by concatenating comment with category."""
        return [f"{comment} [SEP] {category}" 
                for comment, category in zip(comments, categories)]
    
    def fit(self, df, 
            tune_hyperparameters: bool = False,
            param_grid: Optional[Dict] = None) -> 'AspectSentimentClassifier':
        """Train sentiment classifier."""
        X_text = self.prepare_features(df['comment'].values, df['categories'].values)
        X = self.vectorizer.fit_transform(X_text)
        y = self.label_encoder.fit_transform(df['sentiments'].values)
        
        print(f"\nTraining ASC for sentiments: {self.label_encoder.classes_}")
        print(f"Training samples: {len(y)}")
        
        if param_grid is None:
            param_grid = {'C': [0.1, 1.0, 10.0], 'class_weight': [None, 'balanced']}
        
        if tune_hyperparameters:
            base_clf = LinearSVC(max_iter=5000, random_state=42)
            grid_search = GridSearchCV(base_clf, param_grid, cv=3, scoring='f1_macro', n_jobs=-1, verbose=1)
            grid_search.fit(X, y)
            self.classifier = grid_search.best_estimator_
            self.best_params = grid_search.best_params_
        else:
            self.classifier = LinearSVC(C=self.C, class_weight=self.class_weight, max_iter=5000, random_state=42)
            self.classifier.fit(X, y)
        
        return self
    
    def predict(self, comments: List[str], categories: List[str]) -> np.ndarray:
        """Predict sentiments for (comment, category) pairs."""
        X_text = self.prepare_features(comments, categories)
        X = self.vectorizer.transform(X_text)
        y_pred = self.classifier.predict(X)
        return self.label_encoder.inverse_transform(y_pred)
    
    def get_scores(self, df) -> Dict[str, float]:
        """Get evaluation scores as dictionary."""
        X_text = self.prepare_features(df['comment'].values, df['categories'].values)
        X = self.vectorizer.transform(X_text)
        y_true = self.label_encoder.transform(df['sentiments'].values)
        y_pred = self.classifier.predict(X)
        
        return {
            'accuracy': accuracy_score(y_true, y_pred),
            'macro_f1': f1_score(y_true, y_pred, average='macro'),
            'micro_f1': f1_score(y_true, y_pred, average='micro')
        }
    
    def evaluate(self, df) -> Tuple[np.ndarray, np.ndarray]:
        """
        Evaluate ASC performance.
        
        Args:
            df: Test DataFrame
            
        Returns:
            Tuple of (y_true, y_pred)
        """
        X_text = self.prepare_features(
            df['comment'].values, 
            df['categories'].values
        )
        X = self.vectorizer.transform(X_text)
        y_true = self.label_encoder.transform(df['sentiments'].values)
        y_pred = self.classifier.predict(X)
        
        print("\n=== ASC Evaluation ===")
        print(f"Accuracy: {accuracy_score(y_true, y_pred):.4f}")
        print(f"Macro F1: {f1_score(y_true, y_pred, average='macro'):.4f}")
        print(f"Micro F1: {f1_score(y_true, y_pred, average='micro'):.4f}")
        print("\nClassification Report:")
        print(classification_report(
            y_true, y_pred, 
            target_names=self.label_encoder.classes_
        ))
        
        return y_true, y_pred

