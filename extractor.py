import re
from datetime import date


COLUMN_ORDER = ['구분', '유형', '접수월', '접수일', '배정일', '이름', '희망지역', '연락처', '최종담당', 'J열', 'N열', 'Q열', '첫메모', 'A급 DB']


def parse_customer_info(text: str) -> dict:
    result = {col: '' for col in COLUMN_ORDER}
    result['배정일'] = _today()

    lines = [line.strip() for line in text.strip().split('\n')]
    non_empty = [l for l in lines if l]

    if non_empty:
        m = re.match(r'^(\d{1,2})/(\d{1,2})', non_empty[0])
        if m:
            result['접수월'] = m.group(1)
            result['접수일'] = f'{m.group(1)}/{m.group(2)}'

    for line in non_empty:
        if not re.match(r'^\d{1,2}/\d{1,2}', line):
            parts = line.split()
            if len(parts) >= 1:
                result['구분'] = parts[0]
            if len(parts) >= 2:
                result['유형'] = parts[1]
            break

    if '성함' in text:
        _parse_labeled(text, result)
    else:
        _parse_positional(non_empty, result)

    m = re.search(r'(0\d{1,2}[-\s]?\d{3,4}[-\s]?\d{4})', text)
    if m:
        result['연락처'] = m.group(1).strip()

    m = re.search(r'>\s*(.+)', text)
    result['최종담당'] = m.group(1).strip() if m else '미배정'

    for line in non_empty:
        if line.startswith('1차'):
            result['N열'] = line
            break

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

    if re.search(r'\bA\b', text):
        result['A급 DB'] = 'O'

    return result


def _parse_labeled(text: str, result: dict) -> None:
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
    candidates = []
    for line in non_empty:
        if re.match(r'^\d{1,2}/\d{1,2}', line):
            continue
        if line == f"{result['구분']} {result['유형']}".strip() or line == result['구분']:
            continue
        if re.match(r'^0\d{1,2}[-\s]?\d{3,4}[-\s]?\d{4}', line):
            continue
        if line.startswith('1차'):
            continue
        candidates.append(line)

    if len(candidates) >= 1:
        result['이름'] = re.sub(r'\s*\([남녀]\)', '', candidates[0]).strip()
    if len(candidates) >= 2:
        result['희망지역'] = candidates[1].replace(' ', '')


def _today() -> str:
    today = date.today()
    return f'{today.month}/{today.day}'
