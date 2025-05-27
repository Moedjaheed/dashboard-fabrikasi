import gspread
import json
import pandas as pd
import streamlit as st
from gspread_dataframe import get_as_dataframe, set_with_dataframe
from oauth2client.service_account import ServiceAccountCredentials

# Fungsi autentikasi dan pembacaan dari Google Sheets
def load_gsheet(sheet_id, worksheet_name):
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds_dict = json.loads(st.secrets["gcp_service_account"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    worksheet = client.open_by_key(sheet_id).worksheet(worksheet_name)
    df = get_as_dataframe(worksheet).dropna(how='all')
    return df, worksheet

# Fungsi menyimpan ke Google Sheets
def update_gsheet(worksheet, dataframe):
    worksheet.clear()
    set_with_dataframe(worksheet, dataframe)
