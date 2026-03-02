"""
Multilingual Sentiment Intelligence Engine
Production-grade offline AI pipeline for civic feedback analysis
"""

import re
import logging
from typing import Dict, List, Tuple, Optional
from collections import Counter
from datetime import datetime, timezone
import numpy as np

# AI/ML libraries
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from langdetect import detect, LangDetectException
from sklearn.feature_extraction.text import TfidfVectorizer

logger = logging.getLogger(__name__)

class ModelManager:
    """
    Singleton pattern for model loading
    Loads models once at startup to avoid per-request overhead
    """
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not ModelManager._initialized:
            logger.info("Initializing Sentiment Models (one-time load)...")
            try:
                # English sentiment model (primary)
                self.en_tokenizer = AutoTokenizer.from_pretrained(
                    "cardiffnlp/twitter-roberta-base-sentiment-latest"
                )
                self.en_model = AutoModelForSequenceClassification.from_pretrained(
                    "cardiffnlp/twitter-roberta-base-sentiment-latest"
                )
                self.en_model.eval()
                logger.info("✅ English sentiment model loaded")
                
                # Multilingual sentiment model (fallback)
                self.ml_tokenizer = AutoTokenizer.from_pretrained(
                    "nlptown/bert-base-multilingual-uncased-sentiment"
                )
                self.ml_model = AutoModelForSequenceClassification.from_pretrained(
                    "nlptown/bert-base-multilingual-uncased-sentiment"
                )
                self.ml_model.eval()
                logger.info("✅ Multilingual sentiment model loaded")
                
                ModelManager._initialized = True
                
            except Exception as e:
                logger.error(f"Model loading failed: {e}")
                # Fallback to simple rule-based if models fail
                self.en_model = None
                self.ml_model = None
    
    def get_english_model(self):
        return self.en_tokenizer, self.en_model
    
    def get_multilingual_model(self):
        return self.ml_tokenizer, self.ml_model


class LanguageDetector:
    """Detect language using langdetect"""
    
    @staticmethod
    def detect_language(text: str) -> str:
        """
        Detect language from text
        Returns: 'en', 'hi', 'mr', or 'unknown'
        """
        try:
            lang_code = detect(text)
            
            # Map to our supported languages
            lang_map = {
                'en': 'English',
                'hi': 'Hindi',
                'mr': 'Marathi'
            }
            
            return lang_map.get(lang_code, 'English')
            
        except LangDetectException:
            logger.warning(f"Language detection failed for text: {text[:50]}")
            return 'English'


class TextCleaner:
    """Clean and normalize text for sentiment analysis"""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """
        Normalize text: lowercase, remove extra spaces, special chars
        """
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove URLs
        text = re.sub(r'http\S+|www\S+|https\S+', '', text)
        
        # Remove emails
        text = re.sub(r'\S+@\S+', '', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text


class SentimentAnalyzer:
    """Core sentiment analysis with hybrid model routing"""
    
    def __init__(self):
        self.model_manager = ModelManager()
    
    def analyze(self, text: str, language: str) -> Tuple[str, float]:
        """
        Run sentiment inference
        Returns: (sentiment_label, sentiment_score)
        
        sentiment_score: -1.0 (negative) to +1.0 (positive)
        """
        
        # Choose model based on language
        if language == 'English':
            return self._analyze_english(text)
        else:
            return self._analyze_multilingual(text)
    
    def _analyze_english(self, text: str) -> Tuple[str, float]:
        """Analyze using English model (cardiffnlp)"""
        
        tokenizer, model = self.model_manager.get_english_model()
        
        if model is None:
            # Fallback to rule-based
            return self._rule_based_sentiment(text)
        
        try:
            # Tokenize and run inference
            inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
            
            with torch.no_grad():
                outputs = model(**inputs)
                scores = outputs.logits[0]
                scores = torch.softmax(scores, dim=0).numpy()
            
            # cardiffnlp model: [negative, neutral, positive]
            negative, neutral, positive = scores
            
            # Calculate weighted score
            sentiment_score = (positive - negative)  # Range: -1 to 1
            
            # Determine label
            if sentiment_score > 0.3:
                label = "Positive"
            elif sentiment_score < -0.3:
                label = "Negative"
            else:
                label = "Neutral"
            
            return label, float(sentiment_score)
            
        except Exception as e:
            logger.error(f"English sentiment analysis failed: {e}")
            return self._rule_based_sentiment(text)
    
    def _analyze_multilingual(self, text: str) -> Tuple[str, float]:
        """Analyze using multilingual model (nlptown)"""
        
        tokenizer, model = self.model_manager.get_multilingual_model()
        
        if model is None:
            return self._rule_based_sentiment(text)
        
        try:
            inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
            
            with torch.no_grad():
                outputs = model(**inputs)
                scores = outputs.logits[0]
                scores = torch.softmax(scores, dim=0).numpy()
            
            # nlptown model: 1-star to 5-star (5 classes)
            # Map to sentiment: 1-2 = negative, 3 = neutral, 4-5 = positive
            star_scores = scores.tolist()
            predicted_stars = np.argmax(star_scores) + 1  # 1-5
            
            # Convert to -1 to 1 scale
            sentiment_score = (predicted_stars - 3) / 2  # Map 1-5 to -1 to 1
            
            if predicted_stars >= 4:
                label = "Positive"
            elif predicted_stars <= 2:
                label = "Negative"
            else:
                label = "Neutral"
            
            return label, float(sentiment_score)
            
        except Exception as e:
            logger.error(f"Multilingual sentiment analysis failed: {e}")
            return self._rule_based_sentiment(text)
    
    def _rule_based_sentiment(self, text: str) -> Tuple[str, float]:
        """Fallback rule-based sentiment for robustness"""
        
        positive_words = ['good', 'great', 'excellent', 'happy', 'thanks', 'love', 
                         'wonderful', 'amazing', 'best', 'better', 'improved']
        
        negative_words = ['bad', 'poor', 'terrible', 'issue', 'problem', 'broken',
                         'not working', 'complaint', 'worst', 'never', 'no']
        
        text_lower = text.lower()
        
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)
        
        if pos_count > neg_count:
            return "Positive", 0.5
        elif neg_count > pos_count:
            return "Negative", -0.5
        else:
            return "Neutral", 0.0


