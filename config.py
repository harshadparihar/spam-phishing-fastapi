from contextlib import asynccontextmanager
import logging
import os
import motor.motor_asyncio
from dotenv import load_dotenv


load_dotenv()

# configuring proper logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# db config
client = motor.motor_asyncio.AsyncIOMotorClient(os.getenv("MONGO_URI"))
db = client[os.getenv("DB_NAME")]

# collections
Orgs = db["orgs"]
Users = db["users"]

@asynccontextmanager
async def lifespan(app):
	# indexes
	await Orgs.create_index("email", unique=True)

	yield

	client.close()
