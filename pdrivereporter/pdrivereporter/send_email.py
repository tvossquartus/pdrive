from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib


host = 'smtp.gmail.com'
port = 587
email_address = 'feistyelephant123@gmail.com'
password = 'vr,Gq8=H-R{cp5?L'
recip = 'asarves1@gmail.com'

content = "This is a test. Email sent from python."
link = "P:\QUARTUS\Voss\Pdrive\pdrivereporter\pdrivereporter"


class send_email():

    def __init__(self,send_from,send_to,stuff):
                    
        self.sender = send_from
        self.recipient = send_to
        self.password = input("Please enter your password")
        self.message = stuff
        
        msg = MIMEMultipart('alternative')
        msg['FROM'] = self.sender
        msg['TO'] = self.recipient
        msg['Subject'] = 'Test Email'
    
        message_html = MIMEText(self.message,'html')
        msg.attach(message_html)

        print(msg.as_string())
    
        try:
            server = smtplib.SMTP('smtp.gmail.com',587)
            server.ehlo()   
            server.starttls()
            server.login(self.sender,self.password)
            server.sendmail(self.sender,self.recipient,msg.as_string())
            server.quit
            print("Success! Email sent!")
        except:
            print("Email failed to send.")

body = content + '\r' + '<a href=' + '"'+ link + '"</a>'
trythis = send_email(email_address,recip,body)

     


#

#
