"""
Model Download Script for ICIOS
Downloads and caches all required AI models locally.
"""

import os
import logging
from transformers import pipeline
from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def download_sentiment_model():
    """Download the sentiment analysis model and cache it."""
    logger.info("Downloading sentiment model (cardiffnlp/twitter-roberta-base-sentiment-latest)...")
    try:
        classifier = pipeline(
            "sentiment-analysis",
            model="cardiffnlp/twitter-roberta-base-sentiment-latest",
            cache_dir=settings.MODEL_CACHE_DIR
        )
        logger.info("✅ Sentiment model cached successfully!")
    except Exception as e:
        logger.error(f"❌ Failed to download sentiment model: {e}")
        raise

def download_multilingual_model():
    """Download a multilingual model for sentiment (optional, fallback)."""
    logger.info("Downloading multilingual sentiment model (nlptown/bert-base-multilingual-uncased-sentiment)...")
    try:
        classifier = pipeline(
            "sentiment-analysis",
            model="nlptown/bert-base-multilingual-uncased-sentiment",
            cache_dir=settings.MODEL_CACHE_DIR
        )
        logger.info("✅ Multilingual model cached successfully!")
    except Exception as e:
        logger.warning(f"⚠️ Could not download multilingual model: {e}")

def download_language_detection_model():
    """Download language detection model (if using a transformer-based one)."""
    # Currently we use langdetect, which doesn't require download.
    # If we switch to a transformer model, add it here.
    pass

if __name__ == "__main__":
    # Ensure cache directory exists
    os.makedirs(settings.MODEL_CACHE_DIR, exist_ok=True)
    logger.info(f"Model cache directory: {settings.MODEL_CACHE_DIR}")

    download_sentiment_model()
    download_multilingual_model()  # optional

    logger.info("All models downloaded successfully.")