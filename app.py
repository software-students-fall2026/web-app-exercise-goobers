import json
import os
import certifi
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
import pymongo

#Load .evn file. File contains the MongoDB URI and name of the database that is used to connect to MongoDB.
load_dotenv()

#Initialize Flask app
app = Flask(__name__)


#connect to MongoDB
client = pymongo.MongoClient(os.getenv("MONGO_URI"), tlsCAFile=certifi.where())
db = client[os.getenv("MONGO_DBNAME")]

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
@app.route("/login")
def login_page():
    return render_template("login.html")

#page 2 of 6 - Create Account Screen - (create)
@app.route("/register")
def register():
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
    return render_template("machines_in_building.html", building_name=building_name)

#still need 2 more pages - 1 for edit, 1 for delete.


#routing for the admins now
@app.route('/admin/machine-form')
def admin_machine_form():

    # we have the get the list of machines from mongodb first actually
    machines = list(db.machines.find({}))
    return render_template("admin-machine-form.html", machines=machines) 



#we need to let admins post too into this form
@app.route('/admin/machine-form', methods=['POST'])
def admin_machine_form_post():
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


# jade write these
# add yourself to a queue
# delete yourself from the queue



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