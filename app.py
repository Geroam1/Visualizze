from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
from database import Database
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
import os
import base64
from io import BytesIO
import pandas as pd
import uuid
import matplotlib
# prevents GUI output from matlab, since it causes errors and isnt needed
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from functions import generate_and_recommend_visuals


# app setup
app = Flask(__name__)

# secret key for security
app.config['SECRET_KEY'] = 'd9e850b0a5aea4034945ffe3e897c88583ec644577a717be7df58706176529b5518aa6'

# visualizze data base
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
            session.permanent = True # set session to permanent
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
@app.route('/visualize', methods=['POST'])
def upload():
    # Get the uploaded file
    uploaded_file = request.files.get('file')

    # Check if a file was uploaded
    if not uploaded_file:
        return "No file selected.", 400

    # get filename and ensure it is a csv or xlsx
    # additionally add it to the session for use later
    filename = uploaded_file.filename
    if not filename.endswith(('.csv', '.xlsx')):
        return "Invalid file format. Please upload a .csv or .xlsx file.", 400
    

    # renames file to a secure and proper file name for windows
    filename = secure_filename(filename)
    session['file_name'] = filename

    # get user_id for file naming, if logged in acutal user_id, if not randomly generated string code for id
    # prevents data with same name overwritting
    user_id = session.get('user_id') or str(uuid.uuid4())
    filename_with_user_id = f"{user_id}_{filename}"

    # save file to upload folder
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename_with_user_id)
    uploaded_file.save(filepath)

    # defence against empty files
    if os.path.getsize(filepath) == 0:
        return "Error: The file is empty.", 400

    # store file path in session for later use
    session['uploaded_file_path'] = filepath

    # redirect to dashboard
    return redirect(url_for('dashboard'))

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():

    # ensure file was uploaded
    file_path = session.get('uploaded_file_path')
    if not file_path:
        return "No file uploaded", 400

    # get file extension
    file_extension = os.path.splitext(file_path)[1]

    # read file depending on type
    if file_extension == '.xlsx':
        data = pd.read_excel(file_path)
    elif file_extension == '.csv':
        data = pd.read_csv(file_path)
    else:
        return "Unsupported file format", 400

    # get columns
    col_names = list(data.columns)

    # handle POST request (form submission)
    x_col = y_col = z_col = None
    if request.method == 'POST':
        # check selected columns
        if request.form.get('columnx'):
            x_col = request.form.get('columnx')
        if request.form.get('columny'):
            y_col = request.form.get('columny')
        if request.form.get('columnz'):
            z_col = request.form.get('columnz')

        # You can now use x_col, y_col, and z_col as needed for your processing
        print(f"Selected columns: X = {x_col} {type(x_col)}, Y = {y_col}, Z = {z_col}")
    
        # generate visuals and recommend one
        visuals, recommended_visual_name = generate_and_recommend_visuals(
            data, 
            x_col=x_col, 
            y_col=y_col
        )
        if recommended_visual_name:
            recommended_visual = visuals[recommended_visual_name]

            # converts the visual to base64, complicated but this simply allows the visual
            # to be sent to the template as png image
            img_stream = BytesIO()
            recommended_visual.savefig(img_stream, format='png')
            img_stream.seek(0)
            img_base64 = base64.b64encode(img_stream.read()).decode('utf-8')

    # report data
    file_name = session['file_name']
    col_num = len(data.columns)
    row_num = len(data.index)
    data_types = list(data.dtypes)

    # convert data to html table for html table display
    table_html = data.to_html(classes="html-table")

    return render_template(
        'dashboard.html',
        table_html=table_html,
        file_name=file_name,
        col_num=col_num,
        row_num=row_num,
        col_names=col_names,
        data_types=data_types,
        visual=img_base64 if (request.method == 'POST' and recommended_visual_name) else None
    )


@app.route("/home")
def home():
    return render_template("home.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/services")
def services():
    return render_template("service.html")


if __name__ == '__main__':
    app.run(debug=True)