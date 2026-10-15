import pymongo
import os
from dotenv import load_dotenv
from flask import Flask, jsonify
import certifi

#Load .evn file
load_dotenv()

app = Flask(__name__)


#connect to MongoDB
client = pymongo.MongoClient(os.getenv("MONGO_URI"), tlsCAFile=certifi.where())
db = client[os.getenv("MONGO_DBNAME")]

INITIAL_MACHINES = [
    {
        "machine_id": "Washer-001",
        "building": "Carlyle_Court",
        "type": "Washer",
        "status": "Available",
        "current_user": None,
        "users_in_queue": []
    },
    {
        "machine_id": "Washer-002",
        "building": "Carlyle_Court",
        "type": "Washer",
        "status": "Available",
        "current_user": None,
        "users_in_queue": []
    },
    {
        "machine_id": "Dryer-001",
        "building": "Carlyle_Court",
        "type": "Dryer",
        "status": "Available",
        "current_user": None,
        "users_in_queue": []
        }
    
]

def seed_db():
    #auto seed machines if collection is empty
    if db.machines.count_documents({}) == 0:
        db.machines.insert_many(INITIAL_MACHINES)
        print("Database seeded with initial machines.")
    else:
        print("Database already contains machines. No seeding performed.")


#run seed fuction when the app starts

with app.app_context():
    seed_db()

@app.route('/api/machines', methods=['GET'])
def get_machines():
    machines = list(db.machines.find({}, {'_id': 0}))  # Exclude the '_id' field from the response
    return jsonify({ "machines": machines })

if __name__ == '__main__':
    app.run(debug=True)