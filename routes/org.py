from fastapi import APIRouter, HTTPException
from pymongo.errors import DuplicateKeyError, ServerSelectionTimeoutError, PyMongoError
from pydantic import BaseModel, ValidationError
from models import OrgSchema
from config import Orgs, logger
from utils.auth import generate_api_key, hash_password
from utils.constants import APIKeyType


# Request schemas
class OrgRegisterRequest(BaseModel):
	email: str
	userLimit: int
	licenseType: str

router = APIRouter(prefix="/org", tags=["Organization"])

@router.post("/register", status_code=201)
async def org_register(data: OrgRegisterRequest):
	try:
		api_key = generate_api_key(APIKeyType.ORG)

		org = OrgSchema(
			email=data.email,
			apiKey=hash_password(api_key),
			userLimit=data.userLimit,
			licenseType=data.licenseType,
		)

		org = org.model_dump(by_alias=True, exclude={"id"})
		result = await Orgs.insert_one(org)
		
		return {
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