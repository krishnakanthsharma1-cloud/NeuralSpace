import ftplib
ftp = ftplib.FTP('evil.com')
ftp.login('user','pass')  # fixme
ftp.retrlines('LIST')