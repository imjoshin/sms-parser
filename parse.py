import config
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def main():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
    gc = gspread.authorize(credentials)
    sh = gc.open_by_key(config.SHEET)

    wsSent = sh.worksheet("Sent")
    wsRec = sh.worksheet("Received")

    sentHeaders = wsSent.row_values(1)
    recHeaders = wsRec.row_values(1)

    print dict(zip(sentHeaders, wsSent.row_values(2)))

if __name__ == "__main__":
	main()
