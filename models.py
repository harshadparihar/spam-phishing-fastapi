from typing import Any, Optional
from bson import ObjectId
from pydantic import BaseModel, EmailStr, Field
from utils.constants import LicenseType


# ObjectId validation
class PyObjectId(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, field: Any | None = None):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return str(v)

class OrgSchema(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    email: EmailStr
    apiKey: Optional[str] = None
    userLimit: Optional[int] = None
    licenseType: LicenseType

    class Config:
        populate_by_name = True

class UserSchema(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    username: str
    apiKey: str
    reqCount: int
    spamCount: int
    phishingCount: int
    orgID: PyObjectId

    class Config:
        populate_by_name = True