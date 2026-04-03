import re
from datetime import date


COLUMN_ORDER = ['구분', '유형', '접수월', '접수일', '배정일', '이름', '희망지역', '연락처', '최종담당', 'J열', 'N열', 'Q열', '첫메모', 'A급 DB']


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

    # --- 접수월 / 접수일: 첫 줄에서 "M/D" 추출 (뒤에 다른 내용 있어도 인식) ---
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

    # --- J열 / N열 / Q열: 기본값 및 특수 키워드 처리 ---
    result['J열'] = '진행중'
    result['Q열'] = '진성'

    if '허수' in text:
        result['J열'] = '관리종료'
        result['N열'] = '반납'
        result['Q열'] = '허수'
    elif '조건미달' in text:
        result['J열'] = '반납'
        result['N열'] = '반납'
        result['Q열'] = '조건미달'

    # --- A급 DB: 텍스트 전체에 "A" 포함 시 체크 ---
    if re.search(r'\bA\b', text):
        result['A급 DB'] = 'O'

    # --- 이름 (성함): 성별 제거 ---
    m = re.search(r'성함\s*:\s*(.+)', text)
    if m:
        name = m.group(1).strip()
        result['이름'] = re.sub(r'\s*\([남녀]\)', '', name).strip()

    # --- 희망지역: 띄어쓰기 제거 ---
    m = re.search(r'희망\s*지역\s*:\s*(.+)', text)
    if m:
        result['희망지역'] = m.group(1).strip().replace(' ', '')

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
