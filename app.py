import json
import os
import certifi
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
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

#just bring to login screen by default
@app.route('/', methods=['GET'])
def home_screen():
    return render_template("index.html")

@app.route("/login")
def login_page():
    return render_template("login.html")

@app.route("/register")
def register():
    return render_template("create-account.html")

#laundry building home page (displays 3 building options)
@app.route('/building_home_page', methods=['GET'])
def machine_home_screen():
    return render_template("building_home_page.html")

#when you click into a building, this displays all the 
#dynamic route for the building name 
@app.route('/building/<building_name>')
def machine_in_building(building_name):
    return render_template("machines_in_building.html", building_name=building_name)

#routing for the admins now
@app.route('/admin/machine-form')
def admin_machine_form():

    # we have the get the list of machines from mongodb first actually
    machines = list(db.machines.find({}))
    return render_template("admin-machine-form.html", machines=machines) 

#we need to let admins post too into this form
@app.route('/admin/machine-form', methods=['POST'])
def admin_machine_form():
    building = request.form['building']
    machine_id = request.form['machine_id']
    problem = request.form['problem']

    doc = {
        "building": building,
        "machine_id": machine_id,
        "problem": problem,
        "status": "Open"
    }

    db.work_requests.insert_one(doc)

    # look into how we can do this
    # we would need to get the list of machines and make sure we are hitting one that exists
    # we have to get the data coming in from the html? 
    # get form data included in the body of the POST request
    #name = request.form['fname']
    #message = request.form['fmessage']
    # do something fabulous with this data here


# add yourself to a queue
# delete yourself from the queue

#need to let admins delete a machine from a building, will need to access mongodb for this

# need form submissions for logging in and registering as well 

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




# CRUD/Flask:
#Create - user can create their account with name and phone number
#Read - The users can read from the list of washing machines or dryers at a building
#Update - admins can update the status of machines, if they need repairs or what not
#Delete - admins can delete washing machines or dryers if they are no longer there


if __name__ == '__main__':
    app.run(debug=True)