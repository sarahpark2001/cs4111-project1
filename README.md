# Columbia W4111 Intro to Databases: Project 1, Part 3

This repository contains a sample web server setup for managing event planning interactions for the NYC NROTC group. The server is based on a PostgreSQL database and uses Flask as the web framework with SQLAlchemy for database interactions.

## Authors
- Gabrielle Holley - `gf2501`
- Sarah Park - `shp2156`

## Description
Our web server enables event planning interactions for the NYC NROTC group. Users can sign up or sign in as students or staff and are directed to the appropriate dashboard. 

- **Students**: View the student/staff directory, create events, invite others to events, RSVP for events, and log out.
- **Staff**: View the student/staff directory, approve pending events, view all approved events, and log out.

## Directory Structure
- **templates/** - HTML templates used for rendering pages.
- **server.py** - Main server file with all route definitions and database interactions.

## Endpoints
- **/login** - Login page for both students and staff.
- **/logout** - Logs out the user.
- **/signup** - Redirects to signup pages for students or staff.
- **/signup_student** - Form to add new student to Student_Attends table.
- **/signup_staff** - Form to add new staff to Staffs table.
- **/student_dashboard** - Dashboard for students to view events, RSVP, and track points.
- **/staff_dashboard** - Dashboard for staff to view and approve/reject events.
- **/create_event** - Enables students to create new events (pending approval by staff).
- **/view_events** - Staff page for approving/rejecting student-created events.
- **/invite** - Students can send invitations to approved events.
- **/all_events** - Staff view of all approved events, including participants.
- **/rsvp** - Students can accept or decline invitations to approved events.

## Changes from Earlier Stages & Explanations
In our Part 1 Proposal, we briefly mentioned a functionality where students could edit the account details of other students. This doesn't make sense with how we implemented the app. We used unique logins so that everyone is accessing only their own accounts and using those accounts to create events, signup for events, and invite others to events. This functionality was not in our ER diagram or schema (it was something we had considered for our app implementation), so we did not have to make any changes in order to exclude implementation.

We added the event_title (text) attribute to Events_Created, Participates, Approves, and Invites. This helped us to better display events in the web app. Although the unique event_id is sufficient for the database to differentiate, we wanted students and staff to see more information so they could make a decision on approval or attendance. 

## List of All Schema & How They Are Incorporated
*Include a list of the database schema along with explanations of how each table or entity is used in the application.*

