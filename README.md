# Columbia W4111 Intro to Databases: Example Webserver

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
- **/student_dashboard** - Dashboard for students to view events, RSVP, and track points.
- **/staff_dashboard** - Dashboard for staff to view and approve/reject events.
- **/create_event** - Enables students to create new events (pending approval by staff).
- **/view_events** - Staff page for approving/rejecting student-created events.
- **/invite** - Students can send invitations to approved events.
- **/all_events** - Staff view of all approved events, including participants.
- **/rsvp** - Students can accept or decline invitations to approved events.

## Changes from Earlier Stages & Explanations
*List any changes made from earlier project stages here and provide brief explanations.*

## List of All Schema & How They Are Incorporated
*Include a list of the database schema along with explanations of how each table or entity is used in the application.*

