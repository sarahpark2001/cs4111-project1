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
from flask import Flask, request, render_template, g, redirect, session, Response, url_for
from datetime import datetime
import secrets
import re

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

@app.context_processor
def inject_ranks():
    return dict(ranks=ranks)

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

@app.route('/confirm_delete_student', methods=['GET', 'POST'])
def confirm_delete_student():
    if 'user_id' not in session or session.get('user_type') != 'staff':
        return redirect('/login')

    student_id = request.args.get('student_id')

    if request.method == 'POST':
        confirm = request.form.get('confirm')
        if confirm == 'yes':
            # Perform deletion
            try:
                g.conn.execute("DELETE FROM shp2156.Student_Attends WHERE student_id = %s", (student_id,))
                g.conn.execute("DELETE FROM shp2156.belongs WHERE student_id = %s", (student_id,))
                return redirect(url_for('staff_dashboard', info=f"Student ID {student_id} has been deleted successfully."))
            except Exception as e:
                print("Error deleting student:", e)
                return redirect(url_for('staff_dashboard', info="An error occurred while trying to delete the student."))
        else:
            # If deletion is canceled
            return redirect(url_for('staff_dashboard', info="Deletion canceled."))

    # Fetch student information for confirmation display
    student = g.conn.execute(
        "SELECT name FROM shp2156.Student_Attends WHERE student_id = %s", (student_id,)
    ).fetchone()
    if not student:
        return redirect(url_for('staff_dashboard', info="Student not found."))

    return render_template('confirm_delete_student.html', student=student, student_id=student_id)


@app.route('/manage_student', methods=['GET', 'POST'])
def manage_student():
    if 'user_id' not in session or session.get('user_type') != 'staff':
        return redirect('/login')

    if request.method == 'POST':
        student_id = request.form.get('student_id')
        
        # Retrieve the student details from the database
        student = g.conn.execute(
            "SELECT student_id, name FROM shp2156.Student_Attends WHERE student_id = %s",
            (student_id,)
        ).fetchone()

        # If student is found, prompt staff for modify/delete options
        if student:
            return render_template('manage_student_confirm.html', student=student)
        else:
            # If no student is found, display an error message
            message="No student found with that ID."
            return render_template('manage_student.html', info=message)

    return render_template('manage_student.html')

@app.route('/manage_student_action', methods=['POST'])
def manage_student_action():
    if 'user_id' not in session or session.get('user_type') != 'staff':
        return redirect('/login')

    student_id = request.form.get('student_id')
    action = request.form.get('action')
    
    print(f"manage_student_action - student_id: '{student_id}', action: '{action}'")

    # Ensure student_id is provided and valid
    if not student_id:
        return redirect(url_for('staff_dashboard', info="No student ID provided for the action."))

    if action == 'modify':
        # Redirect to modify student information
        return redirect(url_for('manage_student_modify', student_id=student_id))

    elif action == 'delete':
        # Redirect to the new delete confirmation route
        return redirect(url_for('confirm_delete_student', student_id=student_id))

    return redirect(url_for('staff_dashboard'))


@app.route('/directory')
def directory():
    if 'user_id' not in session:
        return redirect('/login')  
        
    staff_query = """
        SELECT job_title, component, name, phone_number, email
        FROM shp2156.Staffs
    """
    staff = g.conn.execute(staff_query).fetchall()

    student_query = """
        SELECT sa.name, sa.email, sa.program_option, sa.school_name, sa.year, b.dept_name, b.div_name
        FROM shp2156.Student_Attends sa JOIN shp2156.belongs b
        ON sa.student_id = b.student_id
    """
    student = g.conn.execute(student_query).fetchall()

    return render_template('directory.html', staff_data=staff, student_data=student)

@app.route('/directory_staff')
def directory_staff():
    if 'user_id' not in session:
        return redirect('/login')  
        
    staff_query = """
        SELECT job_title, component, name, phone_number, email
        FROM shp2156.Staffs
    """
    staff = g.conn.execute(staff_query).fetchall()

    student_query = """
        SELECT sa.name, sa.email, sa.program_option, sa.school_name, sa.year, b.dept_name, b.div_name, sa.total_points
        FROM shp2156.Student_Attends sa JOIN shp2156.belongs b
        ON sa.student_id = b.student_id
    """
    student = g.conn.execute(student_query).fetchall()

    return render_template('directory_staff.html', staff_data=staff, student_data=student)

