import secrets
import string
from dotenv import load_dotenv
from utils.constants import APIKeyType
from passlib.context import CryptContext

load_dotenv()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
characters = string.ascii_letters + string.digits + string.punctuation

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def generate_api_key(type: APIKeyType):
	api_key = ""
      
	if type == APIKeyType.ORG:
		api_key += "org_"
	elif type == APIKeyType.USR:
		api_key += "usr_"

	api_key += ''.join(secrets.choice(characters) for _ in range(40))
	
	return api_key