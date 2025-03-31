from typing import Optional, Tuple
from fastapi import APIRouter, Depends, HTTPException
from pymongo.errors import DuplicateKeyError, ServerSelectionTimeoutError, PyMongoError
from pydantic import BaseModel, ValidationError
from dependencies import get_org_or_user
from models import OrgSchema, UserSchema
from config import Orgs, logger
from utils.auth import generate_api_key, hash_api_key
from utils.constants import APIKeyType


router = APIRouter(prefix="/org", tags=["Organization"])

class OrgRegisterRequest(BaseModel):
	email: str
	userLimit: int
	licenseType: str

@router.post("/register", status_code=201)
async def org_register(data: OrgRegisterRequest):
	try:
		api_key = generate_api_key(APIKeyType.ORG)

		org = OrgSchema(
			email=data.email,
			apiKey=hash_api_key(api_key),
			userLimit=data.userLimit,
			licenseType=data.licenseType,
		)

		org = org.model_dump(by_alias=True, exclude={"id"})
		result = await Orgs.insert_one(org)
		
		return {
			"message": "Organization registered",
			"id": str(result.inserted_id),
			"apiKey": api_key,
		}
	except ValidationError as e:
		raise HTTPException(status_code=400, detail=e.errors()[0]["msg"])
	except DuplicateKeyError:
		raise HTTPException(status_code=409, detail="Email already exists")
	except ServerSelectionTimeoutError:
		raise HTTPException(status_code=500, detail="Database connection failed")
	except PyMongoError as e:
		logger.error(f"Error during organization registration: {str(e)}")
		raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
	except Exception as e:
		logger.error(f"Unexpected error: {str(e)}")
		raise HTTPException(status_code=500, detail="Internal server error")

class RefreshUserKeyRequest(BaseModel):
	username: str

@router.post("/users", status_code=201)
async def refresh_user_key(
	data: RefreshUserKeyRequest, 
	auth_data: Tuple[APIKeyType, Optional[OrgSchema], Optional[UserSchema]] = Depends(get_org_or_user)
):
	try:
		api_key_type, org, user = auth_data

		return {
			"api_key_type": api_key_type, 
			"org": org, 
			"user": user,
		}
	except ValidationError as e:
		raise HTTPException(status_code=400, detail=e.errors()[0]["msg"])
	except ServerSelectionTimeoutError:
		raise HTTPException(status_code=500, detail="Database connection failed")
	except PyMongoError as e:
		logger.error(f"Error during organization registration: {str(e)}")
		raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
	except Exception as e:
		logger.error(f"Unexpected error: {str(e)}")
		raise HTTPException(status_code=500, detail="Internal server error")