@app.route('/edit_staff', methods=['GET', 'POST'])
def edit_staff():
    if 'user_id' not in session or session.get('user_type') != 'staff':
        return redirect('/login')

    staff_id = session['user_id']

    # Fetch existing staff data for GET request
    if request.method == 'GET':
        staff = g.conn.execute(
            "SELECT name, email, phone_number, pay_grade, component, job_title FROM shp2156.Staffs WHERE staff_id = %s",
            (staff_id,)
        ).fetchone()

        return render_template('edit_staff.html', staff=staff)

    # Process form submission on POST request
    if request.method == 'POST':
        # Retrieve form data
        name = request.form.get('name')
        email = request.form.get('email')
        phone_number = request.form.get('phone_number')
        job_title = request.form.get('job_title')
        component = request.form.get('component')
        pay_grade = request.form.get('pay_grade')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        # Validation: Ensure name is provided and valid
        if not name or not re.match(r"^[A-Za-z\s'-]{2,50}$", name):
            message = "Name must be 2-50 characters and contain only letters, spaces, apostrophes, or hyphens."
            return redirect(url_for('edit_staff', info=message))

        # Validate email
        email_regex = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
        if not email or not re.match(email_regex, email):
            message = "Please enter a valid email address."
            return redirect(url_for('edit_staff', info=message))
        
        # Validate phone number.
        phone_regex = r"^\d{3}-\d{3}-\d{4}$"
        if not re.match(phone_regex, phone_number):
            message = "Phone number must be in the format ###-###-####."
            return redirect(url_for('edit_staff', info=message))

        # Validation: Ensure passwords match if provided
        if password1 and password1 != password2:
            info_message = "Passwords do not match."
            return redirect(url_for('edit_staff', info=info_message))

        # Construct SQL query based on whether the password needs to be updated
        if password1:  # If a new password is provided
            update_query = """
                UPDATE shp2156.Staffs
                SET name = %s, email = %s, phone_number = %s,
                    pay_grade = %s, component = %s, job_title = %s, password = %s
                WHERE staff_id = %s
            """
            update_data = (name, email, phone_number, pay_grade, component, job_title, password1, staff_id)
        else:  # If no password update is needed
            update_query = """
                UPDATE shp2156.Staffs
                SET name = %s, email = %s, phone_number = %s,
                    pay_grade = %s, component = %s, job_title = %s
                WHERE staff_id = %s
            """
            update_data = (name, email, phone_number, pay_grade, component, job_title, staff_id)

        # Execute the query with positional placeholders
        try:
            g.conn.execute(update_query, update_data)
            info_message = "Your information has been updated successfully."
            return redirect(url_for('staff_dashboard', info=info_message))
        
        except Exception as e:
            print("Error updating staff information:", e)
            info_message = "An error occurred while updating your information."
            return redirect(url_for('edit_staff', info=info_message))
            # return render_template('edit_staff.html', staff=staff, info="An error occurred while updating your information.")


