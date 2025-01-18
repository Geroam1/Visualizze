from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
from database import Database
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import os
import io
import base64
from io import BytesIO
import pandas as pd
import uuid
import matplotlib
# prevents GUI output from matlab, since it causes errors and isnt needed
matplotlib.use('Agg')
import matplotlib.pyplot as plt
# personal functions
from functions import (
    generate_and_recommend_visuals, 
    process_data, 
    get_data_report_data,
    )
from apscheduler.schedulers.background import BackgroundScheduler
from functions import generate_and_recommend_WIP

"""
start up processes
"""

# app setup
app = Flask(__name__)

# get the VISUALIZZE_SECRET_KEY for .env file for secure sessions
load_dotenv('./files_to_ignore/.env') # load variables from .env file
app.config['SECRET_KEY'] = os.getenv('VISUALIZZE_SECRET_KEY')

# initialize visualizze data base object
db = Database("./DataBase/visualizze.db")

# start background process to clear data_set database periodically
def clean_data_base():
    db.clear_data_sets()
hour, minute = 0, 0 # 24 hour clock, time when the temp database table will be cleaned. 0,0 -> midnight
scheduler = BackgroundScheduler()
scheduler.add_job(func=clean_data_base, trigger='cron', hour=hour, minute=minute)
scheduler.start()

"""
routes
"""

@app.route("/")
def layout():
        return redirect(url_for("home"))


# tool to reset data base as I develop
@app.route("/clear")
def delete_database():
    db.clear_database()
    session.clear()
    return render_template("layout.html")


