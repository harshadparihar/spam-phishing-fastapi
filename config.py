from contextlib import asynccontextmanager
import logging
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pymongo.server_api import ServerApi


load_dotenv()

# configuring proper logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# db config
client = AsyncIOMotorClient(os.getenv("MONGO_URI"), server_api=ServerApi('1'))
db = client[os.getenv("DB_NAME")]

# collections
Orgs = db["orgs"]
Users = db["users"]

@asynccontextmanager
async def lifespan(app):
	# indexes
	await Orgs.create_index("email", unique=True)
	await Orgs.create_index("apiKey")
	await Users.create_index("username", unique=True)
	await Users.create_index("apiKey")
	await Users.create_index("orgID")
	logger.info("Indexes created")

	yield

	client.close()
