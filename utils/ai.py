# using joblib to load spam detection model and vectorizer
import asyncio
import pickle
import joblib
import numpy as np
from config import logger
from utils.constants import threshold

try:
    spam_model = joblib.load("bin/spam_detection_svm_model.pkl")
    vectorizer = joblib.load("bin/tfidf_vectorizer.pkl")

    logger.info("Spam detection model and vectorizer loaded successfully!")

except Exception as e:
    logger.error(f"Error loading spam detection components: {str(e)}")
    raise RuntimeError("Failed to load spam detection model/vectorizer!")

# using pickle to load phishing detection model
try:
    with open("bin/model.pkl", "rb") as phishing_model_file:
        phishing_model = pickle.load(phishing_model_file)

    logger.info("Phishing detection model loaded successfully!")

except Exception as e:
    logger.error(f"Error loading phishing detection model: {str(e)}")
    raise RuntimeError("Failed to load phishing detection model!")

# the phishing detection needs a custom feature extractor
try:
    from feature_extraction import FeatureExtraction
    logger.info("Phishing feature extraction script loaded successfully!")

except Exception as e:
    logger.error(f"Error loading phishing feature extraction script: {str(e)}")
    raise RuntimeError("Failed to load phishing feature extraction script!")


async def detect_phishing(url: str):
	obj = await asyncio.to_thread(lambda: FeatureExtraction(url))
	x = np.array(obj.getFeaturesList()).reshape(1, 30)

	phishing_probability = await asyncio.to_thread(phishing_model.predict_proba, x)
	phishing_probability = round(phishing_probability[0,0] * 100, 2)

	logger.info(f"Phishing Prediction: {phishing_probability} | URL: {url}")
    
	return {
        "url": url,
		"phishing": True if phishing_probability >= threshold else False,
		"phishingProbability": phishing_probability,
	}

async def detect_spam(text: str):
	transformed_text = await asyncio.to_thread(vectorizer.transform, [text])
	spam_probability = await asyncio.to_thread(spam_model.predict_proba, transformed_text)
	spam_probability = round(spam_probability[0, 1] * 100, 2)
	
	logger.info(f"Spam Prediction: {spam_probability}")
     
	return {
		"text": text,
		"spam": True if spam_probability >= threshold else False,
		"spamProbability": spam_probability,
	}