def main(modelname, chival):
    import gspread
    from pydrive.auth import GoogleAuth
    from pydrive.drive import GoogleDrive
    from google.oauth2.service_account import Credentials

    scopes = ['https://www.googleapis.com/auth/spreadsheets',
              'https://www.googleapis.com/auth/drive']
    credentials = Credentials.from_service_account_file('client_key.json', scopes=scopes)

    gc = gspread.authorize(credentials)

    gauth = GoogleAuth()
    drive = GoogleDrive(gauth)

    gs = gc.open_by_key('13k9iSe1oqnPqmU8Ks94cZMo9qkb1QggQ_9BuOZla8Xc')

    results = gs.worksheet('Results')

    vals = [[modelname, chival]]
    gs.values_append('Results', {'valueInputOption': 'RAW'}, {'values': vals})
