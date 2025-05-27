import gspread
from google.oauth2.service_account import Credentials

# Konfigurasi spreadsheet
SHEET_ID = "1JLb5wzQL5yT-8joGw53Wc_rDlzO1TaJeZDWCLtB1DoY"
WORKSHEET_NAME = "Sheet1"
CRED_PATH = "aldzama-dashboard-hidrolis-415739989ae4.json"  # Sesuaikan path lokal kamu

# Setup kredensial Google API
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_file(CRED_PATH, scopes=scope)
client = gspread.authorize(creds)

# Buka Google Sheet
sheet = client.open_by_key(SHEET_ID)
worksheet = sheet.worksheet(WORKSHEET_NAME)

# Baca header
headers = worksheet.row_values(1)

# Kolom baru yang ingin ditambahkan
new_columns = ["Requested By", "Request Date"]

# Tambahkan jika belum ada
for col in new_columns:
    if col not in headers:
        headers.append(col)

# Update baris pertama (header)
worksheet.update("A1", [headers])

print("✅ Header berhasil diperbarui:", headers)
