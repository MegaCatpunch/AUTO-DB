#!/usr/bin/env python3
"""
고객 정보 자동 입력 프로그램
고객 정보 텍스트를 붙여넣으면 파싱하여 구글 스프레드시트에 자동으로 입력합니다.
"""

import json
import os
import sys

from extractor import COLUMN_ORDER, parse_customer_info
from sheets import append_customer

CONFIG_FILE = 'config.json'


def load_config() -> dict:
    if not os.path.exists(CONFIG_FILE):
        print(f"[오류] '{CONFIG_FILE}' 파일이 없습니다.")
        print("       'config.json.example'을 복사하여 config.json을 만들고 설정을 입력해주세요.")
        sys.exit(1)
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def read_paste() -> str:
    """사용자가 붙여넣은 텍스트를 읽습니다. 빈 줄 두 번 입력 시 종료."""
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


def print_preview(data: dict) -> None:
    print("\n" + "=" * 45)
    print("  파싱 결과 미리보기")
    print("=" * 45)
    for col in COLUMN_ORDER:
        value = data.get(col, '')
        print(f"  {col:<10}: {value}")
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
            print("y, n, r 중 하나를 입력해주세요.")

        if answer == 'y':
            try:
                append_customer(
                    data,
                    config['spreadsheet_id'],
                    config['sheet_name'],
                    config['credentials_path'],
                )
                print("\n[완료] 스프레드시트에 입력되었습니다!\n")
            except Exception as e:
                print(f"\n[오류] 입력 실패: {e}\n")
        elif answer == 'r':
            print()
            continue
        else:
            print("\n[취소] 입력하지 않았습니다.\n")

        again = input("계속 입력하시겠습니까? (y/n): ").strip().lower()
        if again != 'y':
            print("\n프로그램을 종료합니다.")
            break
        print()


if __name__ == '__main__':
    main()
