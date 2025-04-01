from typing import Annotated, Optional, Tuple
from fastapi import HTTPException, Header
from config import Orgs, Users
from models import OrgSchema, UserSchema
from utils.auth import hash_api_key
from utils.constants import APIKeyType
from pymongo.errors import PyMongoError


async def get_org_or_user(
	authorization: Annotated[str | None, Header()] = None
) -> Tuple[APIKeyType, Optional[OrgSchema], Optional[UserSchema]]:
	if authorization is None:
		raise HTTPException(status_code=401, detail="Missing Authorization header")
	if not authorization.startswith("Bearer "):
		raise HTTPException(status_code=401, detail="Invalid Authorization header")
	
	parts = authorization.split("Bearer ", 1)
	if len(parts) < 2 or not parts[1].strip():
		raise HTTPException(status_code=401, detail="Missing API Key")
	
	api_key = parts[1]
	hashed_api_key = hash_api_key(api_key)
	
	api_key_type: APIKeyType | None = None
	org: OrgSchema | None = None
	user: UserSchema | None = None

	try: 
		if api_key.startswith("org_"):
			api_key_type = APIKeyType.ORG

			org_instance = await Orgs.find_one({"apiKey": hashed_api_key})
			if not org_instance:
				raise HTTPException(status_code=401, detail="Invalid API Key")
			org = OrgSchema(**org_instance)
		elif api_key.startswith("usr_"):
			api_key_type = APIKeyType.USR

			user_instance = await Users.find_one({"apiKey": hashed_api_key})
			if not user_instance:
				raise HTTPException(status_code=401, detail="Invalid API Key")
			user = UserSchema(**user_instance)
		else:
			raise HTTPException(status_code=401, detail="Invalid API Key")
	except PyMongoError as e:
		raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
	
	return api_key_type, org, user