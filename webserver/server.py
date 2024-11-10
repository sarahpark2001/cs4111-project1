#!/usr/bin/env python3

"""
Columbia W4111 Intro to databases
Example webserver

To run locally

    python server.py

Go to http://localhost:8111 in your browser


A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""

import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, session, Response
import secrets

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)
app.secret_key = secrets.token_hex(16)

# Use the DB credentials you received by e-mail
DB_USER = "shp2156"
DB_PASSWORD = "shp2156"

DB_SERVER = "w4111.cisxo09blonu.us-east-1.rds.amazonaws.com"

DATABASEURI = "postgresql://"+DB_USER+":"+DB_PASSWORD+"@"+DB_SERVER+"/w4111"

engine = create_engine(DATABASEURI)

@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request 
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request

  The variable g is globally accessible
  """
  try:
    g.conn = engine.connect()
  except:
    print("uh oh, problem connecting to database")
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass

@app.route('/')
def index():
   return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id = request.form['userid']
        password = request.form['password']
        user_type = request.form['user_type']  
        
        if user_type == 'student':
            cursor = g.conn.execute(
                "SELECT name FROM shp2156.Student_Attends WHERE student_id = %s AND password = %s",
                (user_id, password)
            )
            user = cursor.fetchone()
            cursor.close()

            if user is None:
                return render_template('login.html', info='Invalid Student ID or Password')
            else:
                session['user_id'] = user_id
                session['user_type'] = 'student'
                return redirect('/student_dashboard')
        
        elif user_type == 'staff':
            cursor = g.conn.execute(
                "SELECT name FROM shp2156.Staffs WHERE staff_id = %s AND password = %s",
                (user_id, password)
            )
            user = cursor.fetchone()
            cursor.close()

            if user is None:
                return render_template('login.html', info='Invalid Staff ID or Password')
            else:
                session['user_id'] = user_id
                session['user_type'] = 'staff'
                return redirect('/staff_dashboard')

    return render_template('login.html')

@app.route('/signup', methods=['POST'])
def signup():
    user_type = request.form.get('user_type')
    
    if user_type == 'student':
        return redirect('/signup_student')
    elif user_type == 'staff':
        return redirect('/signup_staff')
    else:
        return render_template('login.html', info="Please select a valid user type for sign-up.")

@app.route('/student_dashboard')
def student_dashboard():
    if 'user_id' not in session or session.get('user_type') != 'student':
        return redirect('/login')

    student_id = session['user_id']
    student = g.conn.execute(
        "SELECT name, total_points, program_option FROM shp2156.Student_Attends WHERE student_id = %s",
        (student_id,)
    ).fetchone()

    return render_template('student_dashboard.html', student=student)

@app.route('/staff_dashboard')
def staff_dashboard():
    return render_template('staff_dashboard.html', name=session.get('user_id'))

@app.route('/signup_student', methods=['GET', 'POST'])
def signup_student():
    if request.method == 'POST':

        #auto assign student_id to be 1+current max student_id
        cursor = g.conn.execute("SELECT COALESCE(MAX(student_id), 0) + 1 FROM shp2156.Student_Attends")
        student_id = cursor.fetchone()[0]
        cursor.close()
        
        name = request.form['name']
        email = request.form['email']
        password1 = request.form['password1']
        password2 = request.form['password2']
        school_name = request.form['school_name']
        dept_name = request.form['dept_name']
        div_name = request.form['div_name']
        program_option = request.form['program_option']
        year = request.form['year']

        # Check if passwords match
        if password1 != password2:
            return render_template('signup_student.html', info="Passwords do not match.")

        # Check if email already exists
        cursor = g.conn.execute("SELECT * FROM shp2156.Student_Attends WHERE email = %s", (email,))
        existing_user = cursor.fetchone()
        cursor.close()

        if existing_user:
            return render_template('signup_student.html', info="Email already exists.")

        # Validate department and division pair
        valid_divisions = {
            'Administration': ['Public Affairs', 'Academics'],
            'Logistics': ['Transportation', 'Finance'],
            'Operations': ['Events', 'Training'],
            'Supply': ['Wardroom', 'Outreach']
        }

        if dept_name not in valid_divisions or div_name not in valid_divisions[dept_name]:
            return render_template('signup_student.html', info="Invalid division for the selected department.")

        g.conn.execute(
            "INSERT INTO shp2156.Student_Attends (student_id, name, email, password, school_name, dept_name, div_name, program_option, year) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (student_id, name, email, password1, school_name, dept_name, div_name, program_option, year)
        )
        info_message = f"You have been assigned User ID {student_id}. Please save your User ID and password for future logins."
        return redirect(url_for('login', info=info_message))
    
    return render_template('signup_student.html')


@app.route('/signup_staff', methods=['GET', 'POST'])
def signup_staff():
    if request.method == 'POST':
        #assign staff_id to be current max staff_id + 1
        cursor = g.conn.execute("SELECT COALESCE(MAX(staff_id), 0) + 1 FROM shp2156.Staffs")
        staff_id = cursor.fetchone()[0]
        cursor.close()
        
        name = request.form['name']
        email = request.form['email']
        password1 = request.form['password1']
        password2 = request.form['password2']
        phone_number = request.form['phone_number']
        pay_grade = request.form['pay_grade']
        component = request.form['component']
        job_title = request.form['job_title']

        # Check if passwords match
        if password1 != password2:
            return render_template('signup_staff.html', info="Passwords do not match.")

        # Check if email already exists
        cursor = g.conn.execute("SELECT * FROM shp2156.Staffs WHERE email = %s", (email,))
        existing_user = cursor.fetchone()
        cursor.close()
        
        if existing_user:
            return render_template('signup_staff.html', info="Email already exists.")

        # Insert new staff record
        g.conn.execute(
            "INSERT INTO shp2156.Staffs (staff_id, name, email, password, phone_number, pay_grade, component, job_title) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            (staff_id, name, email, password1, phone_number, pay_grade, component, job_title)
        )
        
        return redirect('/login')
    
    return render_template('signup_staff.html')


if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using

        python server.py

    Show the help text using

        python server.py --help

    """

    HOST, PORT = host, port
    print("running on %s:%d" % (HOST, PORT))
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


  run()
