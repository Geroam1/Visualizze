from flask import Flask, request, render_template, redirect, url_for, session # flask tools
from database import Database # my database class
from werkzeug.security import check_password_hash, generate_password_hash # used to hash passwords for secure private password storing
from werkzeug.utils import secure_filename # renames the file to something proper in the very rare case where it isnt already properly named
import os # allows me to access personal files, currently just to get the secret key from key.env
import io # used to create an 'in memory file' to help store the image in the db
from io import BytesIO # user to convert from binary back to a normal file
import base64 # used to convert images to bytes for storage in the db as a BLOB type
import pandas as pd # library for managing data files in python
import uuid # used to create a random string of letters to use as an annoymous user_id when a user isnt logged in
from apscheduler.schedulers.background import BackgroundScheduler # allows me to run code in the background, used to clean the db periodically
# personal functions
from functions import (
    generate_and_recommend_WIP, 
    process_data, 
    get_data_report_data,
    )


"""
start up processes
"""

# app setup
app = Flask(__name__)

# get the VISUALIZZE_SECRET_KEY from .env file for secure sessions
app.config['SECRET_KEY'] = os.getenv('VISUALIZZE_SECRET_KEY')

# initialize visualizze's data base object
db = Database("./DataBase/visualizze.db")

# start background process to clear the data_set table periodically
def clean_data_base():
    db.clear_data_sets()
hour, minute = 0, 0 # 24 hour clock, time when the temp database table will be cleaned. 0,0 -> midnight
scheduler = BackgroundScheduler()
scheduler.add_job(func=clean_data_base, trigger='cron', hour=hour, minute=minute)
scheduler.start()



"""
routes
"""

# initial route
@app.route("/")
def layout():
        return redirect(url_for("home"))



# route i added to clear the data base as a i develop, should be removed if this app goes live
@app.route("/clear")
def delete_database():
    db.clear_database()
    session.clear()
    return render_template("layout.html")



# register page
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        # get form submits
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm-password")       

        # check if password and confirm password match
        if not (password == confirm_password):
            error_message = "Passwords do not match"
            return render_template("register.html", error_message=error_message)
        
        # check if username already exists
        if db.user_exists(username):
            error_message = "Username already exists"
            return render_template("register.html", error_message=error_message)

        # hash password
        password_hash = generate_password_hash(password)

        # add user data to database
        db.add_user(username, password_hash, email)

        # store user_id in session
        user = db.get_user(username)
        session['user_id'] = user['id']

        # redirect to logged in home
        return redirect("/home")

    return render_template("register.html")



# login page
@app.route("/login", methods=["GET", "POST"])
def login():
    # login error message to pass to login.html
    error_message = None

    if request.method == 'POST':

        # get form submits
        username = request.form.get('username')
        password = request.form.get('password')

        # check if user exists in the data base
        user = db.authenticate_user(username, password)

        # if user exists, check the password is correct
        if user and check_password_hash(user['password_hash'], password):
            # clear any existing session and store user_id in session if user authenticated
            session.clear()
            session.permanent = True # set session to permanent (keeps a user logged in until logout, good quality of life)
            session['user_id'] = user['id']
            return redirect('/home')
        else:
            # if username or password incorrect do not login and prompt the error message
            error_message = "Invalid username or password."

    return render_template('login.html', error_message=error_message)



# logout route
@app.route("/logout")
def logout():
    # clear session
    session.clear()

    # redirect to login page
    return redirect(url_for('login'))



# visualizzer route
@app.route("/visualize")
def visualize():
    return render_template("visualize.html")



# route to handle visualize file upload
# its better to do this to handle future additions (future me here: this just complicated things)
@app.route('/visualize', methods=['POST'])
def upload():

    # if user is not logged in give an annoymous id to use the session object efficently
    if not session.get('user_id'):
        session['user_id_private'] = str(uuid.uuid4())

    # get the uploaded file input form submit
    uploaded_file = request.files.get('file')

    # ensure a file was actually uploaded
    if not uploaded_file:

        # render the error_message to the dropbox page if not
        error_message = "File missing or removed from server. Please reupload the file."
        return render_template('visualize.html', error_message=error_message)
    
    # get filename and ensure it is a csv or xlsx
    filename = uploaded_file.filename
    if not filename.endswith(('.csv', '.xlsx')):
        return "Invalid file format. Please upload a .csv or .xlsx file.", 400
    # renames file to a secure and proper file name for the OS
    filename = secure_filename(filename)
    # add to session for easy access later
    session['file_name'] = filename

    # get user_id, or a user_id_private, to add to the data base
    user_id = session.get('user_id') or session.get('user_id_private')

    # get file size in bytes
    file_size = len(uploaded_file.read())
    uploaded_file.seek(0) # reset file pointer, so that later file reading does not output something empty

    # define the max file size allowed
    max_file_size = 2**20 / 2 # file_size is in Bytes, so 2**20 / 2 would represent 500 kb

    # add this to the session as the users max server storage size for later
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

        # show save request form when rendering, this will only show if the user is logged in (due to the jinja if condition in the template)
        session['show-save-request-form'] = True        

    except Exception as e:
        # if anything goes wrong in this step render the error page
        return render_template('error.html', error_message = f"Error while saving to database")

    # redirect to dashboard
    return redirect(url_for('dashboard'))



