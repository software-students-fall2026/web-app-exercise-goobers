import json
import os
import certifi
from dotenv import load_dotenv
# from flask import Flask, jsonify, render_template
import pymongo

import re
from bson import ObjectId
from bson.errors import InvalidId
from pymongo.errors import DuplicateKeyError
from flask import (
    Flask, jsonify, render_template,
    request, redirect, url_for, session
)

#Load .evn file
load_dotenv()


app = Flask(__name__)


#connect to MongoDB
client = pymongo.MongoClient(os.getenv("MONGO_URI"), tlsCAFile=certifi.where())
db = client[os.getenv("MONGO_DBNAME")]


def seed_db():
    #seed users
    base_dir = os.path.dirname(__file__)
    if db.users.count_documents({}) == 0:
        users_file = os.path.join(base_dir, "users.json")
        if os.path.exists(users_file):
            with open(users_file, 'r') as f:
                db.users.insert_many(json.load(f))
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

#login screen
@app.route('/', methods=['GET'])
def home_screen():
    return render_template("index.html")

#laundry building home page
@app.route('/buidling_home_page', methods=['GET'])
def machine_home_screen():
    return render_template("building_home_page.html")

# jade write these
# add yourself to a queue
# delete yourself from the queue

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

@app.route("/login")
def login_page():
    return render_template("login.html")
@app.route("/register")
def register():
    return render_template("create-account.html")


# CRUD/Flask:
#Create - user can create their account with name and phone number
#Read - The users can read from the list of washing machines or dryers at a building
#Update - admins can update the status of machines, if they need repairs or what not
#Delete - admins can delete washing machines or dryers if they are no longer there


if __name__ == '__main__':
    app.run(debug=True)