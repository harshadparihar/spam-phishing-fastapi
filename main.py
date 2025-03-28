import pickle
import joblib
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Load Spam Detection Model & Vectorizer using joblib
try:
    spam_model = joblib.load("bin/spam_detection_svm_model.pkl")
    vectorizer = joblib.load("bin/tfidf_vectorizer.pkl")

    logger.info("Spam detection model and vectorizer loaded successfully!")

except Exception as e:
    logger.error(f"Error loading spam detection components: {str(e)}")
    raise RuntimeError("Failed to load spam detection model/vectorizer!")

# Load Phishing Detection Model
try:
    with open("bin/model.pkl", "rb") as phishing_model_file:
        phishing_model = pickle.load(phishing_model_file)

    logger.info("Phishing detection model loaded successfully!")

except Exception as e:
    logger.error(f"Error loading phishing detection model: {str(e)}")
    raise RuntimeError("Failed to load phishing detection model!")

# # Import Custom Feature Extraction Code
# try:
#     from phishing_feature_extraction import extract_features  # Ensure this script is in the same directory
#     logger.info("Phishing feature extraction script loaded successfully!")

# except Exception as e:
#     logger.error(f"Error loading phishing feature extraction script: {str(e)}")
#     raise RuntimeError("Failed to load phishing feature extraction script!")

# # Initialize FastAPI app
# app = FastAPI(title="Spam & Phishing Detection API", version="1.0")

# # Enable CORS
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # Change this for better security
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Define Input Models
# class SpamInput(BaseModel):
#     text: str

# class PhishingInput(BaseModel):
#     url: str

# # Root Route
# @app.get("/")
# async def root():
#     return {"message": "Spam & Phishing Detection API is running!"}

# # Spam Detection Route
# @app.post("/predict/spam")
# async def predict_spam(data: SpamInput):
#     text = data.text.strip()

#     if not text:
#         logger.warning("Empty text received for spam prediction.")
#         raise HTTPException(status_code=400, detail="No text provided")

#     try:
#         transformed_text = vectorizer.transform([text])
#         prediction = spam_model.predict(transformed_text)[0]
#         result = "spam" if prediction == 1 else "not spam"

#         logger.info(f"Spam Prediction: {result} | Text: {text[:30]}...")
#         return {"prediction": result}

#     except Exception as e:
#         logger.error(f"Error during spam prediction: {str(e)}")
#         raise HTTPException(status_code=500, detail="Spam prediction failed due to server error")

# # Phishing Detection Route
# @app.post("/predict/phishing")
# async def predict_phishing(data: PhishingInput):
#     url = data.url.strip()

#     if not url:
#         logger.warning("Empty URL received for phishing prediction.")
#         raise HTTPException(status_code=400, detail="No URL provided")

#     try:
#         # Extract features using custom function
#         features = extract_features(url)
#         features_array = np.array(features).reshape(1, -1)  # Ensure correct shape

#         prediction = phishing_model.predict(features_array)[0]
#         result = "phishing" if prediction == 1 else "not phishing"

#         logger.info(f"Phishing Prediction: {result} | URL: {url}")
#         return {"prediction": result}

#     except Exception as e:
#         logger.error(f"Error during phishing prediction: {str(e)}")
#         raise HTTPException(status_code=500, detail="Phishing prediction failed due to server error")

# # Run the API locally
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
