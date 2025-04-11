from typing import Optional, Tuple
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException
from pymongo.errors import DuplicateKeyError, ServerSelectionTimeoutError, PyMongoError
from pydantic import BaseModel
from dependencies import get_org_or_user
from models import OrgSchema, UserSchema
from config import Orgs, Users, logger
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
	except HTTPException:
		raise
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
		api_key_type, org, _ = auth_data

		# RBAC
		if api_key_type != APIKeyType.ORG:
			raise HTTPException(status_code=403, detail="Insufficient permissions")
		
		api_key = generate_api_key(APIKeyType.USR)
		hashed_api_key = hash_api_key(api_key)

		user = await Users.find_one({"username": data.username, "orgID": ObjectId(org.id)})
		
		if not user: # create a new user and return its api key
			# checking first how many users this org has registered
			user_count = await Users.count_documents({"orgID": ObjectId(org.id)})
			if user_count == org.userLimit:
				raise HTTPException(status_code=409, detail="User limit reached for the organization")
			
			# now create the user
			user_dict = UserSchema(
				username=data.username,
				apiKey=hashed_api_key,
				orgID=ObjectId(org.id),
			)
			user_dict = user_dict.model_dump(by_alias=True, exclude={"id"})
			await Users.insert_one(user_dict)

			return { "apiKey": api_key }		
		
		update_result = await Users.update_one(
			{"username": data.username, "orgID": ObjectId(org.id)}, 
			{"$set": {"apiKey": hashed_api_key}},
		)
		
		if update_result.modified_count == 0:
			raise HTTPException(status_code=409, detail="Failed to update apiKey for user")

		return { "apiKey": api_key }
	except HTTPException:
		raise
	except ServerSelectionTimeoutError:
		raise HTTPException(status_code=500, detail="Database connection failed")
	except PyMongoError as e:
		logger.error(f"Error during organization registration: {str(e)}")
		raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
	except Exception as e:
		logger.error(f"Unexpected error: {str(e)}")
		raise HTTPException(status_code=500, detail="Internal server error")
	
@router.get("/users")
async def get_users_summary(
	auth_data: Tuple[APIKeyType, Optional[OrgSchema], Optional[UserSchema]] = Depends(get_org_or_user)
):
	try:
		api_key_type, org, _ = auth_data

		# RBAC
		if api_key_type != APIKeyType.ORG:
			raise HTTPException(status_code=403, detail="Insufficient permissions")
		
		users = []

		async for user in Users.find(
			{ "orgID": ObjectId(org.id) }, { "_id": 0, "apiKey": 0, "orgID": 0 }
		):
			if (user["spamReqCount"]) == 0:
				user["spamPercent"] = 0
			else:
				user["spamPercent"] = user["isSpamCount"] / user["spamReqCount"]
    
			user["spamPercent"] = round(user["spamPercent"] * 100, 2)

			if (user["phishingReqCount"]) == 0:
				user["phishingPercent"] = 0
			else:
				user["phishingPercent"] = user["isPhishingCount"] / user["phishingReqCount"]
    
			user["phishingPercent"] = round(user["phishingPercent"] * 100, 2)

			users.append(user)

		return { "users": users }
		
	except HTTPException:
		raise
	except ServerSelectionTimeoutError:
		raise HTTPException(status_code=500, detail="Database connection failed")
	except PyMongoError as e:
		logger.error(f"Error during organization registration: {str(e)}")
		raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
	except Exception as e:
		logger.error(f"Unexpected error: {str(e)}")
		raise HTTPException(status_code=500, detail="Internal server error")