# visualizer dashboard route
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():

    # ensure a session is running
    user_id = session.get('user_id') or session.get('user_id_private')
    if not user_id:
        error_message = "No user ID found"
        return render_template('error.html', error_message = error_message)

    # if user is logged in
    if session.get('user_id'):
        saved_data_set_count = db.get_user_id_saved_datasets_counnt(user_id)

        # check if user exceeded their saved datasets count limit, and set the bool allow_saving variable
        max_dataset_save_count = 10
        if saved_data_set_count >= max_dataset_save_count:
            allow_saving = False
        else:
            allow_saving = True

    # get dataset from the database based on user_id
    try:
        # get db entries from the temp dataset table as a dictionary
        # session['dataset_id'] is define in the upload and history route, and represents the current dataset being used
        # from the temporary datasets table
        data_set_entry = db.get_data_set_by_id(session['dataset_id'])

        # if dataset was not found, prompt the user that a file was not uploaded
        if not data_set_entry:
            error_message = "No file uploaded"
            return render_template('error.html', error_message = error_message)

        # define dataset data obtained from the db
        file_name = data_set_entry['file_name']
        file_type = data_set_entry['file_type']
        file_data = data_set_entry['data_set']
        file_size = data_set_entry['file_size']

        # read the binary file_data using pandas
        if file_type == 'xlsx':
            data = pd.read_excel(BytesIO(file_data))
        elif file_type == 'csv':
            data = pd.read_csv(BytesIO(file_data))
        else:
            # render an error if somehow the user managed to upload a file that was xlsx or csv
            return render_template("error.html", error_message = "Unsupported file format")
        
        # process the data to prepare it for visualization
        data = process_data(data)

    except Exception as e:
        # if something goes wrong in this step render the error page with the prompt
        return render_template("error.html", error_message = "Error while retrieving file from the database")
    
    # Data Report data, to show in the data report section
    file_name = file_name
    data_report = get_data_report_data(data)

    # convert the dataset to a html table for to show in the Data section
    table_html = data.to_html(classes="html-table")
    # convert the col data section to a html table as well to show in the Data Report section
    col_data_html = data_report['col data'].to_html(classes="html-table", index=False)

    # prefine these variables as None before POST request, this prevents and error from occuring and instead renders nothing for
    # the visuals section
    x_col = y_col = z_col = None
    
    # handle user form submissions
    if request.method == 'POST':
        
        # save_dataset represents one of the buttons from the request to save the dataset to the users saved datasets,
        # this value will be either 'yes' or 'no' or None
        save_dataset = request.form.get('save_dataset')

        if save_dataset == 'yes':
            # stop showing save request form
            session['show-save-request-form'] = False

            # save the dataset to user_data_sets table
            db.save_user_data_set(user_id=session['user_id'], 
                                  data_set=file_data, 
                                  file_name=file_name,
                                  file_type=file_type, 
                                  file_size=file_size, 
                                  user_max_server_storage_bytes=session['user_max_server_storage'])
        elif save_dataset == 'no':
            # stop showing save request form
            session['show-save-request-form'] = False

        # this checks if the user selected a column from the drop down column select form,
        # the values will represent a column name in the dataset
        if request.form.get('columnx'):
            x_col = request.form.get('columnx')
        if request.form.get('columny'):
            y_col = request.form.get('columny')
    
        # if the user submitted without selecting an option, prompt an errormessage and re-render
        if x_col not in data.columns and y_col not in data.columns:
            if 'visualize' in request.form:
                error_message = "Please select at least 1 column."
                return render_template(
                    'dashboard.html',
                    allow_saving = allow_saving if session.get('user_id') else False, 
                    error_message=error_message, 
                    data_report=data_report, 
                    table_html=table_html, 
                    col_data_html=col_data_html)
        
        # beging generation visuals
        visuals, recommended_visual_name = generate_and_recommend_WIP(
            data,        # dataset
            x_col=x_col, # x axis column name
            y_col=y_col, # y axis column name
        )
        # if any visual was generated
        if recommended_visual_name:
            # get the recommended visual blob, the recommended visual is just the first visual the function plotted
            recommended_visual = visuals[recommended_visual_name] 

            # converts the visual to base64, complicated but this simply allows the visual
            # to be sent to the template as a png image
            img_stream = BytesIO()
            recommended_visual.savefig(img_stream, format='png')
            img_stream.seek(0)
            img_base64 = base64.b64encode(img_stream.read()).decode('utf-8')

        # if their are any visuals plotted, also complicated this allows me to send a list of all visuals plotted
        # to html as png images    
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

        # visual pngs to send
        visual=img_base64 if (request.method == 'POST' and recommended_visual_name) else None,
        encoded_visuals=encoded_visuals if (request.method == 'POST' and visuals) else None
    )



