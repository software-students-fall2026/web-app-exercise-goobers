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

#configure this session
app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

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

db.users.create_index("user_id", unique=True)

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

#login and register (user, profile section)
def normalize_phone(value):
    return re.sub(r"[\s().+-]", "", value.strip())


def read_account_form():
    user_id = request.form.get("username", "").strip()
    phone = normalize_phone(request.form.get("phone", ""))

    if not re.fullmatch(r"[A-Za-z0-9_]{1,50}", user_id):
        return None, None, (
            "Username must contain 1–50 letters, numbers, or underscores."
        )

    if not re.fullmatch(r"[0-9]{10}", phone):
        return None, None, "Enter a 10-digit phone number."

    return user_id, phone, None


def current_user():
    mongo_id = session.get("user_id")

    if not isinstance(mongo_id, str):
        return None

    try:
        return db.users.find_one({"_id": ObjectId(mongo_id)})
    except InvalidId:
        return None


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("create-account.html")

    user_id, phone, error = read_account_form()

    if error:
        return render_template("create-account.html", error=error), 400

    try:
        result = db.users.insert_one({
            "user_id": user_id,
            "phone": phone,
            "role": "student"
        })
    except DuplicateKeyError:
        return render_template(
            "create-account.html",
            error="That username is already taken."
        ), 409

    session.clear()
    session["user_id"] = str(result.inserted_id)

    return redirect(url_for("profile"))


@app.route("/login", methods=["GET", "POST"])
def login_page():
    if request.method == "GET":
        return render_template("login.html")

    user_id, phone, error = read_account_form()

    if error:
        return render_template("login.html", error=error), 400

    user = db.users.find_one({"user_id": user_id})

    # Normalizing here also supports existing hyphenated seed numbers.
    if (
        user is None
        or normalize_phone(str(user.get("phone", ""))) != phone
    ):
        return render_template(
            "login.html",
            error="No account matches that username and phone number."
        ), 400

    session.clear()
    session["user_id"] = str(user["_id"])

    return redirect(url_for("profile"))


@app.route("/profile", methods=["GET", "POST"])
def profile():
    user = current_user()

    if user is None:
        session.clear()
        return redirect(url_for("login_page"))

    if request.method == "POST":
        user_id, phone, error = read_account_form()

        if error:
            return render_template(
                "profile.html", user=user, error=error
            ), 400

        try:
            db.users.update_one(
                {"_id": user["_id"]},
                {"$set": {
                    "user_id": user_id,
                    "phone": phone
                }}
            )
        except DuplicateKeyError:
            return render_template(
                "profile.html",
                user=user,
                error="That username is already taken."
            ), 409

        return redirect(url_for("profile"))

    return render_template("profile.html", user=user)


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("login_page"))


# CRUD/Flask requirement:
#Create - user can create their account with name and phone number
#Read - The users can read from the list of washing machines or dryers at a building
#Update - admins can update the status of machines, if they need repairs or what not
#Delete - admins can delete washing machines or dryers if they are no longer there


if __name__ == '__main__':
    app.run(debug=True)