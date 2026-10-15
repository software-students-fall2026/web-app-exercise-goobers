import json
import os
import certifi
from dotenv import load_dotenv
from flask import Flask, jsonify
import pymongo

#Load .evn file
load_dotenv()


app = Flask(__name__)


#connect to MongoDB
client = pymongo.MongoClient(os.getenv("MONGO_URI"), tlsCAFile=certifi.where())
db = client[os.getenv("MONGO_DBNAME")]


def seed_db():
    #seed users
    base_dir = os.path.dirname(__file__)
    if db.user.count_documents({}) == 0:
        users_file = os.path.join(base_dir, "users.json")
        if os.path.exists(users_file):
            with open(users_file, 'r') as f:
                db.user.insert_many(json.load(f))
                print("Users seeded successfully.")

    if db.machines.count_documents({}) == 0:
        machines_file = os.path.join(base_dir, "machines.json")
        if os.path.exists(machines_file):
            with open(machines_file, 'r') as f:
                db.machines.insert_many(json.load(f))
                print("Machines seeded successfully.")


#run seed fuction when the app starts

with app.app_context():
    seed_db()

@app.route('/api/machines', methods=['GET'])
def get_machines():
    machines = list(db.machines.find({}, {'_id': 0})) 
    return jsonify({ "machines": machines })

@app.route("/api/users", methods=["GET"])
def get_users():
    users = list(db.users.find({}, {"_id": 0}))
    return jsonify({"users": users})

@app.route("/api/admin/reset-db", methods=["POST"])
def reset_db_endpoint():
    base_dir = os.path.dirname(__file__)
    users_file = os.path.join(base_dir, "users.json")
    machines_file = os.path.join(base_dir, "machines.json")

    db.users.delete_many({})
    db.machines.delete_many({})

    user_count = 0
    machine_count = 0

    if os.path.exists(users_file):
        with open(users_file, 'r') as f:
            user = json.load(f)
            if user:
                db.users.insert_many(user)
                user_count = len(user)

    if os.path.exists(machines_file):
        with open(machines_file, 'r') as f:
            machines = json.load(f)
            if machines:
                db.machines.insert_many(machines)
                machine_count = len(machines)

    return jsonify({"message": f"Database reset successfully. {user_count} users and {machine_count} machines added."})

if __name__ == '__main__':
    app.run(debug=True)