@app.route('/manage_student_modify', methods=['GET', 'POST'])
def manage_student_modify():
    if 'user_id' not in session or session.get('user_type') != 'staff':
        return redirect('/login')

    student_id = request.args.get('student_id')
    if not student_id:
        return "No student ID provided.", 400

    # Fetch school, department, and division data for form
    cursor = g.conn.execute("SELECT school_name FROM schools")
    schools = cursor.fetchall()

    cursor = g.conn.execute("SELECT dept_name FROM departments")
    departments = cursor.fetchall()

    cursor = g.conn.execute("SELECT div_name, dept_name FROM division_belongs")
    divisions = cursor.fetchall()

    dept_divisions = {}
    for division, department in divisions:
        if department not in dept_divisions:
            dept_divisions[department] = []
        dept_divisions[department].append(division)

    # Fetch existing student data
    student = g.conn.execute(
        "SELECT name, email, program_option, year, school_name, div_name, dept_name "
        "FROM shp2156.Student_Attends sa JOIN shp2156.belongs b "
        "ON sa.student_id = b.student_id WHERE sa.student_id = %s",
        (student_id,)
    ).fetchone()

    if not student:
        return "Student not found", 404

    if request.method == 'GET':
        return render_template(
            'edit_student.html',
            page_title="Modify Student Information",
            form_action=url_for('manage_student_modify', student_id=student_id),
            student=student,
            schools=schools,
            departments=departments,
            dept_divisions=dept_divisions
        )

    # Handle form submission
    name = request.form.get('name')
    email = request.form.get('email')
    password1 = request.form.get('password1')
    password2 = request.form.get('password2')
    school_name = request.form.get('school_name')
    dept_name = request.form.get('dept_name')
    div_name = request.form.get('div_name')
    program_option = request.form.get('program_option')
    year = request.form.get('year')

    # Check for duplicate email if changed
    if email != student.email:
        duplicate_email = g.conn.execute(
            "SELECT student_id FROM shp2156.Student_Attends WHERE email = %s AND student_id != %s",
            (email, student_id)
        ).fetchone()

        if duplicate_email:
            message= "Email already exists."
            return redirect(url_for('edit_student', student=student, schools=schools, departments=departments, dept_divisions=dept_divisions, info=message))
            # return render_template('edit_student.html', student=student, schools=schools, departments=departments, dept_divisions=dept_divisions, info="This email is already in use by another student.")

    if password1 != password2:
        message="Passwords do not match."
        return redirect(url_for('edit_student', info=message))
        return render_template('edit_student.html', student=student, schools=schools, departments=departments, dept_divisions=dept_divisions, info="Passwords do not match.")

    try:
        # Update `Student_Attends`
        if password1:
            g.conn.execute(
                "UPDATE shp2156.Student_Attends SET name = %s, email = %s, program_option = %s, year = %s, school_name = %s, password = %s WHERE student_id = %s",
                (name, email, program_option, year, school_name, password1, student_id)
            )
        else:
            g.conn.execute(
                "UPDATE shp2156.Student_Attends SET name = %s, email = %s, program_option = %s, year = %s, school_name = %s WHERE student_id = %s",
                (name, email, program_option, year, school_name, student_id)
            )

        # Update belongs
        g.conn.execute(
            "UPDATE shp2156.belongs SET div_name = %s, dept_name = %s WHERE student_id = %s",
            (div_name, dept_name, student_id)
        )

        return redirect(url_for('staff_dashboard', info=f"Student information for {name} (ID: {student_id}) has been updated successfully."))

    except Exception as e:
        print("Error updating student information:", e)
        message = "An error occurred while updating the student's information."
        return redirect(url_for('edit_student', info=message))
        # return render_template('edit_student.html', student=student, schools=schools, departments=departments, dept_divisions=dept_divisions, info="An error occurred while updating the student's information.")


@app.route('/edit_student', methods=['GET', 'POST'])
def edit_student():
    if 'user_id' not in session or session.get('user_type') != 'student':
        return redirect('/login')

    student_id = session['user_id']  # Only allow the logged-in student's ID

    if request.method == 'GET':
        # Fetch school, department, and division data for form
        cursor = g.conn.execute("SELECT school_name FROM schools")
        schools = cursor.fetchall()

        cursor = g.conn.execute("SELECT dept_name FROM departments")
        departments = cursor.fetchall()

        cursor = g.conn.execute("SELECT div_name, dept_name FROM division_belongs")
        divisions = cursor.fetchall()

        dept_divisions = {}
        for division, department in divisions:
            if department not in dept_divisions:
                dept_divisions[department] = []
            dept_divisions[department].append(division)

        # Fetch existing student data for form
        student = g.conn.execute(
            "SELECT name, email, program_option, year, school_name, div_name, dept_name "
            "FROM shp2156.Student_Attends sa JOIN shp2156.belongs b "
            "ON sa.student_id = b.student_id WHERE sa.student_id = %s",
            (student_id,)
        ).fetchone()

        return render_template(
            'edit_student.html',
            page_title="Edit Your Information",
            form_action=url_for('edit_student'),
            student=student,
            schools=schools,
            departments=departments,
            dept_divisions=dept_divisions
        )

    if request.method == 'POST':
        # Handle form submission
        name = request.form.get('name')
        email = request.form.get('email')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')
        school_name = request.form.get('school_name')
        dept_name = request.form.get('dept_name')
        div_name = request.form.get('div_name')
        program_option = request.form.get('program_option')
        year = request.form.get('year')

        # Fetch existing student data for form
        student = g.conn.execute(
            "SELECT name, email, program_option, year, school_name, div_name, dept_name "
            "FROM shp2156.Student_Attends sa JOIN shp2156.belongs b "
            "ON sa.student_id = b.student_id WHERE sa.student_id = %s",
            (student_id,)
        ).fetchone()

        if not name or not re.match(r"^[A-Za-z\s'-]{2,50}$", name):
            message = "Name must be 2-50 characters and contain only letters, spaces, apostrophes, or hyphens."
            return redirect(url_for('edit_student', info=message))
        
        email_regex = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
        if not email or not re.match(email_regex, email):
            message = "Please enter a valid email address."
            return redirect(url_for('edit_student', info=message))

        # Validate and update
        if email != student.email:
            duplicate_email = g.conn.execute(
                "SELECT student_id FROM shp2156.Student_Attends WHERE email = %s AND student_id != %s",
                (email, student_id)
            ).fetchone()

            if duplicate_email:
                message = "Email already exists."
                return redirect(url_for('edit_student', info=message))

        if password1 != password2:
            message = "Passwords do not match."
            return redirect(url_for('edit_student', info=message))
        

        try:
            # Update student data
            if password1:
                g.conn.execute(
                    "UPDATE shp2156.Student_Attends SET name = %s, email = %s, program_option = %s, year = %s, school_name = %s, password = %s WHERE student_id = %s",
                    (name, email, program_option, year, school_name, password1, student_id)
                )
            else:
                g.conn.execute(
                    "UPDATE shp2156.Student_Attends SET name = %s, email = %s, program_option = %s, year = %s, school_name = %s WHERE student_id = %s",
                    (name, email, program_option, year, school_name, student_id)
                )

            # Update belongs
            g.conn.execute(
                "UPDATE shp2156.belongs SET div_name = %s, dept_name = %s WHERE student_id = %s",
                (div_name, dept_name, student_id)
            )

            return redirect(url_for('student_dashboard', info="Your information has been updated successfully."))

        except Exception as e:
            print("Error updating student information:", e)
            message="An error occurred while updating your information."
            return redirect(url_for('edit_student', info=message))


