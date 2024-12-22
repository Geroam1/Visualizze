from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
from database import Database
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
import time
import os
import pandas as pd
import uuid
import matplotlib.pyplot as plt

app = Flask(__name__)
app.secret_key = 'secret_key_here_once_i_understand_it'

# website data base
db = Database("visualizze.db")

# folder to hold file uploads
UPLOAD_FOLDER = 'uploads'
# make folder directory if it doesnt exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
# folder path
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route("/")
def layout():
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


@app.route("/visualize")
def visualize():
    return render_template("visualize.html")

# route to handle visualize file upload
# its better to do this to handle future additions
@app.route('/upload', methods=['POST'])
def upload():
    # grabs a file from the request.files flask object, uploaded with a form
    uploaded_file = request.files.get('file')

    # if file exists
    if uploaded_file:

        # check file type, server side, to somewhat prevent cyber attacks
        filename = uploaded_file.filename
        if filename.endswith(('.csv', '.xlsx')):

            # ensure filename is named properly
            filename = secure_filename(uploaded_file.filename)

            # if user logged in
            if 'user_id' in session:
                # create a secure filename and append user ID to prevent overwriting
                user_id = str(session['user_id'])
                # makes sure the file uploaded is a properly named file
                filename_with_user_id = f"{user_id}_{filename}"

            # if user is not logged in
            else:
                # create a unique id to prevent data overwriting
                unique_suffix = str(uuid.uuid4())
                filename_with_user_id = f"{unique_suffix}_{filename}"

            # save file to uploads folder
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename_with_user_id)
            uploaded_file.save(filepath)

            # check if the file is empty
            if os.path.getsize(filepath) == 0:
                return "Error: The file is empty."
            
            # read data set from the uploads folder
            if filename.endswith('.csv'):
                try:
                    data = pd.read_csv(filepath)
                except pd.errors.EmptyDataError:
                    return "Error: The CSV file is empty."
            else:
                try:
                    data = pd.read_excel(filepath)
                except ValueError:
                    return "Error: The Excel file could not be read."

            # render visualize.html with file data
            return render_template('visualize.html', data=data.to_html(), filename=filename)

        else:
    # error messages
            return "Invalid file format. Please upload a .csv or .xlsx file.", 400
    
    return "No file selected.", 400


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