import os
from flask import (
    Flask, flash, render_template, 
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env


app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)


@app.route("/")
@app.route("/get_user")
def get_user():
    users = mongo.db.users.find()
    return render_template("user.html", users = users)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        #check if username exists in database
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            flash("Username already exists")
            return redirect(url_for("register"))

        register = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password"))
        }
        mongo.db.users.insert_one(register)

        # put new user into 'session' cookie
        session["user"] = request.form.get("username").lower()
        flash("Registration Successful!")
        return redirect(url_for("profile", username=session["user"]))

    return render_template("register.html")


@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        # check if username exist in database
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            # ensure hashed password matches user input
            if check_password_hash(
                existing_user["password"], request.form.get("password")):
                    session["user"] = request.form.get("username").lower()
                    flash("Welcome, {}".format(
                        request.form.get("username")))
                    return redirect(url_for("profile", username=session["user"]))
            else:
                # invalid password match
                flash("Incorrect Username and/or Password")
                return redirect(url_for("login"))

        else:
            # username doesn't exist
            flash("Incorrect Username and/or Password")
            return redirect(url_for("login"))

    return render_template("login.html") 


@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    # grab the session user's username from db
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]
    events = mongo.db.events.find(
        {"created_by": username.lower()})

    if session["user"]:
        return render_template("profile.html", username=username, events=events)

    return render_template("profile.html", username=username, events=events) 


@app.route("/logout", methods=["GET","POST"])
def logout():
    # remove user from session cookie
    flash("You have been logged out")
    session.pop("user")
    return redirect(url_for("login"))

@app.route("/create_event", methods=["GET", "POST"])
def create_event():
    if request.method == "POST":
        event = {
            "event_title": request.form.get("event_title"),
            "event_description": request.form.get("event_description"),
            "event_location": request.form.get("event_location"),            
            "event_type": request.form.getlist("event_type")[0],            
            "event_date": request.form.get("event_date"),            
            "start_time": request.form.get("start_time"),
            "created_by": session["user"] 
        }
        mongo.db.events.insert_one(event)
        flash("Event Successfully Added")
        return redirect(url_for("profile", username=session["user"]))

    categories = mongo.db.categories.find().sort("category_name", 1)
    return render_template("create_event.html", categories=categories)


@app.route("/edit_event/<event_id>", methods=["GET", "POST"])
def edit_event(event_id):
    if request.method == "POST":
        update_event = {
            "event_title": request.form.get("event_title"),
            "event_description": request.form.get("event_description"),
            "event_location": request.form.get("event_location"),            
            "event_type": request.form.getlist("event_type")[0],            
            "event_date": request.form.get("event_date"),            
            "start_time": request.form.get("start_time"),
            "created_by": session["user"] 
        }
        mongo.db.events.update({"_id": ObjectId(event_id)}, update_event)
        flash("Event Successfully Updated")
        
    event = mongo.db.events.find_one({"_id": ObjectId(event_id)})
    categories = mongo.db.categories.find().sort("category_name", 1)
    return render_template("edit_event.html", event=event, categories=categories)

@app.route("/delete_event/<event_id>")
def delete_event(event_id):
    return redirect(url_for("profile"))


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)