@app.route('/login', methods=['GET', 'POST'])
def login():

    info = request.args.get('info')
    
    if request.method == 'POST':
        user_id = request.form['userid']
        password = request.form['password']
        user_type = request.form['user_type']  

        if user_type not in ['student', 'staff'] or not user_id or not password:
            return render_template('login.html', info='Please enter valid credentials.')
        
        if user_type == 'student':
            try:
                cursor = g.conn.execute(
                    "SELECT name FROM shp2156.Student_Attends WHERE student_id = %s AND password = %s",
                    (user_id, password)
                )
                user = cursor.fetchone()
                cursor.close()
            except Exception as e:
                print(e)
                user = None
            
            if user is None:
                return render_template('login.html', info='Invalid Student ID or Password')
            else:
                session['user_id'] = user_id
                session['user_type'] = 'student'
                return redirect('/student_dashboard')
        
        elif user_type == 'staff':
            try:
                cursor = g.conn.execute(
                    "SELECT name FROM shp2156.Staffs WHERE staff_id = %s AND password = %s",
                    (user_id, password)
                )
                user = cursor.fetchone()
                cursor.close()
            except Exception as e:
                print(e)
                user = None

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
    
    division_query = """
        SELECT div_name
        FROM shp2156.belongs
        WHERE student_id = %s
    """
    division_result = g.conn.execute(division_query, (student_id,)).fetchone()
    division = division_result['div_name']
    
    division_events_query = """
        SELECT a.event_id, a.staff_id, ec.student_id, ec.event_title, ec.event_date, ec.event_start, ec.max_capacity, ec.event_points,
               (ec.max_capacity - COUNT(DISTINCT p.student_id2)) AS spots_remaining
        FROM shp2156.invites a
        JOIN shp2156.events_created ec ON a.event_id = ec.event_id AND a.event_title = ec.event_title
        LEFT JOIN shp2156.Participates p ON ec.event_id = p.event_id AND ec.event_title = p.event_title
        WHERE a.div_name = %s AND ec.event_date > CURRENT_DATE
        GROUP BY a.event_id, a.staff_id, ec.student_id, ec.event_id, ec.event_title, ec.event_date, ec.event_start, ec.max_capacity, ec.event_points
        ORDER BY ec.event_date, ec.event_start;
    """
    
    division_events = g.conn.execute(division_events_query, (division,)).fetchall()

    invitation_messages = []
    for div_event in division_events:
        event_title = div_event['event_title']
        event_date = div_event['event_date']
        invitation_messages.append(f"You are invited to RSVP for '{event_title}' on {event_date}!")

    rsvp_query="""
        SELECT ec.event_title, ec.event_date 
        FROM shp2156.Participates p
        JOIN shp2156.events_created ec ON p.event_id = ec.event_id
        WHERE p.student_id2 = %s
    """
    rsvp_result = g.conn.execute(rsvp_query, (student_id,)).fetchall()

    rsv_messages = []
    for rsvp in rsvp_result:
        event_title = rsvp['event_title']
        event_date = rsvp['event_date']
        rsv_messages.append(f"You have already RSVPed for '{event_title}' on {event_date}.")

    events_query = """
        SELECT a.event_id, a.staff_id, ec.student_id, ec.event_title, ec.event_date, ec.event_start, ec.max_capacity, ec.event_points, (ec.max_capacity - COUNT(DISTINCT p.student_id2)) AS spots_remaining
        FROM shp2156.approves a
        JOIN shp2156.events_created ec ON a.event_id = ec.event_id
        LEFT JOIN shp2156.Participates p ON ec.event_id = p.event_id 
        WHERE ec.event_date > CURRENT_DATE
        GROUP BY a.event_id, a.staff_id, ec.student_id, ec.event_id, ec.event_title, ec.event_date, ec.event_start, ec.max_capacity, ec.event_points
        ORDER BY ec.event_date, ec.event_start;
    """
    events = g.conn.execute(events_query).fetchall()

    if request.method == 'POST':
        message = ""
        for event in events:
            event_title = event['event_title']
            event_id = event['event_id']
            event_points = event['event_points']
            event_date = event['event_date']
            rsvp_status = request.form.get(f"rsvp_{event_id}")

            check_query = """
                SELECT 1
                FROM shp2156.participates
                WHERE student_id = %s AND event_id = %s AND student_id2 = %s AND staff_id = %s AND event_title = %s
            """
            check = g.conn.execute(check_query, (event['student_id'], event_id, student_id, event['staff_id'], event_title)).fetchone()

            if rsvp_status == 'yes':
                if check:
                    message += f"You have already RSVPed for '{event_title}' on {event_date}.<br>"
                elif event['spots_remaining'] <= 0:
                    message += f"Sorry, '{event_title}' on {event_date} is full.<br>"
                else:
                    # Add student to the event if not already signed up
                    g.conn.execute(
                        """
                        INSERT INTO shp2156.Participates (student_id, event_id, student_id2, staff_id, event_title)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (student_id, event_id, student_id2, staff_id, event_title) DO NOTHING
                        """,
                        (event['student_id'], event['event_id'], student_id, event['staff_id'], event_title)
                    )
                    
                    # Increase student points by event points on RSVP
                    g.conn.execute(
                        """
                        UPDATE shp2156.student_attends
                        SET total_points = total_points + %s
                        WHERE student_id = %s
                        """,
                        (event_points, student_id)
                    )
                
                    message += f"You have RSVPed for '{event_title}' on {event_date}. You earned {event_points} points.<br>"

            elif rsvp_status == 'no':
                if check:
                    # Remove student from the event if they cancel RSVP
                    g.conn.execute(
                        """
                        DELETE FROM shp2156.Participates 
                        WHERE event_id = %s AND student_id2 = %s
                        """,
                        (event['event_id'], student_id)
                    )
                    
                    # Decrease student points by event points on cancel
                    g.conn.execute(
                        """
                        UPDATE shp2156.student_attends
                        SET total_points = total_points - %s
                        WHERE student_id = %s
                        """,
                        (event_points, student_id)
                    )

                    message += f"You have canceled your RSVP for '{event_title}' on {event_date}. You lost {event_points} points.<br>"
                else:
                    message += f"You have not RSVPed for '{event_title}' on {event_date}.<br>"
        total_points_result = g.conn.execute(
            "SELECT total_points FROM shp2156.student_attends WHERE student_id = %s",
            (student_id,)
        ).fetchone()
        total_points = total_points_result['total_points']

        message += f"You now have {total_points} points."

        return redirect(url_for('student_dashboard', info=message))

    return render_template('rsvp.html', events=events, invitation_messages=invitation_messages, rsvp_messages=rsv_messages, division_events=division_events)


