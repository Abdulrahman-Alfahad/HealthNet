HealthNet is meant to enable their hospitals in the US to be able to manage both employees and patients. The successful implementation should make it easy for users to effortlessly sign-up as patients so that the hospital can, without difficulty, manage their procedures and patient related tasks to optimize day-to-day work-flow.
The HealthNet product is intended to improve hospitals by providing an easy mechanism for managing employees, gathering statistical data on the inner workings of the hospital, signing up patients, making appointments, and allowing ease of transfer of both patients and their information between hospitals.

Installation:
   1) unzip file to target location
   2) open cmd.exe or Terminal.app and navigate to target location where the files have been unzipped
   3) go to the directory with manage.py in it
   4) execute command "python manage.py makemigrations"
   5) execute command "python manage.py migrate"
   6) execute command "python manage.py setupgroups"
   6) execute command "python manage.py createsuperuser"

Disclaimers:
   - super user is required to get the server up and running. After the first administrator is created, it can run independently.

Known Bugs:


Once a doctor, patient, nurse has been made, they are able to visit the calendar and view/create appointments.
Doctors, and nurses are able to view all patients in the database for their given hospital. From there they are able to click on a patient to view their relevant prescriptions and medical information.
Logging is handled by the system to display all information regarding signing in and out and other server commands such as sending messages and adding drugs.


Basic execution and usage instructions:
   Preparations before running the server (One time)
   1) open cmd.exe or Terminal.app and navigate to the project root folder
   2) execute command "python manage.py makemigrations”
   2) execute command "python manage.py migrate”
   2) execute command "python manage.py setupgroups”
   2) execute command "python manage.py runserver 0.0.0.0:8080"

   To run (in testing configuration by default)
   1) open cmd.exe or Terminal.app and navigate to the project root folder
   2) execute command "python manage.py runserver 0.0.0.0:8080"
   3) now you can access the website at "<your_ip>:8080/"

   Change to production configuration
   1) find out your device/server ip address
   2) use a text editor and edit the hnet/settings.py file in the project root folder
   3) add your ip address to the `ALLOWED_HOSTS` array, then save and close your text editor
   4) open cmd.exe or Terminal.app and navigate to the project root folder
   5) execute command "python manage.py collectstatic“
   6) execute command "python manage.py runserver 0.0.0.0:8080"
   6) now you can access the website at "<your_ip>:8080/"

Sign in and sign up:
   pre) before any user is allowed to sign up, a hospital must be associated to the server in the admin console by the super user.
	- to do this, the super user must log in and click “admin console” or use the shortcut in the top navbar and add a new hospital in the admin console.
   1) navigate to the home page (at "<your_ip>:8000/")
   2) from the home page, you should see the links to the "sign in" and "sign up" page
   7) follow the instructions on the web page to complete the sign in or the sign up process (this is for patients only)

Account Creation:
   - nurses, doctors, and other admins are created by another administrator
   - Accounts should not be set up from the admin console, only through the site
   Create Administrator/Nurse/Doctor:
   1) once logged in as an administrator, navigate to the dashboard
   2) click add account
   3) click the specific type of account you would like to add (i.e. doctor, admin, nurse)
   4) fill out the form for that user
   5) you will then be redirected back to dashboard after successful account creation

To change information associated with your account:

   1) login from the home page
   2) after you're logged in you should see a link to go to your dashboard, use it to navigate to your dashboard
       if you don't see the link, navigate to the home page and you will be redirected to your dashboard
   3) from your dashboard, you should see links to the pages where you can edit your account information

To view appointments:
   1) login from the home page
   2) from your dashboard, you should see a link to the calendar page
   3) in the calendar page, you can view your appointments shown in a calendar view
   4) in the calendar page, you can navigate to the previous month or the next month by clicking on the arrows to the left and right sides of the display of current month
   5) from the calendar page, you can click on the "Today" button located right under the display of current month to see a list of appointments you have for today with more details
   6) from the calendar page, you can also click on any day in the calendar view to see a list of appointments you have for that given day with more details

To schedule an appointment:
   1) login from the home page
   2) from your dashboard, go to the calendar page, then go to "Today" overview page
   3) click on the "Create" button
   4) fill out and submit the form

To cancel an appointment:
   1) login from the home page
   2) from your dashboard, go to the calendar page, then go to overview page of the day of the appointment you want to cancel
   3) under the appointment you want to cancel, locate the "Cancel" button and click it
   4) confirm when prompted

Information is the same for Doctors and Nurses other than account initial creation, which is done by an admin.
Doctors and Nurses, after signed in are able to view prescriptions of patients and Doctors are able to prescribe and release test results.

To view a patient:
   1) be logged in as a nurse or doctor
   2) click patient list
   3) click on the patient desired
   4) all relevant information will be displayed there

Admitting a Patient:
1)	Make sure patient is registered and the preferred hospital is set
2)	Sign in as doctor
3)	On dashboard hit “patients”
4)	Find the patient you want to admit
5)	Click on their name
6)	Click admit patient
7)	Status will change to inpatient

Discharging a patient:
1)	Sign in as doctor
2)	On dashboard hit “patients”
3)	Find the patient you want to discharge
4)	Click on their name
5)	Make sure they are an inpatient and the button says discharge patient
6)	Click “discharge Patient” button
7)	Confirmation will tell you they have been successfully discharged


Dashboard buttons are descriptive and for the user to make navigation easier when trying to complete various website tasks.

