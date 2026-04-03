# AUTO-DB Windows 설치 스크립트
# PowerShell 관리자 권한으로 실행하세요

$TARGET = "C:\AUTO-DB"

# 폴더 생성
if (-Not (Test-Path $TARGET)) {
    New-Item -ItemType Directory -Path $TARGET | Out-Null
    Write-Host "[완료] 폴더 생성: $TARGET"
} else {
    Write-Host "[확인] 폴더 이미 존재: $TARGET"
}

# extractor.py
@'
import re
from datetime import date


COLUMN_ORDER = ['구분', '유형', '접수월', '접수일', '배정일', '이름', '희망지역', '연락처', '최종담당', '첫메모', 'A급 DB']


def parse_customer_info(text: str) -> dict:
    result = {col: '' for col in COLUMN_ORDER}
    result['배정일'] = _today()

    lines = [line.strip() for line in text.strip().split('\n')]
    non_empty = [l for l in lines if l]

    if non_empty:
        m = re.match(r'^(\d{1,2})/(\d{1,2})$', non_empty[0])
        if m:
            result['접수월'] = m.group(1)
            result['접수일'] = non_empty[0]

    if len(non_empty) > 1:
        parts = non_empty[1].split()
        if len(parts) >= 1:
            result['구분'] = parts[0]
        if len(parts) >= 2:
            result['유형'] = parts[1]

    if re.search(r'\bA\b', text):
        result['A급 DB'] = 'O'

    m = re.search(r'성함\s*:\s*(.+)', text)
    if m:
        name = m.group(1).strip()
        result['이름'] = re.sub(r'\s*\([남녀]\)', '', name).strip()

    m = re.search(r'희망\s*지역\s*:\s*(.+)', text)
    if m:
        result['희망지역'] = m.group(1).strip().replace(' ', '')

    m = re.search(r'>\s*(.+)', text)
    if m:
        result['최종담당'] = m.group(1).strip()

    m = re.search(r'(0\d{1,2}[-\s]?\d{3,4}[-\s]?\d{4})', text)
    if m:
        result['연락처'] = m.group(1).strip()

    memo_parts = []
    m = re.search(r'현재\s*직업\s*:\s*(.+)', text)
    if m:
        memo_parts.append(f'직업: {m.group(1).strip()}')
    m = re.search(r'방문\s*경험\s*:\s*(.+)', text)
    if m:
        memo_parts.append(f'방문경험: {m.group(1).strip()}')
    m = re.search(r'창업\s*자금\s*:\s*(.+)', text)
    if m:
        memo_parts.append(f'창업자금: {m.group(1).strip()}')
    result['첫메모'] = ' / '.join(memo_parts)

    return result


def _today() -> str:
    today = date.today()
    return f'{today.month}/{today.day}'
'@ | Set-Content "$TARGET\extractor.py" -Encoding UTF8
Write-Host "[완료] extractor.py"

# sheets.py
@'
import gspread
from google.oauth2.service_account import Credentials

from extractor import COLUMN_ORDER

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive',
]


def append_customer(data: dict, spreadsheet_id: str, sheet_name: str, credentials_path: str) -> None:
    creds = Credentials.from_service_account_file(credentials_path, scopes=SCOPES)
    client = gspread.authorize(creds)
    ws = client.open_by_key(spreadsheet_id).worksheet(sheet_name)
    row = [data.get(col, '') for col in COLUMN_ORDER]
    ws.append_row(row, value_input_option='USER_ENTERED')
'@ | Set-Content "$TARGET\sheets.py" -Encoding UTF8
Write-Host "[완료] sheets.py"

# main.py
@'
import json
import os
import sys

from extractor import COLUMN_ORDER, parse_customer_info
from sheets import append_customer

CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config.json')


def load_config():
    if not os.path.exists(CONFIG_FILE):
        print(f"[오류] config.json 파일이 없습니다.")
        sys.exit(1)
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def read_paste():
    print("고객 정보를 붙여넣고 빈 줄에서 Enter를 두 번 누르세요:\n")
    lines = []
    blank_count = 0
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line == '':
            blank_count += 1
            if blank_count >= 2:
                break
            lines.append(line)
        else:
            blank_count = 0
            lines.append(line)
    return '\n'.join(lines).strip()


def print_preview(data):
    print("\n" + "=" * 45)
    print("  파싱 결과 미리보기")
    print("=" * 45)
    for col in COLUMN_ORDER:
        print(f"  {col:<10}: {data.get(col, '')}")
    print("=" * 45)


def main():
    print("=" * 45)
    print("   고객 정보 자동 입력 프로그램")
    print("=" * 45 + "\n")

    config = load_config()

    while True:
        text = read_paste()
        if not text:
            print("[경고] 입력된 내용이 없습니다.\n")
            continue

        data = parse_customer_info(text)
        print_preview(data)

        while True:
            answer = input("\n스프레드시트에 입력하시겠습니까? (y: 입력 / n: 취소 / r: 다시 붙여넣기): ").strip().lower()
            if answer in ('y', 'n', 'r'):
                break

        if answer == 'y':
            try:
                append_customer(data, config['spreadsheet_id'], config['sheet_name'], config['credentials_path'])
                print("\n[완료] 스프레드시트에 입력되었습니다!\n")
            except Exception as e:
                print(f"\n[오류] 입력 실패: {e}\n")
        elif answer == 'r':
            print()
            continue
        else:
            print("\n[취소]\n")

        again = input("계속 입력하시겠습니까? (y/n): ").strip().lower()
        if again != 'y':
            print("\n프로그램을 종료합니다.")
            break
        print()


if __name__ == '__main__':
    main()
'@ | Set-Content "$TARGET\main.py" -Encoding UTF8
Write-Host "[완료] main.py"

# config.json
@'
{
  "spreadsheet_id": "1RHbWmA4uf16REOgyXphXOJ5jHyE3ryPmrgy3XHnDDcM",
  "sheet_name": "통합DB",
  "credentials_path": "C:\\AUTO-DB\\credentials.json"
}
'@ | Set-Content "$TARGET\config.json" -Encoding UTF8
Write-Host "[완료] config.json"

# requirements.txt
@'
gspread==6.1.2
google-auth==2.29.0
'@ | Set-Content "$TARGET\requirements.txt" -Encoding UTF8
Write-Host "[완료] requirements.txt"

Write-Host ""
Write-Host "======================================="
Write-Host "  설치 완료!"
Write-Host "======================================="
Write-Host ""
Write-Host "다음 단계:"
Write-Host "1. credentials.json 을 C:\AUTO-DB\ 에 복사"
Write-Host "2. 아래 명령어 실행:"
Write-Host "   pip install -r C:\AUTO-DB\requirements.txt"
Write-Host "   python C:\AUTO-DB\main.py"
