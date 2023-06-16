from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import os
import sys

uploadFile = str(sys.argv[1])
gauth = GoogleAuth()
gauth.LoadCredentialsFile("credentials.json")
if gauth.credentials is None:
	gauth.LocalWebserverAuth()
elif gauth.access_token_expired:
	gauth.Refresh()
else:
	gauth.Authorize()
gauth.SaveCredentialsFile("credentials.json")

drive = GoogleDrive(gauth)
filetitle = uploadFile.split("/")[-1]
# path = 'home/driscollg/Documents/pngTest'
# f = drive.CreateFile({'title': 'spider-man.png'})
# f.SetContentFile(os.path.join(path, 'spider-man.png'))
# f.Upload()

gfile = drive.CreateFile({'parents': [{'id': '1p0pY3lRDMwjC1l45dDilrAfNQbdZ6OaZ'}]})
gfile.SetContentFile(uploadFile)
gfile.Upload()
gfile['title'] = filetitle
gfile.Upload()
