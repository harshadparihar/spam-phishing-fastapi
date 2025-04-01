# defining input models
import asyncio
import pickle
from typing import Optional, Tuple
from bson import ObjectId
import joblib
import numpy as np
from pydantic import BaseModel
import tldextract
from fastapi import APIRouter, Depends, HTTPException
from config import Orgs, Users, logger
from dependencies import get_org_or_user
from models import OrgSchema, UserSchema
from utils.constants import APIKeyType, LicenseType, threshold


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

# fastapi router
router = APIRouter(prefix="/predict", tags=["Predict"])

# phishing detection
@router.post("/phishing")
async def predict_phishing(
    data: PhishingInput,
    auth_data: Tuple[APIKeyType, Optional[OrgSchema], Optional[UserSchema]] = Depends(get_org_or_user)
):
    api_key_type, _, user = auth_data

    # RBAC
    if api_key_type != APIKeyType.USR:
        raise HTTPException(status_code=403, detail="Detection can only be done with user api keys")
    
    org = await Orgs.find_one({"_id": ObjectId(user.orgID)})
    if org and org["licenseType"] == LicenseType.SD:
        raise HTTPException(status_code=403, detail="Organization's license doesn't include this endpoint")
    
    url = data.url.strip()

    if not url:
        logger.warning("Empty URL received for phishing prediction.")
        raise HTTPException(status_code=400, detail="No URL provided")

    try:
        obj = await asyncio.to_thread(lambda: FeatureExtraction(url))
        x = np.array(obj.getFeaturesList()).reshape(1, 30)

        phishing_probability = await asyncio.to_thread(phishing_model.predict_proba, x)
        phishing_probability = round(phishing_probability[0,0] * 100, 2)
        
        result = {
            "url": url,
            "phishing": True if phishing_probability >= threshold else False,
            "phishingProbability": phishing_probability,
        }
        
        user.reqCount += 1
        if result["phishing"]:
            user.phishingCount += 1

        user_dict = user.model_dump(by_alias=True, exclude={"id"})
        update_result = await Users.update_one(
            {"username": user.username, "orgID": ObjectId(user.orgID)}, 
            {"$set": user_dict}
        )
        if update_result.modified_count == 0:
            raise HTTPException(status_code=409, detail="Failed to update counts for user")

        logger.info(f"Phishing Prediction: {result['phishingProbability']} | URL: {url}")
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during phishing prediction: {str(e)}")
        raise HTTPException(status_code=500, detail="Phishing prediction failed due to server error")


# spam detection
@router.post("/spam")
async def predict_spam(
    data: SpamInput,
    auth_data: Tuple[APIKeyType, Optional[OrgSchema], Optional[UserSchema]] = Depends(get_org_or_user)
):
    api_key_type, _, user = auth_data

    # RBAC
    if api_key_type != APIKeyType.USR:
        raise HTTPException(status_code=403, detail="Detection can only be done with user api keys")

    org = await Orgs.find_one({"_id": ObjectId(user.orgID)})
    if org and org["licenseType"] == LicenseType.PD:
        raise HTTPException(status_code=403, detail="Organization's license doesn't include this endpoint")
    
    text = data.text.strip()

    if not text:
        logger.warning("Empty text received for spam prediction.")
        raise HTTPException(status_code=400, detail="No text provided")
    
    clean_text, _ = extract_urls(text)

    if not clean_text:
        logger.warning("Only URLs received for spam prediction.")
        raise HTTPException(status_code=400, detail="Only URLs provided")

    try:
        transformed_text = await asyncio.to_thread(vectorizer.transform, [clean_text])
        spam_probability = await asyncio.to_thread(spam_model.predict_proba, transformed_text)
        spam_probability = round(spam_probability[0, 1] * 100, 2)

        result = {
            "text": clean_text,
            "spam": True if spam_probability >= threshold else False,
            "spamProbability": spam_probability,
        }

        user.reqCount += 1
        if result["spam"]:
            user.spamCount += 1

        user_dict = user.model_dump(by_alias=True, exclude={"id"})
        update_result = await Users.update_one(
            {"username": user.username, "orgID": ObjectId(user.orgID)}, 
            {"$set": user_dict}
        )
        if update_result.modified_count == 0:
            raise HTTPException(status_code=409, detail="Failed to update counts for user")

        logger.info(f"Spam Prediction: {result['spamProbability']}")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during spam prediction: {str(e)}")
        raise HTTPException(status_code=500, detail="Spam prediction failed due to server error")

# both spam and phishing detection
@router.post("/spam-phishing")
async def predict_spam_and_phishing(
    data: SpamInput,
    auth_data: Tuple[APIKeyType, Optional[OrgSchema], Optional[UserSchema]] = Depends(get_org_or_user)
):
    api_key_type, _, user = auth_data

    # RBAC
    if api_key_type != APIKeyType.USR:
        raise HTTPException(status_code=403, detail="Detection can only be done with user api keys")
    
    org = await Orgs.find_one({"_id": ObjectId(user.orgID)})
    if org and org["licenseType"] != LicenseType.SPD:
        raise HTTPException(status_code=403, detail="Organization's license doesn't include this endpoint")
    
    text = data.text.strip()

    if not text:
        logger.warning("Empty text received for spam prediction.")
        raise HTTPException(status_code=400, detail="No text provided")
    
    clean_text, urls = extract_urls(text)
    
    try:
        transformed_text = await asyncio.to_thread(vectorizer.transform, [clean_text])
        spam_probability = await asyncio.to_thread(spam_model.predict_proba, transformed_text)
        spam_probability = round(spam_probability[0, 1] * 100, 2)
        
        result = {
            "text": clean_text,
            "urls": [],
            "spam": True if spam_probability >= threshold else False,
            "spamProbability": spam_probability,
        }

        user.reqCount += 1
        if result["spam"]:
            user.spamCount += 1

        for url in urls:
            obj = await asyncio.to_thread(lambda: FeatureExtraction(url))
            x = np.array(obj.getFeaturesList()).reshape(1, 30)

            phishing_probability = await asyncio.to_thread(phishing_model.predict_proba, x)
            phishing_probability = round(phishing_probability[0,0] * 100, 2)
            
            phishing_result = {
                "url": url,
                "phishing": True if phishing_probability >= threshold else False,
                "phishingProbability": phishing_probability,
            }

            user.reqCount += 1
            if phishing_result["phishing"]:
                user.phishingCount += 1

            logger.info(f"Phishing Prediction: {phishing_result['phishingProbability']} | URL: {url}")
            result["urls"].append(phishing_result)

        user_dict = user.model_dump(by_alias=True, exclude={"id"})
        update_result = await Users.update_one(
            {"username": user.username, "orgID": ObjectId(user.orgID)}, 
            {"$set": user_dict}
        )
        if update_result.modified_count == 0:
            raise HTTPException(status_code=409, detail="Failed to update counts for user")

        logger.info(f"Spam Prediction: {result['spamProbability']}")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during spam prediction: {str(e)}")
        raise HTTPException(status_code=500, detail="Spam and phishing prediction failed due to server error")