@app.route('/student_dashboard')
def student_dashboard():
    if 'user_id' not in session or session.get('user_type') != 'student':
        return redirect('/login')

    student_id = session['user_id']
    student = g.conn.execute(
        "SELECT name, total_points, program_option FROM shp2156.Student_Attends WHERE student_id = %s",
        (student_id,)
    ).fetchone()
    
    message = request.args.get('info', None)

    return render_template('student_dashboard.html', student=student, info=message)


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
    message = request.args.get('info', None)

    return render_template('staff_dashboard.html', title=title, name=name, info = message)


@app.route('/signup_student', methods=['GET', 'POST'])
def signup_student():
    if request.method == 'POST':
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

        if name == '' or email == '' or password1 == '' or password2 == '' or school_name == '' or dept_name == '' or div_name == '' or program_option == '' or year == '':
            return redirect(url_for('signup_student', info="All fields are required."))

        # Validate name
        if not name or not re.match(r"^[A-Za-z\s'-]{2,50}$", name):
            message = "Name must be 2-50 characters and contain only letters, spaces, apostrophes, or hyphens."
            return redirect(url_for('signup_student', info=message))

        # Validate email
        email_regex = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
        if not email or not re.match(email_regex, email):
            message = "Please enter a valid email address."
            return redirect(url_for('signup_student', info=message))

        # Check if passwords match
        if password1 != password2:
            message = "Passwords do not match."
            return redirect(url_for('signup_student', info=message))
        
        try:
            cursor = g.conn.execute("SELECT * FROM shp2156.Student_Attends WHERE email = %s", (email,))
            existing_user = cursor.fetchone()
            cursor.close()
        except Exception as e:
            print(e)
            existing_user = None

        if existing_user:
            message = "Email already exists."
            return redirect(url_for('signup_student', info=message))

        cursor = g.conn.execute("SELECT div_name, dept_name FROM division_belongs")
        divisions = cursor.fetchall()

        dept_divisions = {}
        for division, department in divisions:
            if department not in dept_divisions:
                dept_divisions[department] = []
            dept_divisions[department].append(division)

        if dept_name not in dept_divisions or div_name not in dept_divisions[dept_name]:
            return redirect(url_for('signup_student', info="Invalid division for the selected department."))

        try:
            g.conn.execute(
                "INSERT INTO shp2156.Student_Attends (student_id, email, name, program_option, total_points, year, school_name, password) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                (student_id, email, name, program_option, 0, year, school_name, password1)
            )
        except Exception as e:
            print(e)
            return redirect(url_for('signup_student', info="Error creating student account."))
        try:
            g.conn.execute(
                "INSERT INTO shp2156.belongs (student_id, div_name, dept_name) "
                "VALUES (%s, %s, %s)",
                (student_id, div_name, dept_name)
            )
        except Exception as e:
            print(e)
            return redirect(url_for('signup_student', info="Error creating student account."))

        # Successful registration message
        message = f"You have been assigned User ID {student_id}. Please save your User ID and password for future logins."
        return redirect(url_for('login', info=message))

    # Retrieve `info` from query parameters if present (on redirect)
    info = request.args.get('info', '')
    
    cursor = g.conn.execute("SELECT school_name FROM schools")
    schools = cursor.fetchall()

    cursor = g.conn.execute("SELECT dept_name FROM departments")
    departments = cursor.fetchall()

    cursor = g.conn.execute("SELECT div_name, dept_name FROM division_belongs")
    divisions = cursor.fetchall()

    dept_divisions = {}
    for division, department in divisions:
        if department not in dept_divisions:
            dept_divisions[department] = []
        dept_divisions[department].append(division)

    return render_template('signup_student.html', schools=schools, departments=departments, dept_divisions=dept_divisions)


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

        if name == '' or email == '' or password1 == '' or password2 == '' or phone_number == '' or pay_grade == '' or component == '' or job_title == '':
            return redirect(url_for('signup_staff', info="All fields are required."))

        # Validate phone number.
        phone_regex = r"^\d{3}-\d{3}-\d{4}$"
        if not re.match(phone_regex, phone_number):
            message = "Phone number must be in the format ###-###-####."
            return redirect(url_for('signup_staff', info=message))
        
        # Validate name
        if not name or not re.match(r"^[A-Za-z\s'-]{2,50}$", name):
            message = "Name must be 2-50 characters and contain only letters, spaces, apostrophes, or hyphens."
            return redirect(url_for('signup_staff', info=message))

        # Validate email
        email_regex = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
        if not email or not re.match(email_regex, email):
            message = "Please enter a valid email address."
            return redirect(url_for('signup_staff', info=message))

        # Check if passwords match
        if password1 != password2:
            return redirect(url_for('signup_staff', info="Passwords do not match."))

        # Check if email already exists
        try:
            cursor = g.conn.execute("SELECT * FROM shp2156.Staffs WHERE email = %s", (email,))
            existing_user = cursor.fetchone()
            cursor.close()
        except Exception as e:
            print(e)
            existing_user = None
        
        if existing_user:
            return redirect(url_for('signup_staff', info="Email already exists."))

        # Insert new staff record
        try:
            g.conn.execute(
                "INSERT INTO shp2156.Staffs (staff_id, name, email, password, phone_number, pay_grade, component, job_title) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                (staff_id, name, email, password1, phone_number, pay_grade, component, job_title)
            )
        except Exception as e:
            print(e)
            return redirect(url_for('signup_staff', info="Error creating staff account."))

        # Redirect to login with info message
        info_message = f"You have been assigned User ID {staff_id}. Please save your User ID and password for future logins."
        return redirect(url_for('login', info=info_message))

    info = request.args.get('info', None)
    
    return render_template('signup_staff.html')


