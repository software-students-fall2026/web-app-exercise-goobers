import pymongo
import os

#Load .evn file
load_dotenv()

#connect to MongoDB
client = pymongo.MongoClient(os.getenv("MONGO_URI"))
db = client[os.getenv("MONGO_DBNAME")]