@app.route("/register", methods=["GET", "POST"])
# register page
def register():
    error_message = None
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm-password")       

        # check if password and confirm password are equal
        if not (password == confirm_password):
            error_message = "Passwords do not match"
            return render_template("register.html", error_message=error_message)
        
        # check if username already exists
        if db.user_exists(username):
            error_message = "Username already exists"
            return render_template("register.html", error_message=error_message)

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
    # login error message to pass to login.html
    error_message = None
    if request.method == 'POST':
        # get username and password inputs
        username = request.form.get('username')
        password = request.form.get('password')

        # Example: Check if the user exists and password is correct
        user = db.authenticate_user(username, password)

        # check user existance, and correct password
        if user and check_password_hash(user['password_hash'], password):
            # clear any existing session and store user_id in session if user authenticated
            session.clear()
            session.permanent = True # set session to permanent (keeps a user logged in until logout)
            session['user_id'] = user['id']
            return redirect('/home')
        else:
            # if username or password incorrect do not login
            error_message = "Invalid username or password."

    return render_template('login.html', error_message=error_message)


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

    # if user is not logged in give an annoymous id
    if not session.get('user_id'):
        session['user_id_private'] = str(uuid.uuid4())

    # get the uploaded file from requests
    uploaded_file = request.files.get('file')

    # check that a file was uploaded
    if not uploaded_file:
        error_message = "File missing or removed from server. Please reupload the file."
        return render_template('visualize.html', error_message=error_message)

    # get filename and ensure it is a csv or xlsx
    # additionally add it to the session for use later
    filename = uploaded_file.filename
    if not filename.endswith(('.csv', '.xlsx')):
        return "Invalid file format. Please upload a .csv or .xlsx file.", 400
    
    # renames file to a secure and proper file name for the OS
    filename = secure_filename(filename)
    session['file_name'] = filename

    # get user_id, or generate an annoymous one, and add it to the session to access data later
    user_id = session.get('user_id') or session.get('user_id_private')

    # get file size in bytes
    file_size = len(uploaded_file.read())
    uploaded_file.seek(0) # reset file pointer, so that later file reading does not output something empty

    # check file size
    max_file_size = 2**20 / 2 # file_size is in Bytes, so 2**20 would represent 500 kb

    # add this to the session as the users max server storage size for later
    # maybe a feature can be added to increase this in some.. Financial way 
    session['user_max_server_storage'] = max_file_size
    if file_size > max_file_size:
        error_message = "File size to large, max file size: 500 kb"
        return render_template('visualize.html', error_message=error_message)

    # try to add data set to db
    try:
        # reads file as binary
        data_set = uploaded_file.read()

        # upload file data to temp db table and record dataset id in session
        session['dataset_id'] = db.add_data_set(user_id, filename, 'csv' if filename.endswith('.csv') else 'xlsx', file_size, data_set)

        # show save request form when rendering
        session['show-save-request-form'] = True        

    except Exception as e:
        return f"Error while saving to database: {str(e)}", 500

    # redirect to dashboard
    return redirect(url_for('dashboard'))


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():

    # ensure file was uploaded
    user_id = session.get('user_id') or session.get('user_id_private')
    if not user_id:
        error_message = "No user ID found"
        return render_template('error.html', error_message = error_message)

    # if user is logged in
    if session.get('user_id'):
        saved_data_set_count = db.get_user_id_saved_datasets_counnt(user_id)

        # check if user exceeded saved dataset count limit
        max_dataset_save_count = 10
        if saved_data_set_count >= max_dataset_save_count:
            allow_saving = False
        else:
            allow_saving = True

    # get dataset from the database based on user_id
    try:
        # get db entries from temp dataset table as a dictionary
        data_set_entry = db.get_data_set_by_id(session['dataset_id'])

        if not data_set_entry:
            error_message = "No file uploaded"
            return render_template('error.html', error_message = error_message)

        # seperate db data
        file_name = data_set_entry['file_name']
        file_type = data_set_entry['file_type']
        file_data = data_set_entry['data_set']
        file_size = data_set_entry['file_size']


        # read the binary data using pandas
        if file_type == 'xlsx':
            data = pd.read_excel(BytesIO(file_data))
        elif file_type == 'csv':
            data = pd.read_csv(BytesIO(file_data))
        else:
            return "Unsupported file format", 400
        
        # process the data to ready for visualization
        data = process_data(data)

    except Exception as e:
        return f"Error while retrieving file from the database: {str(e)}", 500
    
    # report data
    file_name = file_name
    data_report = get_data_report_data(data)

    # convert data(s) to html table for html table display
    table_html = data.to_html(classes="html-table")
    col_data_html = data_report['col data'].to_html(classes="html-table", index=False)

    # handle POST request (form submission)
    x_col = y_col = z_col = None
    

    if request.method == 'POST':
        # Check for 'save_dataset' value
        save_dataset = request.form.get('save_dataset')

        if save_dataset == 'yes':
            # stop showing form
            session['show-save-request-form'] = False
            # save dataset to user_data_sets tab;e
            print('Saving dataset to saved datasets...')
            db.save_user_data_set(user_id=session['user_id'], 
                                  data_set=file_data, 
                                  file_name=file_name,
                                  file_type=file_type, 
                                  file_size=file_size, 
                                  user_max_server_storage_bytes=session['user_max_server_storage'])
            print('Saved to saved datasets...')
        elif save_dataset == 'no':
            # stop showing form
            session['show-save-request-form'] = False
            print('Not saving dataset to saved datasets...')

        # check selected columns
        if request.form.get('columnx'):
            x_col = request.form.get('columnx')
        if request.form.get('columny'):
            y_col = request.form.get('columny')
            print(y_col)
    
        # check columns were selected
        if x_col not in data.columns and y_col not in data.columns:
            if 'visualize' in request.form:
                error_message = "Please select at least 1 column."
                return render_template(
                    'dashboard.html', 
                    error_message=error_message, 
                    data_report=data_report, 
                    table_html=table_html, 
                    col_data_html=col_data_html)
        
        # generate visuals
        visuals, recommended_visual_name = generate_and_recommend_WIP(
            data, 
            x_col=x_col, 
            y_col=y_col,
        )
        if recommended_visual_name:
            recommended_visual = visuals[recommended_visual_name]

            # converts the visual to base64, complicated but this simply allows the visual
            # to be sent to the template as png image
            img_stream = BytesIO()
            recommended_visual.savefig(img_stream, format='png')
            img_stream.seek(0)
            img_base64 = base64.b64encode(img_stream.read()).decode('utf-8')
        if visuals:
            # encode visuals into base64
            encoded_visuals = []
            for visual_name, fig in visuals.items():
                buf = io.BytesIO()
                fig.savefig(buf, format='png')
                buf.seek(0)
                encoded_visual = base64.b64encode(buf.getvalue()).decode('utf-8')
                buf.close()
                encoded_visuals.append(f"data:image/png;base64,{encoded_visual}")

    return render_template(
        # template to render
        'dashboard.html',

        # html table data to send
        table_html=table_html,
        col_data_html = col_data_html,

        # general data to send
        file_name=file_name,
        data_report = data_report,
        allow_saving = allow_saving if session.get('user_id') else False,

        # visual data to send
        visual=img_base64 if (request.method == 'POST' and recommended_visual_name) else None,
        encoded_visuals=encoded_visuals if (request.method == 'POST' and visuals) else None
    )