@app.route('/create_event', methods=['GET', 'POST'])
def create_event():
    if request.method == 'POST':
        if 'user_id' not in session or session.get('user_type') != 'student':
            return redirect('/login')
    
        student_id = session['user_id']

        #assign event_id to be current max event_id + 1
        cursor = g.conn.execute("SELECT COALESCE(MAX(event_id), 0) + 1 FROM shp2156.events_created")
        event_id = cursor.fetchone()[0]
        cursor.close()
        
        title = request.form['event_title']
        location = request.form['event_location']
        date = request.form['event_date']
        event_start = request.form['event_start']
        event_end = request.form['event_end']
        max_capacity = request.form['max_capacity']
        points = request.form['points']

        if title == '' or location == '' or date == '' or event_start == '' or event_end == '' or max_capacity == '' or points == '':
            return redirect(url_for('create_event', info="All fields are required."))

        event_date = datetime.strptime(date, '%Y-%m-%d').date()
        # Check if event date is in the future
        if event_date <= datetime.now().date():
            return redirect(url_for('create_event', info="Event date must be in the future."))
        
        event_start_time = datetime.strptime(event_start, '%H:%M').time()
        event_end_time = datetime.strptime(event_end, '%H:%M').time()
        # Check if event start is before event end
        if event_start_time >= event_end_time:
            return redirect(url_for('create_event', info="Event start time must be before event end time."))

        # Insert new staff record
        try:
            g.conn.execute(
                "INSERT INTO shp2156.events_created (event_id, event_start, event_end, event_date, event_location, event_points, max_capacity, student_id, event_title) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (event_id, event_start, event_end, date, location, points, max_capacity, student_id, title)
            )
        except Exception as e:
            print(e)
            return redirect(url_for('create_event', info="Error creating event."))

        # Redirect to login with info message
        try:
            student = g.conn.execute(
                "SELECT name, total_points, program_option FROM shp2156.Student_Attends WHERE student_id = %s",
                (student_id,)
            ).fetchone()
        except Exception as e:
            print(e)
            student = None

        info_message = f"Your {title} event has been sent to the staffs for approval!"
        return redirect(url_for('student_dashboard', student=student, info=info_message))
    
    return render_template('create_event.html')

