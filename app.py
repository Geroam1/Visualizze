from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
from database import Database
from werkzeug.security import check_password_hash, generate_password_hash
import time

app = Flask(__name__)
app.secret_key = 'secret_key_here_once_i_understand_it'

db = Database("visualizze.db")

@app.route("/")
def visualize():
        return render_template("layout.html")

# tool to reset data base as I develop
@app.route("/clear")
def delete_database():
    db.clear_database()
    return render_template("layout.html")

@app.route("/register", methods=["GET", "POST"])
# register page
def register():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        # hash password
        password_hash = generate_password_hash(password)
        
        # document data in database
        db.add_user(username, password_hash, email)

        # store user_id in session
        user = db.get_user(username)
        session['user_id'] = user['id']

        # redirect to logged in home
        return redirect("/home")

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
# register page
def login():
    if request.method == 'POST':
        # get username and password inputs
        username = request.form.get('username')
        password = request.form.get('password')

        # Example: Check if the user exists and password is correct
        user = db.authenticate_user(username, password)
        # check user existance
        if user:
            # store user_id in session if user authenticated
            session['user_id'] = user['id']
            return redirect('/home')

        # if user unauthenticated
        flash('Invalid username or password', 'error')

    return render_template('login.html')

@app.route("/logout")
def logout():
    # clear session
    session.clear()
    
    # redirect to unlogged in home page
    return redirect(url_for('login'))

@app.route("/home")
def home():
    return render_template("home.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/services")
def services():
    return render_template("service.html")


if __name__ == "__main__":
    app.run(debug=True)