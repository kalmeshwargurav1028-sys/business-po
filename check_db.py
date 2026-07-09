from pymongo import MongoClient
import os
from dotenv import load_dotenv
import certifi

load_dotenv()
mongo_uri = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
client = MongoClient(mongo_uri, tlsCAFile=certifi.where())
db = client['business_dashboard_db']
users = db['users'].find()
for u in users:
    print(u.get('email'), u.get('role'))
