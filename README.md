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
- **/login** - Login page for both students and staff. Can choose which user type to login as. Contains links to signup pages.
- **/logout** - Logs out the user. Redirects to login page.
- **/signup** - Redirects to signup pages for students or staff based on form submission from \login page.
- **/signup_student** - Form to add new student to Student_Attends table as well as add them to the appropriate division & department in the `belongs` table.
- **/signup_staff** - Form to add new staff to Staffs table.
- **/student_dashboard** - Dashboard for students to see the directory, view events, RSVP, and track points.
- **/staff_dashboard** - Dashboard for staff to see the directory as well as view and approve/reject events.
- **/create_event** - Enables students to create new events (pending approval by staff).
- **/view_events** - Staff page for approving/rejecting student-created events.
- **/invite** - Students who created the event can send invitations to approved events.
- **/all_events** - Staff view history of all approved events, including participants.
- **/rsvp** - Students can accept or decline invitations to approved events and sign up for all other approved events.
- **/edit_student** - Students can edit the data attached to their student_id in the `student_attends` and `belongs` tables.
- **/edit_staff** - Staff can edit the data attached to their staff_id in the Staffs table.
- **/manage_student** - Staff can look up a student by student_id to manage that student's record, with options to modify or delete the student.
- **/manage_student_action** - Handles the action selected in `/manage_student` (either modify or delete), and routes the user accordingly.
- **/manage_student_modify** - Allows staff to modify student information, similar to `/edit_student` but with administrative permissions.
- **/confirm_delete_student** - Separate page for staff to confirm deletion of a student after choosing the delete option, displaying a final confirmation prompt for the action.


## Changes from Earlier Stages & Explanations

In Part 1, we proposed a functionality where students could edit and delete other student accounts. However, during the development process, we realized that this approach would have conflicted with our app’s permissions structure and use-case. In our implementation, each student can access only their own account to create events, sign up for events, and send invitations. Students' access to other users' data is read-only, in the form of a directory. Instead, we implemented a feature where staff can modify or delete student records, which better aligns with the app’s permissions model.

To support this feature, we modified the foreign key constraint on the `Belongs` and `Participates` tables to include `ON DELETE CASCADE`. This adjustment allows related entries in these tables to be automatically removed when a corresponding student record is deleted from `Student_Attends.` This update facilitates the staff's ability to delete student records without triggering foreign key violations, enhancing data integrity across the application. 

Additionally, we added an `event_title` attribute (text) to the `Events_Created`, `Participates`, `Approves`, and `Invites` tables, incorporating it into the keys of these tables. While the unique `event_id` is sufficient for database management, `event_title` provides more contextual information for students and staff when deciding on event approvals and attendance, improving the user experience in the web app.

Beyond these schema changes, we expanded our implementation with many other new details. For instance, a new student’s default `total_points` is set to 0 upon signup. We added functionality to auto-assign `staff_id` and `student_id` as one higher than the current highest value to ensure uniqueness. To maintain data integrity, we implemented regex checks for names, phone numbers, and emails to prevent junk data from being stored. 

We also introduced a dictionary mapping military pay grades and service components to formal titles so that users are greeted appropriately upon login. Additionally, we added a constraint in the `Events_Created` table to verify that `event_date` is in the future (`event_date > CURRENT_DATE`), ensuring that students cannot create events in the past. This date constraint follows UTC time. Finally, we restricted RSVP functionality to future events only, preventing students from earning points from past events.

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
