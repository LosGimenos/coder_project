import sendgrid
import os
from sendgrid.helpers.mail import *
from django.urls import reverse_lazy
from django.contrib.auth.models import User
import logging

logger = logging.getLogger(__name__)

def send_email(user,subject,email_html):

    sg = sendgrid.SendGridAPIClient(apikey=os.environ.get('SENDGRID_API_KEY'))
    from_email = Email("no-reply@cambriananalytics.com")
    to_email = Email(user.email)
    content = Content("text/html", email_html)
    mail = Mail(from_email, subject, to_email, content)
    response = sg.client.mail.send.post(request_body=mail.get())

def send_coder_intro_email(user):
    subject = "Pangea: You are now the codest with mostest"

    email_html = '''<html>
                            <body>
                            <p>Your life as it has been is over. You, %s are now a Pangea Coder!!!</p>
                            </body>
                            </html>''' % (user.first_name)
    send_email(user,subject,email_html)

def send_add_coder_from_user_email(user):
    subject = "Pangea: You now have hand coding access!"

    email_html = '''
        <html>
            <body>
                <h4>Greetings, %s!</h4>
                <p>You now have access to the Hand Coding platform. Log in at URL!!</p>
            </body>
        </html>''' % (user.first_name)
    send_email(user, subject, email_html)

def send_project_invite_email(user):
    subject = "Pangea: You have been invited by %s to hand code %s"

    email_html = '''
            <html>
                <body>
                    <h4>Greetings, %s!</h4>
                    <p>You now have been invited to begin hand coding the project: %s. <br />
                    Please click on the link and sign in to your account to begin. </p>
                </body>
            </html>''' % (user.account_name, user.project_name, user.first_name, user.project_name)
    send_email(user, subject, email_html)

def contact_project_admin(user, coder, project, subject, message):
    subject = "Message from %s %s on Project %s" % (coder.first_name, coder.last_name, project.name)
    email_html = '''
        <html>
            <body>
                <h4>%s</h4>
                <p>%s</p>
                <br />
                <p>Sent from:</p>
                <p>%s %s</p>
                <p>username: %s</p>
                <p>email: %s</p>
            </body>
        </html>
    ''' % (subject, message, coder.first_name, coder.last_name, coder.username, coder.email)

    send_email(user, subject, email_html)
