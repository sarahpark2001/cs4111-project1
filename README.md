# Columbia W4111 Intro to Databases: Project 1, Part 3

This repository contains a sample web server setup for managing event planning interactions for the NYC NROTC group. The server is based on a PostgreSQL database and uses Flask as the web framework with SQLAlchemy for database interactions.

## Authors
- Gabrielle Holley - `gf2501`
- Sarah Park - `shp2156`

## Description
Our web server enables event planning interactions for the NYC NROTC group. Users can sign up or sign in as students or staff and are directed to the appropriate dashboard. 

- **Students**: View the student/staff directory, create events, invite others to events, RSVP for future events, and log out.
- **Staff**: View the student/staff directory, approve pending events, view all approved events, and log out.

## Directory Structure
- **templates/** - HTML templates used for rendering pages.
- **server.py** - Main server file with all route definitions and database interactions.

## Endpoints
- **/login** - Login page for both students and staff. Can choose which user type to login as.
- **/logout** - Logs out the user.
- **/signup** - Redirects to signup pages for students or staff.
- **/signup_student** - Form to add new student to Student_Attends table.
- **/signup_staff** - Form to add new staff to Staffs table.
- **/student_dashboard** - Dashboard for students to see the directory, view events, RSVP, and track points.
- **/staff_dashboard** - Dashboard for staff to see the directory as well as view and approve/reject events.
- **/create_event** - Enables students to create new events (pending approval by staff).
- **/view_events** - Staff page for approving/rejecting student-created events.
- **/invite** - Students who created the event can send invitations to approved events.
- **/all_events** - Staff view history of all approved events, including participants.
- **/rsvp** - Students can accept or decline invitations to approved events and sign up for all other approved events.

## Changes from Earlier Stages & Explanations
In our Part 1 Proposal, we briefly mentioned a functionality where students could edit the account details of other students. This doesn't make sense with how we implemented the app and our app's use-case. We used unique logins so that everyone is accessing only their own accounts and using those accounts to create events, signup for events, and invite others to events. This functionality was not in our ER diagram or schema (it was something we had considered for our app implementation), so we did not have to make any changes in order to exclude implementation.

We added the event_title (text) attribute to Events_Created, Participates, Approves, and Invites and added it to the keys of the tables too. This helped us to better display events in the web app. Although the unique event_id is sufficient for the database to differentiate, we wanted students and staff to see more information so they could make a decision on approval or attendance. 

We also added many more details into our implementation than we initially outlined. For instance, when the student signs up, their default total_points will be 0. We added functionality to auto-assign staff_id and student_id as +1 from the current highest value to make sure they are unique. We added regex checks on names, phone numbers and emails to make sure that we aren't storing junk data. We added a dictionary which corresponds military paygrades and service components to formal titles so that the users are greeted appropriately upon login. Additionally, we added the constraint in our Events_Created table so that we check if the event_date is in the future (event_date > CURRENT_DATE). This is so that students are not creating events in the future. Note, that this is in UTC time. We also made sure that students can only RSVP to events in the future so that students can't earn points from past events. 

## List of All Schema & How They Are Incorporated
| Table Name         | Attributes (Type)                                                                                                                                                            | Description                                                                                                                                                                                      |
|--------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| approves           | student_id (integer), event_id (integer), staff_id (integer), event_title (text)                                                                                            | Contains events that staff members have approved. The contents of this table are visible on the RSVP page for students and visible in the View All Events page for staff.                                 |
| belongs            | student_id (integer), div_name (text), dept_name (text)                                                                                                                     | Records which students are in which divisions and departments. Viewable on the directory page and used when issuing invitations to created events.         |
| departments        | dept_name (text)                                                                                                                                                             | Stores all departments. Used in the same implementations as `belongs` and during student sign-up.                                                         |
| division_belongs   | div_name (text), dept_name (text)                                                                                                                                           | Stores all divisions and their associated departments. Used during student sign-up.                                                                       |
| events_created     | event_id (integer), event_start (time), event_end (time), event_date (date), event_location (text), event_points (integer), max_capacity (integer), student_id (integer), event_title (text) | Shows all student-proposed events that are pending or approved. Viewable by staff to make approval decisions.        |
| invites            | student_id (integer), event_id (integer), staff_id (integer), div_name (text), dept_name (text), event_title (text)                                                        | Students who created an event can issue invitations to students in a specific division, displayed on the recipients' RSVP page.                           |
| participates       | student_id (integer), event_id (integer), staff_id (integer), student_id2 (integer), event_title (text)                                                                     | Keeps track of all RSVP entries as unique (student_id, event_id) pairs, used to allocate participation points.                                                      |
| schools            | school_name (text), address (text)                                                                                                                                           | Contains all NYC NROTC schools. Used in student sign-up and in the directory.                                                                             |
| staffs             | staff_id (integer), email (text), name (text), phone_number (text), pay_grade (text), component (text), job_title (text), password (text)                                   | Contains all staff members; used for staff login and directory. Entries can be added via staff sign-up.                                                   |
| student_attends    | student_id (integer), email (text), name (text), program_option (text), total_points (integer), year (integer), school_name (text), password (text)                        | Contains all students; used for student login and directory. Entries can be added via student sign-up.                                                    |
