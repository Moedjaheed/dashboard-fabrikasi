
import gspread
from gspread_dataframe import get_as_dataframe, set_with_dataframe
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

# Fungsi autentikasi dan pembacaan dari Google Sheets
def load_gsheet(sheet_id, worksheet_name, cred_path="aldzama-dashboard-hidrolis-415739989ae4.json"):
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(cred_path, scope)
    client = gspread.authorize(creds)
    worksheet = client.open_by_key(sheet_id).worksheet(worksheet_name)
    df = get_as_dataframe(worksheet).dropna(how='all')
    return df, worksheet

# Fungsi menyimpan ke Google Sheets
def update_gsheet(worksheet, dataframe):
    worksheet.clear()
    set_with_dataframe(worksheet, dataframe)
