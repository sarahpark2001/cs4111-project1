Authors: 
Gabrielle Holley gf2501
Sarah Park shp2156

Description:

Our web server is set up to enable event planning interactions for the NYC NROTC group. 
Users can sign up or sign in as students or staff, and are then directed to the appropriate dashboard.
On the dashboard, students can view student/staff directory, create events, invite others to events, sign up for events, and logout. 
Staff can view student/staff directory, approve pending events, view all approved events and logout.

Directory Structure:

templates/ - HTML templates used for rendering pages.
server.py - Main server file with all route definitions and database interactions.

Endpoints: 

/login - Login page for both students and staff.
/logout - Logs out the user.
/signup - Redirects to signup for students or staff.
/student_dashboard - Dashboard for students to view events, RSVP, and track points.
/staff_dashboard - Dashboard for staff to view and approve/reject events.
/create_event - Enables students to create new events (pending approval by staff).
/view_events - Staff page for approving/rejecting student-created events.
/invite - Students send invitations to approved events.
/all_events - Staff view of all approved events, including participants.
/rsvp - Students can accept or reject invitations to approved events.

Changes from Earlier Stages & Explanations:

List of All Schema & How They Are Incorporated:
