import re
from datetime import date


COLUMN_ORDER = ['구분', '유형', '접수월', '접수일', '배정일', '이름', '희망지역', '연락처', '최종담당', '첫메모', 'A급 DB']


def parse_customer_info(text: str) -> dict:
    """
    고객 정보 텍스트를 파싱하여 스프레드시트 컬럼에 맞는 딕셔너리로 반환합니다.

    예시 입력:
        4/2
        벌툰 일반

        성함 : 임태형(남)
        희망 지역 : 경기 동두천시
        방문 경험 : 없음
        현재 직업 : 목수
        창업 자금 : 미공개
        창업 시기 : 미정

        > 신현준

        010-2683-9503
    """
    result = {col: '' for col in COLUMN_ORDER}
    result['배정일'] = _today()

    lines = [line.strip() for line in text.strip().split('\n')]
    non_empty = [l for l in lines if l]

    # --- 접수월 / 접수일: 첫 줄 "M/D" 형식 ---
    if non_empty:
        m = re.match(r'^(\d{1,2})/(\d{1,2})$', non_empty[0])
        if m:
            result['접수월'] = m.group(1)
            result['접수일'] = m.group(2)

    # --- 구분 / 유형: 두 번째 줄 "구분 유형" 형식 ---
    if len(non_empty) > 1:
        parts = non_empty[1].split()
        if len(parts) >= 1:
            result['구분'] = parts[0]
        if len(parts) >= 2:
            result['유형'] = parts[1]
            # 유형에 "A" 포함 시 A급 DB 체크
            if _is_grade_a(parts[1]):
                result['A급 DB'] = 'O'

    # --- 이름 (성함) ---
    m = re.search(r'성함\s*:\s*(.+)', text)
    if m:
        result['이름'] = m.group(1).strip()

    # --- 희망지역 ---
    m = re.search(r'희망\s*지역\s*:\s*(.+)', text)
    if m:
        result['희망지역'] = m.group(1).strip()

    # --- 최종담당: ">" 다음에 오는 이름 ---
    m = re.search(r'>\s*(.+)', text)
    if m:
        result['최종담당'] = m.group(1).strip()

    # --- 연락처: 전화번호 패턴 ---
    m = re.search(r'(0\d{1,2}[-\s]?\d{3,4}[-\s]?\d{4})', text)
    if m:
        result['연락처'] = m.group(1).strip()

    # --- 첫메모: 직업 / 방문경험 / 창업자금 ---
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
    """오늘 날짜를 M/D 형식으로 반환합니다."""
    today = date.today()
    return f'{today.month}/{today.day}'


def _is_grade_a(type_str: str) -> bool:
    """유형 문자열이 A급인지 확인합니다. (예: 'A', 'A급', 'a급')"""
    return bool(re.search(r'\bA급?\b', type_str, re.IGNORECASE))
