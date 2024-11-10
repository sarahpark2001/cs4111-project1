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

# ranks dictionary to use for directory, etc.
ranks = {
    'USMC': {
        'E-1': 'Private', 'E-2': 'Private First Class', 'E-3': 'Lance Corporal', 'E-4': 'Corporal',
        'E-5': 'Sergeant', 'E-6': 'Staff Sergeant', 'E-7': 'Gunnery Sergeant', 'E-8': 'Master Sergeant',
        'E-9': 'Master Gunnery Sergeant', 'O-1': 'Second Lieutenant', 'O-2': 'First Lieutenant', 'O-3': 'Captain',
        'O-4': 'Major', 'O-5': 'Lieutenant Colonel', 'O-6': 'Colonel', 'O-7': 'Brigadier General',
        'O-8': 'Major General', 'O-9': 'Lieutenant General', 'O-10': 'General'
    },
    'USN': {
        'E-1': 'Seaman Recruit', 'E-2': 'Seaman Apprentice', 'E-3': 'Seaman',
        'E-4': 'Petty Officer Third Class', 'E-5': 'Petty Officer Second Class', 'E-6': 'Petty Officer First Class',
        'E-7': 'Chief Petty Officer', 'E-8': 'Senior Chief Petty Officer', 'E-9': 'Master Chief Petty Officer',
        'O-1': 'Ensign', 'O-2': 'Lieutenant Junior Grade', 'O-3': 'Lieutenant', 'O-4': 'Lieutenant Commander',
        'O-5': 'Commander', 'O-6': 'Captain', 'O-7': 'Rear Admiral (lower half)', 'O-8': 'Rear Admiral (upper half)',
        'O-9': 'Vice Admiral', 'O-10': 'Admiral'
    }
}

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

@app.route('/directory')
def directory():
    if 'user_id' not in session:
        return redirect('/login')  

    db_session = SessionFactory()

    staff_list = db_session.query(Staffs).all()
    student_list = db_session.query(Student_Attends).all()

    staff_data = []
    for staff in staff_list:
        component_key = 'USN' if staff.component == 'USNR' else staff.component
        rank_title = ranks.get(component_key, {}).get(staff.pay_grade, '') if component_key != 'Civilian' else ''
        staff_data.append({
            'title': rank_title,
            'name': staff.name,
            'phone_number': staff.phone_number,
            'email': staff.email
        })

    student_data = []
    for student in student_list:
        title = 'OC' if student.program_option == 'STA-21' else 'MIDN'
        student_data.append({
            'title': title,
            'name': student.name,
            'phone_number': student.phone_number,
            'email': student.email
        })

    db_session.close()

    return render_template('directory.html', staff_data=staff_data, student_data=student_data)
t_data)

@app.route('/login', methods=['GET', 'POST'])
def login():

    info = request.args.get('info')
    
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

    return render_template('login.html', info=info)

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()  
    return redirect('/login')

@app.route('/signup', methods=['POST'])
def signup():
    user_type = request.form.get('user_type')
    
    if user_type == 'student':
        return redirect('/signup_student')
    elif user_type == 'staff':
        return redirect('/signup_staff')
    else:
        return render_template('login.html', info="Please select a valid user type for sign-up.")

@app.route('/rsvp', methods=['GET', 'POST'])
def rsvp():
    if 'user_id' not in session or session.get('user_type') != 'student':
        return redirect('/login')
    
    student_id = session['user_id']
    
    events_query = """
        SELECT ec.event_title, ec.event_date, ec.event_start, ec.max_capacity, 
               (ec.max_capacity - COUNT(DISTINCT p.student_id2)) AS spots_remaining
        FROM shp2156.Events_Created ec
        LEFT JOIN shp2156.Participates p 
        ON ec.event_id = p.event_id AND ec.event_title = p.event_title
        GROUP BY ec.event_id, ec.event_title, ec.event_date, ec.event_start, ec.max_capacity
        ORDER BY ec.event_date, ec.event_start;
    """
    
    events = g.conn.execute(events_query).fetchall()

    if request.method == 'POST':
        for event in events:
            event_title = event['event_title']
            rsvp_status = request.form.get(f"rsvp_{event_title}")

            if rsvp_status == 'yes':
                # Add student to the event if not already signed up
                g.conn.execute(
                    """
                    INSERT INTO shp2156.Participates (student_id, event_id, student_id2)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (student_id, event_id, student_id2) DO NOTHING
                    """,
                    (student_id, event['event_id'], student_id)
                )
            elif rsvp_status == 'no':
                # Remove student from the event if they cancel RSVP
                g.conn.execute(
                    """
                    DELETE FROM shp2156.Participates 
                    WHERE event_id = %s AND student_id2 = %s
                    """,
                    (event['event_id'], student_id)
                )
        return redirect('/student_dashboard')

    return render_template('rsvp.html', events=events)



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
    staff_id = session.get('user_id')
    if not staff_id:
        return redirect('/login')

    with engine.connect() as conn:
        result = conn.execute(
            "SELECT name, component, pay_grade FROM Staffs WHERE staff_id = %s", (staff_id,)
        ).fetchone()

    if not result:
        return "Staff member not found", 404

    name, component, pay_grade = result['name'], result['component'], result['pay_grade']

    title = ranks.get(component, {}).get(pay_grade, "Staff")

    return render_template('staff_dashboard.html', title=title, name=name)

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
        
        # Redirect to login with info message
        info_message = f"You have been assigned User ID {staff_id}. Please save your User ID and password for future logins."
        return redirect(url_for('login', info=info_message))
    
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