@app.route("/continue_without_account", methods=["POST"])
def continue_without_account():
    user_id_private = str(uuid.uuid4())
    session['user_id_private'] = user_id_private
    print('private session started')
    return redirect(url_for("home"))
@app.route("/home")
def home():
    # if user logged in, or is in an annoymous session
    if session.get('user_id') or session.get('user_id_private'):
        if session.get('user_id'):
            username = str(db.get_username(session.get('user_id')))
            print(username)
        else:
            username = ""
        return render_template('home.html', username=username)
    return redirect(url_for("homeXlog"))
@app.route("/homeXlog")
def homeXlog():
    return render_template("homeXlog.html")


@app.route("/history", methods=['GET', 'POST'])
def history():

    # check what button the user clicked
    if request.method == 'POST':
        # get the id of the saved dataset from form
        saved_data_set_id = request.form.get('saved_data_set_id')

        # if deleted button clicked
        if request.form.get('delete_dataset') == 'true':
            try:
                # remove dataset by dataset_id from the table
                db.delete_saved_user_dataset_by_id(saved_data_set_id)

            except Exception as e:
                # incase of a strange error
                error_message = f"Error deleting dataset"
                return render_template('error.html', error_message=error_message)

        # if 'send to visualizer' button was clicked
        else:

            # get the data from the users_saved_datasets table
            data_set_data = db.get_saved_user_dataset_data_by_id(saved_data_set_id)

            # define data as variables
            user_id = data_set_data['user_id']
            file_name = data_set_data['file_name']
            file_type = data_set_data['file_type']
            file_size = data_set_data['file_size']
            data_set = data_set_data['data_set']

            # add the data set to the temporary dataset table and set the session dataset_id to its incremented id
            session['dataset_id'] = db.add_data_set(user_id, file_name, file_type, file_size, data_set)

            # redirect to dashboard, using the new dataset_id
            return redirect(url_for('dashboard'))
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users_data_sets WHERE user_id=?", (session['user_id'],))
        
        # table column names from db
        table_columns = ['file_name', 'file_size_bytes', 'saved_at']
        
        # Custom headers for the table
        header_names = {
            'file_name': 'File Name',
            'file_size_bytes': 'File Size (bytes)',
            'saved_at': 'Saved At'
        }
        
        # get all rows
        saved_data_set_rows = cursor.fetchall()

        # calculate sum of storage use
        total_storage_used = sum(row['file_size_bytes'] for row in saved_data_set_rows)

    # if there are entries in the table pass it to the template, else pass an empty data table message
    if saved_data_set_rows:
        return render_template("history.html", 
                               total_storage_used=total_storage_used, 
                               saved_data_set_rows=saved_data_set_rows, 
                               table_columns=table_columns, 
                               header_names=header_names)
    else:
        return render_template("history.html", message="No datasets saved.")





@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/error")
def error():
    return render_template("error.html")


if __name__ == '__main__':
    app.run(debug=True)