@app.route('/view_events', methods=['GET', 'POST'])
def view_events():
    if 'user_id' not in session or session.get('user_type') != 'staff':
        return redirect('/login')
    
    staff_id = session['user_id']

    # Query to get events that have not been approved
    events_query = """
        SELECT * FROM shp2156.events_created 
        WHERE event_id NOT IN (SELECT event_id FROM shp2156.approves);
    """
    events = g.conn.execute(events_query).fetchall()

    # List to store event titles that were approved or rejected for confirmation message
    approved_events = []
    rejected_events = []

    if request.method == 'POST':
        # Loop over the submitted form and check for changes
        for event in events:
            event_id = event['event_id']
            action = request.form.get(f'action_{event_id}')
            
            if action == 'approve':
                g.conn.execute(
                    """
                    INSERT INTO shp2156.approves (student_id, event_id, staff_id, event_title)
                    VALUES (%s, %s, %s, %s);
                    """, (event['student_id'], event_id, staff_id, event['event_title'])
                )
                
                approved_events.append(event['event_title'])  #to build message

            elif action == 'reject':
                # Delete the event from events_created (rejected event)
                g.conn.execute(
                    "DELETE FROM shp2156.events_created WHERE event_id = %s", (event_id,)
                )
                
                rejected_events.append(event['event_title'])  #to build message


        # Prepare the message to pass to the staff dashboard
        info_message = ""
        if approved_events:
            info_message += "You approved the following events:\n" + "\n".join(approved_events) + "\n"
        if rejected_events:
            info_message += "You rejected the following events:\n" + "\n".join(rejected_events)

        return redirect(url_for('staff_dashboard', info=info_message))

    return render_template('view_events.html', events=events)

