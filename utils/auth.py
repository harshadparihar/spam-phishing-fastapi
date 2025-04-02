import secrets
import string
from dotenv import load_dotenv
from utils.constants import APIKeyType
import hashlib

load_dotenv()

characters = string.ascii_letters + string.digits

def hash_api_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode()).hexdigest()

def generate_api_key(type: APIKeyType):
	api_key = ""
      
	if type == APIKeyType.ORG:
		api_key += "org_"
	elif type == APIKeyType.USR:
		api_key += "usr_"

	api_key += ''.join(secrets.choice(characters) for _ in range(40))
	
	return api_key