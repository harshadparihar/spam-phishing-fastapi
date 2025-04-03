# defining input models
import asyncio
from typing import Optional, Tuple
from bson import ObjectId
import numpy as np
from pydantic import BaseModel
import tldextract
from fastapi import APIRouter, Depends, HTTPException
from config import Orgs, Users, logger
from dependencies import get_org_or_user
from models import OrgSchema, UserSchema
from utils.ai import detect_phishing, detect_spam
from utils.constants import APIKeyType, LicenseType, threshold


# defining input models
class Input(BaseModel):
    text: str

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
    data: Input,
    auth_data: Tuple[APIKeyType, Optional[OrgSchema], Optional[UserSchema]] = Depends(get_org_or_user)
):
    api_key_type, _, user = auth_data

    # RBAC
    if api_key_type != APIKeyType.USR:
        raise HTTPException(status_code=403, detail="Detection can only be done with user api keys")
    
    org = await Orgs.find_one({"_id": ObjectId(user.orgID)})
    if org and org["licenseType"] == LicenseType.SD:
        raise HTTPException(status_code=403, detail="Organization's license doesn't include this endpoint")
    
    text = data.text.strip()

    if not text:
        logger.warning("Empty URL received for phishing prediction.")
        raise HTTPException(status_code=400, detail="No URL provided")

    _, urls = extract_urls(text)

    if len(urls) == 0:
        return {
            "message": "No URLs found in text"
        }
    try:
        result = { "urls": [] }

        phishing_tasks = []

        for url in urls:
            phishing_tasks.append(detect_phishing(url))

        phishing_results = await asyncio.gather(*phishing_tasks, return_exceptions=True)

        for url, phishing_result in zip(urls, phishing_results):
            if isinstance(phishing_result, Exception):
                logger.error(f"Error processing {url}: {phishing_result}")
                result["urls"].append({"url": url, "error": str(phishing_result)})
            else:
                user.phishingReqCount += 1
                if phishing_result["phishing"]:
                    user.isPhishingCount += 1

                result["urls"].append(phishing_result)

        user_dict = user.model_dump(by_alias=True, exclude={"id"})
        update_result = await Users.update_one(
            {"username": user.username, "orgID": ObjectId(user.orgID)}, 
            {"$set": user_dict}
        )
        if update_result.modified_count == 0:
            raise HTTPException(status_code=409, detail="Failed to update counts for user")
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during phishing prediction: {str(e)}")
        raise HTTPException(status_code=500, detail="Phishing prediction failed due to server error")


# spam detection
@router.post("/spam")
async def predict_spam(
    data: Input,
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
        result = await detect_spam(clean_text)

        user.spamReqCount += 1
        if result["spam"]:
            user.isSpamCount += 1

        user_dict = user.model_dump(by_alias=True, exclude={"id"})
        update_result = await Users.update_one(
            {"username": user.username, "orgID": ObjectId(user.orgID)}, 
            {"$set": user_dict}
        )
        if update_result.modified_count == 0:
            raise HTTPException(status_code=409, detail="Failed to update counts for user")

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during spam prediction: {str(e)}")
        raise HTTPException(status_code=500, detail="Spam prediction failed due to server error")

# both spam and phishing detection
@router.post("/spam-phishing")
async def predict_spam_and_phishing(
    data: Input,
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
        result = await detect_spam(clean_text)
        result["urls"] = []

        if len(urls) != 0:
            phishing_tasks = []

            for url in urls:
                phishing_tasks.append(detect_phishing(url))

            phishing_results = await asyncio.gather(*phishing_tasks, return_exceptions=True)

            for url, phishing_result in zip(urls, phishing_results):
                if isinstance(phishing_result, Exception):
                    logger.error(f"Error processing {url}: {phishing_result}")
                    result["urls"].append({"url": url, "error": str(phishing_result)})
                else:
                    user.phishingReqCount += 1
                    if phishing_result["phishing"]:
                        user.isPhishingCount += 1

                    result["urls"].append(phishing_result)

        user.spamReqCount += 1
        if result["spam"]:
            user.isSpamCount += 1

        user_dict = user.model_dump(by_alias=True, exclude={"id"})
        update_result = await Users.update_one(
            {"username": user.username, "orgID": ObjectId(user.orgID)}, 
            {"$set": user_dict}
        )
        if update_result.modified_count == 0:
            raise HTTPException(status_code=409, detail="Failed to update counts for user")
        
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during spam prediction: {str(e)}")
        raise HTTPException(status_code=500, detail="Spam and phishing prediction failed due to server error")

