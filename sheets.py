import gspread
from google.oauth2.service_account import Credentials

from extractor import COLUMN_ORDER

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive',
]


def get_worksheet(spreadsheet_id: str, sheet_name: str, credentials_path: str):
    creds = Credentials.from_service_account_file(credentials_path, scopes=SCOPES)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(spreadsheet_id)
    return spreadsheet.worksheet(sheet_name)


def append_customer(data: dict, spreadsheet_id: str, sheet_name: str, credentials_path: str) -> None:
    """파싱된 고객 데이터를 스프레드시트에 한 행으로 추가합니다."""
    ws = get_worksheet(spreadsheet_id, sheet_name, credentials_path)
    row = [data.get(col, '') for col in COLUMN_ORDER]
    ws.append_row(row, value_input_option='USER_ENTERED')
