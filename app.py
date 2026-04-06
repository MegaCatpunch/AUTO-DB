import json
import os

import streamlit as st
from google.oauth2.service_account import Credentials

from extractor import COLUMN_ORDER, parse_customer_info
from sheets import COLUMN_POSITIONS

st.set_page_config(page_title="고객 정보 자동 입력", page_icon="📋", layout="centered")

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def load_config():
    if "spreadsheet" in st.secrets:
        return {
            "spreadsheet_id": st.secrets["spreadsheet"]["id"],
            "sheet_name": st.secrets["spreadsheet"]["sheet_name"],
            "credentials": dict(st.secrets["gcp_service_account"]),
        }
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    return {
        "spreadsheet_id": cfg["spreadsheet_id"],
        "sheet_name": cfg["sheet_name"],
        "credentials": cfg["credentials_path"],
    }


def get_credentials(config):
    if isinstance(config["credentials"], dict):
        return Credentials.from_service_account_info(config["credentials"], scopes=SCOPES)
    return Credentials.from_service_account_file(config["credentials"], scopes=SCOPES)


st.title("📋 고객 정보 자동 입력")
st.caption("고객 정보를 붙여넣으면 구글 스프레드시트에 자동으로 입력됩니다.")

text = st.text_area(
    "고객 정보 붙여넣기",
    height=300,
    placeholder="4/3 A\n벌툰 전화\n\n성함 : 홍길동 (남)\n희망 지역 : 강남\n...\n\n> 담당자이름\n\n010-1234-5678",
)

col1, col2 = st.columns([1, 4])
parse_clicked = col1.button("파싱", use_container_width=True)
submit_clicked = col2.button("✅ 스프레드시트에 입력", use_container_width=True, type="primary")

if text and (parse_clicked or submit_clicked):
    data = parse_customer_info(text)

    st.subheader("파싱 결과")
    col_left, col_right = st.columns(2)
    items = [(k, v) for k, v in data.items() if k in COLUMN_ORDER]
    half = len(items) // 2 + len(items) % 2
    with col_left:
        for k, v in items[:half]:
            st.markdown(f"**{k}** : {v if v else '_(비어있음)_'}")
    with col_right:
        for k, v in items[half:]:
            st.markdown(f"**{k}** : {v if v else '_(비어있음)_'}")

    if submit_clicked:
        try:
            config = load_config()
            creds = get_credentials(config)

            import gspread
            client = gspread.authorize(creds)
            ws = client.open_by_key(config["spreadsheet_id"]).worksheet(config["sheet_name"])

            max_col = max(COLUMN_POSITIONS.values())
            row = [""] * max_col
            for field, col_idx in COLUMN_POSITIONS.items():
                row[col_idx - 1] = data.get(field, "")

            START_ROW = 4
            col_a = ws.col_values(1)
            last_filled = len(col_a)
            target_row = max(START_ROW, last_filled + 1)

            ws.update(f"A{target_row}", [row], value_input_option="USER_ENTERED")
            st.success(f"✅ {target_row}행에 입력 완료!")
        except Exception as e:
            st.error(f"오류: {e}")
