import smtplib, sys, os
from email.mime.text import MIMEText
from email.header    import Header

def send_update():
    clean_lines = []
    with open(sys.argv[2], 'r') as out_file:
    	lines = out_file.readlines()
	clean_lines = [l.strip() for l in lines if l.strip()]
    
    smtp_host = 'smtp.gmail.com'       # google
    login, password = "INSERT YOUR EMAIL ADDR", "INSERT PSSWD" #FIX ME
    recipients_emails = "INSERT EMAIL ADDR" #FIX ME

    body = ('{}'.format("".join((lines))))
    msg = MIMEText(body, 'plain', 'utf-8')
    msg['Subject'] = Header('Labware sample and customer updates', 'utf-8')
    msg['From'] = login
    msg['To'] = ", ".join(recipients_emails)
    s = smtplib.SMTP(smtp_host, 587, timeout=10)
    s.set_debuglevel(1)
    try:
        s.starttls()
	s.login(login, password)
	s.sendmail(msg['From'], recipients_emails, msg.as_string())
    finally:
        s.quit()

	
def send_failure():
    clean_lines = []
    with open(sys.argv[1], 'r') as error_file:
        lines = error_file.readlines()
        clean_lines = [l.strip() for l in lines if l.strip()]

    smtp_host = 'smtp.gmail.com'       # google
    login, password = "INSERT YOUR EMAIL ADDR", "INSERT PSSWD" #FIX ME
    recipients_emails = "INSERT EMAIL ADDR" #FIX ME   
 
    body = ("The program running to update labware sample and customer tables has failed. \n" +
		"Please investigate issue further.Error message below.\n\n" +
		"\n".join(clean_lines))

    msg = MIMEText(body, 'plain', 'utf-8')
    msg['Subject'] = Header('PROGRAM FAILURE:labware data migration (production)', 'utf-8')
    msg['From'] = login
    msg['To'] = ", ".join(recipients_emails)
    
    s = smtplib.SMTP(smtp_host, 587, timeout=10)
    s.set_debuglevel(1)
    try:
    	s.starttls()
	s.login(login, password)
	s.sendmail(msg['From'], recipients_emails, msg.as_string())
    finally:
        s.quit()

def main():
    if os.stat(sys.argv[1]).st_size == 0:
    	print ("there")
	send_update()
	
    else:
    	print ("here")
    	send_failure()

main()
