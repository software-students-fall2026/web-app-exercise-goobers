import json
import os
import certifi
from dotenv import load_dotenv
from flask import (
    Flask, abort, flash, jsonify, redirect,
    render_template, request, url_for
)
from flask_login import (
    LoginManager, UserMixin, current_user,
    login_required, login_user, logout_user
)
import pymongo
from bson import ObjectId
from datetime import datetime, timezone

#Load .env file. File contains the MongoDB URI and name of the database that is used to connect to MongoDB.
load_dotenv()

#Initialize Flask app
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]

login_manager = LoginManager(app)
login_manager.login_view = "login_page"

#connect to MongoDB
client = pymongo.MongoClient(os.getenv("MONGO_URI"), tlsCAFile=certifi.where())
db = client[os.getenv("MONGO_DBNAME")]

#add user class and loader
class User(UserMixin):
    def __init__(self, document):
        self.id = document["user_id"]
        self.role = document.get("role", "student")


@login_manager.user_loader
def load_user(user_id):
    document = db.user.find_one({"user_id": user_id})

    if document is None:
        return None

    return User(document)

#seed creates a defualt set of users and machines into the database if they don't already exist. 
#takes from machines.json and users.json files. 
def seed_db():
    base_dir = os.path.dirname(__file__)
    #seed in users
    if db.user.count_documents({}) == 0:
        users_file = os.path.join(base_dir, "users.json")
        if os.path.exists(users_file):
            with open(users_file, 'r') as f:
                db.user.insert_many(json.load(f))
    #seed in machines
    if db.machines.count_documents({}) == 0:
        machines_file = os.path.join(base_dir, "machines.json")
        if os.path.exists(machines_file):
            with open(machines_file, 'r') as f:
                db.machines.insert_many(json.load(f))


#run seed fuction when the app starts
#temp comment out to test front end
with app.app_context():
    seed_db()

#page 1 of 6 - Login Screen - (none) ***change to login screen by default***
#just bring to login screen by default
@app.route('/', methods=['GET'])
def home_screen():
    return render_template("index.html")

#***replace '/' with this***
@app.route("/login", methods=["GET", "POST"])
def login_page():
    if request.method == "POST":
        phone = request.form.get("phone", "").strip()
        user = db.user.find_one({"phone": phone}) if phone else None

        if user is None:
            return render_template(
                "login.html",
                error="No account found with that phone number."
            ), 400

        login_user(User(user))

        if current_user.role == "admin":
            return redirect(url_for("admin_machine_form"))

        return redirect(url_for("machine_home_screen"))

    return render_template("login.html")

#page 2 of 6 - Create Account Screen - (create)
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        phone = request.form.get("phone", "").strip()

        if not username or not phone:
            return render_template(
                "create-account.html",
                error="Please enter a username and phone number."
            ), 400

        existing_user = db.user.find_one({
            "$or": [
                {"user_id": username},
                {"phone": phone}
            ]
        })

        if existing_user:
            return render_template(
                "create-account.html",
                error="That username or phone number is already registered."
            ), 400

        user = {
            "user_id": username,
            "name": username,
            "phone": phone,
            "role": "student"
        }

        db.user.insert_one(user)
        login_user(User(user))

        return redirect(url_for("machine_home_screen"))

    return render_template("create-account.html")

#page 3 of 6 - Buildings - (read/search)
#laundry building home page (displays 3 building options)
@app.route('/building_home_page', methods=['GET'])
def machine_home_screen():
    return render_template("building_home_page.html")

#page 4 of 6 - machine list for building - (read)
#when you click into a building, this displays all the 
#dynamic route for the building name 
@app.route('/building/<building_name>')
def machine_in_building(building_name):
    machines = list(db.machines.find({"building": building_name}))
    return render_template("machines_in_building.html", building_name=building_name, machines=machines)

#still need 2 more pages - 1 for edit, 1 for delete.


#routing for the admins now
@app.route('/admin/machine-form')
@login_required
def admin_machine_form():
    if current_user.role != "admin":
        abort(403)

    # we have the get the list of machines from mongodb first actually
    machines = list(db.machines.find({}))
    return render_template("work-request.html", machines=machines) 



#we need to let admins post too into this form
@app.route('/admin/machine-form', methods=['POST'])
@login_required
def admin_machine_form_post():
    if current_user.role != "admin":
        abort(403)

    machine_id = request.form.get("machine_id", "").strip()
    problem = request.form.get("problem", "").strip()

    machine = db.machines.find_one({"machine_id": machine_id})

    if machine is None or not problem:
        machines = list(db.machines.find({}))
        return render_template(
            "work-request.html",
            machines=machines,
            error="Choose a valid machine and describe the issue."
        ), 400

    db.work_requests.insert_one({
        "building": machine["building"],
        "machine_id": machine["machine_id"],
        "problem": problem,
        "status": "Open"
    })

    flash("Work request submitted.")
    return redirect(url_for("admin_machine_form"))

    # look into how we can do this
    # we would need to get the list of machines and make sure we are hitting one that exists
    # we have to get the data coming in from the html? 
    # get form data included in the body of the POST request
    #name = request.form['fname']
    #message = request.form['fmessage']
    
    # do something fabulous with this data here


# add yourself to a queue
@app.route('/machines/<machine_id>/queue', methods=['POST'])
def add_to_queue(machine_id):
    #so get the user, get the machine that they click, go to the queue that we have, append, then update mongodb mahcine doc

    data = request.get_json()
    user_id = data['user_id']

    machine = db.machines.find_one({"machine_id": machine_id})

    queue = machine.get("users_in_queue", [])

    queue.append(user_id)

    #have to update it. 
    db.machines.update_one(
        {"machine_id": machine_id},
        {"$set": {"users_in_queue": queue}}
    )

    return jsonify({"message": "user joined queue"})



# delete yourself from the queue
@app.route('/machines/<machine_id>/queue', methods=['DELETE'])
def delete_from_queue(machine_id):
    #so get the user, get the machine that they click, go to the queue that we have, remove, then update mongodb machine doc

    data = request.get_json()
    user_id = data['user_id']

    machine = db.machines.find_one({"machine_id": machine_id})

    queue = machine.get("users_in_queue", [])

    queue.remove(user_id)

    #have to update it.
    db.machines.update_one(
        {"machine_id": machine_id},
        {"$set": {"users_in_queue": queue}}
    )

    return jsonify({"message": "user left queue"})



#need to let admins delete a machine from a building, will need to access mongodb for this

@app.route('/api/machines', methods=['GET'])
def get_machines():
    machines = list(db.machines.find({}, {'_id': 0})) 
    return jsonify({ "machines": machines })

@app.route("/api/users", methods=["GET"])
def get_users():
    users = list(db.users.find({}, {"_id": 0}))
    return jsonify({"users": users})



if __name__ == '__main__':
    app.run(debug=True)