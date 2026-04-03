import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive',
]

# 각 항목의 열 위치 (A=1, B=2, ... V=22, Z=26)
COLUMN_POSITIONS = {
    '구분':     1,   # A
    '유형':     2,   # B
    '접수월':   3,   # C
    '접수일':   4,   # D
    '배정일':   5,   # E
    '이름':     6,   # F
    '희망지역': 7,   # G
    '연락처':   8,   # H
    '최종담당': 9,   # I
    '첫메모':   22,  # V
    'A급 DB':  26,  # Z
}


def append_customer(data: dict, spreadsheet_id: str, sheet_name: str, credentials_path: str) -> None:
    creds = Credentials.from_service_account_file(credentials_path, scopes=SCOPES)
    client = gspread.authorize(creds)
    ws = client.open_by_key(spreadsheet_id).worksheet(sheet_name)

    max_col = max(COLUMN_POSITIONS.values())
    row = [''] * max_col
    for field, col_idx in COLUMN_POSITIONS.items():
        row[col_idx - 1] = data.get(field, '')

    ws.append_row(row, value_input_option='USER_ENTERED')
