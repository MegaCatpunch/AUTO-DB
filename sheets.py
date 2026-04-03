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
    'J열':     10,  # J
    'N열':     14,  # N
    'Q열':     17,  # Q
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

    # A열(구분) 기준으로 마지막 데이터 행 찾기 (서식만 있는 빈 셀 무시)
    START_ROW = 4
    col_a = ws.col_values(1)  # 실제 값이 있는 셀만 반환
    last_filled = len(col_a)
    target_row = max(START_ROW, last_filled + 1)

    ws.update(f'A{target_row}', [row], value_input_option='USER_ENTERED')