class KeywordExtractor:
    """Extract issue keywords using simple frequency-based approach"""
    
    # Stop words for filtering
    STOP_WORDS = set(['the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of', 'is', 
                      'are', 'was', 'were', 'been', 'be', 'have', 'has', 'had'])
    
    @staticmethod
    def extract_keywords(text: str, top_n: int = 5) -> List[str]:
        """
        Extract top keywords using word frequency
        Returns: List of keywords
        """
        
        # Clean text
        text_clean = TextCleaner.clean_text(text)
        
        # Tokenize
        words = re.findall(r'\b[a-z]{3,}\b', text_clean)
        
        # Filter stop words
        words = [w for w in words if w not in KeywordExtractor.STOP_WORDS]
        
        # Count frequency
        word_freq = Counter(words)
        
        # Get top N
        keywords = [word for word, _ in word_freq.most_common(top_n)]
        
        return keywords


class ScoreNormalizer:
    """Normalize sentiment scores to 0-100 scale"""
    
    @staticmethod
    def normalize(sentiment_score: float) -> float:
        """
        Convert -1 to 1 scale → 0 to 100 scale
        -1.0 → 0
         0.0 → 50
        +1.0 → 100
        """
        return ((sentiment_score + 1) / 2) * 100


# Main Pipeline Class
class SentimentPipeline:
    """
    Complete sentiment analysis pipeline
    Orchestrates all components
    """
    
    def __init__(self):
        self.language_detector = LanguageDetector()
        self.text_cleaner = TextCleaner()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.keyword_extractor = KeywordExtractor()
        self.score_normalizer = ScoreNormalizer()
    
    def process(self, text: str, language: Optional[str] = None) -> Dict:
        """
        Complete pipeline processing
        
        Returns:
        {
            'text': cleaned_text,
            'language': detected_language,
            'sentiment_label': Positive/Negative/Neutral,
            'sentiment_score': -1.0 to 1.0,
            'sentiment_score_normalized': 0 to 100,
            'keywords': [list of keywords]
        }
        """
        
        # Step 1: Clean text
        cleaned_text = self.text_cleaner.clean_text(text)
        
        # Step 2: Detect language
        if not language:
            language = self.language_detector.detect_language(cleaned_text)
        
        # Step 3: Run sentiment analysis
        sentiment_label, sentiment_score = self.sentiment_analyzer.analyze(cleaned_text, language)
        
        # Step 4: Normalize score
        normalized_score = self.score_normalizer.normalize(sentiment_score)
        
        # Step 5: Extract keywords
        keywords = self.keyword_extractor.extract_keywords(cleaned_text)
        
        return {
            'text': cleaned_text,
            'language': language,
            'sentiment_label': sentiment_label,
            'sentiment_score': sentiment_score,
            'sentiment_score_normalized': normalized_score,
            'keywords': keywords
        }


# Initialize models on module import (singleton)
try:
    _model_manager = ModelManager()
    logger.info("Sentiment models initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize sentiment models: {e}")
