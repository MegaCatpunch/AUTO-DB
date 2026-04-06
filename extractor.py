import re
from datetime import date


COLUMN_ORDER = ['구분', '유형', '접수월', '접수일', '배정일', '이름', '희망지역', '연락처', '최종담당', 'J열', 'N열', 'Q열', '첫메모', 'A급 DB']


def parse_customer_info(text: str) -> dict:
    result = {col: '' for col in COLUMN_ORDER}
    result['배정일'] = _today()

    lines = [line.strip() for line in text.strip().split('\n')]
    non_empty = [l for l in lines if l]

    # --- 접수월 / 접수일: 첫 줄에서 "M/D" 추출 ---
    if non_empty:
        m = re.match(r'^(\d{1,2})/(\d{1,2})', non_empty[0])
        if m:
            result['접수월'] = m.group(1)
            result['접수일'] = f'{m.group(1)}/{m.group(2)}'

    # --- 구분 / 유형: 날짜가 없는 첫 번째 줄에서 추출 ---
    for line in non_empty:
        if not re.match(r'^\d{1,2}/\d{1,2}', line):
            parts = line.split()
            if len(parts) >= 1:
                result['구분'] = parts[0]
            if len(parts) >= 2:
                result['유형'] = parts[1]
            break

    # --- 형식 판별: "성함 :" 레이블 여부 ---
    if '성함' in text:
        _parse_labeled(text, result)
    else:
        _parse_positional(non_empty, result)

    # --- 연락처: 전화번호 패턴 (공통) ---
    m = re.search(r'(0\d{1,2}[-\s]?\d{3,4}[-\s]?\d{4})', text)
    if m:
        result['연락처'] = m.group(1).strip()

    # --- 최종담당: ">" 다음 이름, 없으면 "미배정" ---
    m = re.search(r'>\s*(.+)', text)
    result['최종담당'] = m.group(1).strip() if m else '미배정'

    # --- 1차상담결과: "1차"로 시작하는 줄 → N열 ---
    for line in non_empty:
        if line.startswith('1차'):
            result['N열'] = line
            break

    # --- J열 / Q열 기본값 ---
    result['J열'] = '진행중'
    result['Q열'] = '진성'

    # --- 키워드 규칙 (허수/조건미달은 N열 포함 덮어쓰기) ---
    if '허수' in text:
        result['J열'] = '관리종료'
        result['N열'] = '반납'
        result['Q열'] = '허수'
    elif '조건미달' in text:
        result['J열'] = '반납'
        result['N열'] = '반납'
        result['Q열'] = '조건미달'

    # --- A급 DB ---
    if re.search(r'\bA\b', text):
        result['A급 DB'] = 'O'

    return result


def _parse_labeled(text: str, result: dict) -> None:
    """레이블 형식: 성함 :, 희망 지역 :, 현재 직업 : 등"""
    m = re.search(r'성함\s*:\s*(.+)', text)
    if m:
        name = m.group(1).strip()
        result['이름'] = re.sub(r'\s*\([남녀]\)', '', name).strip()

    m = re.search(r'희망\s*지역\s*:\s*(.+)', text)
    if m:
        result['희망지역'] = m.group(1).strip().replace(' ', '')

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


def _parse_positional(non_empty: list, result: dict) -> None:
    """레이블 없는 형식: 날짜 / 구분유형 / 이름 / 지역 / 1차상담결과 / 연락처"""
    # 날짜, 구분/유형, 전화번호, 1차... 줄 제외하고 순서대로 이름 → 지역 추출
    candidates = []
    for line in non_empty:
        if re.match(r'^\d{1,2}/\d{1,2}', line):
            continue  # 날짜
        if line == f"{result['구분']} {result['유형']}".strip() or line == result['구분']:
            continue  # 구분/유형 줄
        if re.match(r'^0\d{1,2}[-\s]?\d{3,4}[-\s]?\d{4}', line):
            continue  # 전화번호
        if line.startswith('1차'):
            continue  # 1차상담결과
        candidates.append(line)

    if len(candidates) >= 1:
        result['이름'] = re.sub(r'\s*\([남녀]\)', '', candidates[0]).strip()
    if len(candidates) >= 2:
        result['희망지역'] = candidates[1].replace(' ', '')


def _today() -> str:
    today = date.today()
    return f'{today.month}/{today.day}'