# home page routes
@app.route("/continue_without_account", methods=["POST"])
def continue_without_account():
    # if the user selected to continue without an account, start a private session and redirect to home 
    user_id_private = str(uuid.uuid4())
    session['user_id_private'] = user_id_private
    return redirect(url_for("home"))
@app.route("/home")
def home():
    # if a session is running
    if session.get('user_id') or session.get('user_id_private'):
        if session.get('user_id'):
            # if user is logged in define the user name for the welcome message
            username = str(db.get_username(session.get('user_id')))
        else:
            # if user is not logged in leave the welcome message empty
            username = ""
        # render home.html with or without the username
        return render_template('home.html', username=username)
    # if a session is not running return to initial page
    return redirect(url_for("homeXlog"))
@app.route("/homeXlog")
def homeXlog():
    return render_template("homeXlog.html")



# history route (should have been named saved_datasets)
@app.route("/history", methods=['GET', 'POST'])
def history():

    # check what button the user clicked, either send to visualizer or deleted
    if request.method == 'POST':
        # get the id of the saved dataset from form, this value is defined within jinja as the value of clicking the button
        # and represents the id of the dataset within the user datasets table in the data base
        saved_data_set_id = request.form.get('saved_data_set_id')

        # if delete button clicked
        if request.form.get('delete_dataset') == 'true':
            try:
                # remove dataset by dataset_id from the table
                db.delete_saved_user_dataset_by_id(saved_data_set_id)

            except Exception as e:
                # incase of a strange error during this step
                error_message = f"Error deleting dataset"
                return render_template('error.html', error_message=error_message)

        # if 'send to visualizer' button was clicked
        else:
            try:
                # get the data from the users_saved_datasets table as a dictionary of column keys and row values
                data_set_data = db.get_saved_user_dataset_data_by_id(saved_data_set_id)

                # define the data read as variables
                user_id = data_set_data['user_id']
                file_name = data_set_data['file_name']
                file_type = data_set_data['file_type']
                file_size = data_set_data['file_size']
                data_set = data_set_data['data_set']

                # add the data set to the temporary dataset table and set the session dataset_id to its incremented id
                session['dataset_id'] = db.add_data_set(user_id, file_name, file_type, file_size, data_set)

                # redirect to dashboard, using the new dataset_id
                return redirect(url_for('dashboard'))
            
            except Exception as e:
                # incase of a strange error during this step
                error_message = f"Error in sending dataset to visualizer"
                return render_template('error.html', error_message=error_message)

    # connect to the users_data_sets table based on the session id, and display their saved datasets in a html table
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users_data_sets WHERE user_id=?", (session['user_id'],))
        
        # table column names from the db
        table_columns = ['file_name', 'file_size_bytes', 'saved_at']
        
        # rename the column headers for the table
        header_names = {
            'file_name': 'File Name',
            'file_size_bytes': 'File Size (bytes)',
            'saved_at': 'Saved At'
        }
        
        # get all rows
        saved_data_set_rows = cursor.fetchall()

    # if there are entries in the table pass it to the template, else pass an empty data table message
    if saved_data_set_rows:
        return render_template("history.html", 
                               saved_data_set_rows=saved_data_set_rows, 
                               table_columns=table_columns, 
                               header_names=header_names)
    else:
        return render_template("history.html", message="No datasets saved.")



# tutorial route
@app.route("/tutorial")
def tutorial():
    return render_template("tutorial.html")



# about route
@app.route("/about")
def about():
    return render_template("about.html")



# error route
@app.route("/error")
def error():
    return render_template("error.html")


if __name__ == '__main__':
    app.run()