@app.route('/invite', methods=['GET', 'POST'])
def invite():
    if 'user_id' not in session or session.get('user_type') != 'student':
        return redirect('/login')
    
    student_id = session['user_id']

    # Query to get events that have not been approved
    events_query = """
        SELECT a.student_id, a.event_id, a.staff_id, a.event_title, ec.event_start, ec.event_end, ec.event_date, ec.event_location, ec.event_points, ec.max_capacity
        FROM shp2156.approves a JOIN shp2156.events_created ec
        ON a.event_id = ec.event_id
        WHERE a.event_id NOT IN (SELECT event_id FROM shp2156.invites)
        AND a.student_id = %s;
    """
    events = g.conn.execute(events_query, (student_id,)).fetchall()

    # List to store event titles that were sent invitations for confirmation message
    invited_events = []

    if request.method == 'POST':
        # Loop over the submitted form and check for changes
        for event in events:
            event_id = event['event_id']
            divisions = request.form.getlist(f"invite_{event_id}")
            
            for division in divisions:
                department_query = """
                    SELECT dept_name
                    FROM shp2156.belongs
                    WHERE div_name = %s
                """
                department_result = g.conn.execute(department_query, (division,)).fetchone()
                department = department_result['dept_name']

                g.conn.execute(
                    """
                    INSERT INTO shp2156.invites (student_id, event_id, staff_id, div_name, dept_name, event_title)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """, 
                    (student_id, event_id, event['staff_id'], division, department, event['event_title'])
                )
                
                if event['event_title'] not in invited_events:
                    invited_events.append(event['event_title'])  #to build message

        # Prepare the message to pass to the staff dashboard
        info_message = ""
        if invited_events:
            info_message += "You sent invitations for the following events:\n" + "\n".join(invited_events) + "\n"


        return redirect(url_for('student_dashboard', info=info_message))

    return render_template('invite.html', events=events)

@app.route('/all_events')
def all_events():
    if 'user_id' not in session or session.get('user_type') != 'staff':
        return redirect('/login')

    events_query = """
        SELECT a.student_id, a.event_id, a.staff_id, a.event_title, ec.event_start, ec.event_end, ec.event_date, ec.event_location, ec.event_points, ec.max_capacity
        FROM shp2156.approves a JOIN shp2156.events_created ec
        ON a.event_id = ec.event_id
        ORDER BY ec.event_date, ec.event_start;
    """
    events = g.conn.execute(events_query).fetchall()

    participants = {}
    for event in events:
        event_id = event['event_id']
        participants_query = """
            SELECT p.student_id2, sa.name
            FROM shp2156.participates p
            JOIN shp2156.Student_Attends sa
            ON p.student_id2 = sa.student_id
            WHERE p.event_id = %s
        """
        participants[event_id] = g.conn.execute(participants_query, (event_id,)).fetchall()


    return render_template('all_events.html', events=events, participants=participants)

@app.route('/school_dept_info')
def school_dept_info():
    if 'user_id' not in session:
        return redirect('/login')

    school_query = """
        SELECT school_name, address
        FROM shp2156.schools
        ORDER BY school_name
    """
    schools = g.conn.execute(school_query).fetchall()
    
    dept_query = """
        SELECT dept_name
        FROM shp2156.departments
        ORDER BY dept_name
    """
    departments = g.conn.execute(dept_query).fetchall()

    dept_div = {}
    for dept in departments:
        dept_name = dept['dept_name']
        div_query = """
            SELECT div_name
            FROM shp2156.division_belongs
            WHERE dept_name = %s
            ORDER BY div_name
        """
        dept_div[dept_name] = g.conn.execute(div_query, (dept_name,)).fetchall()

    return render_template('school_dept_info.html', schools=schools, departments=departments, dept_div=dept_div)


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
