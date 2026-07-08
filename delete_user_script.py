import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv('business_dashboard/.env')
# If no .env, it might use hardcoded uri in app.py. 
# Let's check app.py for the URI first.
