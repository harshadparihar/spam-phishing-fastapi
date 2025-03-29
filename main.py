import pickle
import joblib
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware
import numpy as np
import tldextract

# configuring proper logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# using joblib to load spam detection model and vectorizer
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

# initializing fastapi app
app = FastAPI(title="Spam & Phishing Detection API", version="1.0")

# enabling cors
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: check if needs to be changed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# defining input models
class SpamInput(BaseModel):
    text: str

class PhishingInput(BaseModel):
    url: str

# helper function
def extract_urls(text):
    words = text.split()
    urls = []

    # iterating in reverse to preserve index
    for i in range(len(words) - 1, -1, -1):
        extracted = tldextract.extract(words[i])

        # url found
        if extracted.domain and extracted.suffix:
            urls.append(words.pop(i))

    clean_text = " ".join(words)
    return clean_text, urls

# root / health check
@app.get("/")
async def root():
    return {"message": "Spam & Phishing Detection API is running!"}


# phishing detection
@app.post("/predict/phishing")
async def predict_phishing(data: PhishingInput):
    url = data.url.strip()

    if not url:
        logger.warning("Empty URL received for phishing prediction.")
        raise HTTPException(status_code=400, detail="No URL provided")

    try:
        obj = FeatureExtraction(url)
        x = np.array(obj.getFeaturesList()).reshape(1, 30)

        # y_pred = phishing_model.predict(x)[0] # 1 is safe, -1 is unsafe
        phishing_probability = phishing_model.predict_proba(x)[0, 0]
        # y_pro_non_phishing = phishing_model.predict_proba(x)[0, 1]
        
        result = {
            "url": url,
            # "safe": True if y_pred == 1 else False,
            "phishingProbability": round(phishing_probability * 100, 2),
            # "nonPhishingProbability": round(y_pro_non_phishing * 100, 2)
        }
        
        logger.info(f"Phishing Prediction: {result['phishingProbability']} | URL: {url}")
        return result
    
    except Exception as e:
        logger.error(f"Error during phishing prediction: {str(e)}")
        raise HTTPException(status_code=500, detail="Phishing prediction failed due to server error")


# spam detection
@app.post("/predict/spam")
async def predict_spam(data: SpamInput):
    text = data.text.strip()

    if not text:
        logger.warning("Empty text received for spam prediction.")
        raise HTTPException(status_code=400, detail="No text provided")
    
    clean_text, _ = extract_urls(text)

    if not clean_text:
        logger.warning("Only URLs received for spam prediction.")
        raise HTTPException(status_code=400, detail="Only URLs provided")

    try:
        transformed_text = vectorizer.transform([clean_text])
        spam_probability = spam_model.predict_proba(transformed_text)[0, 0]

        result = {
            "text": clean_text,
            "spamProbability": round(spam_probability * 100, 2)
        }

        logger.info(f"Spam Prediction: {result['spamProbability']}")
        return result

    except Exception as e:
        logger.error(f"Error during spam prediction: {str(e)}")
        raise HTTPException(status_code=500, detail="Spam prediction failed due to server error")

# running api on localhost
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
