"""한국어 번역문 줄 배치(자동 줄바꿈)"""
import re
from width import ch_w

LIMIT = {'codec': 410, 'demo': 480, 'vox': 480, 'stage': 696}
MAXLINES = {'codec': 3, 'demo': 2, 'vox': 2}


def unit_w(u):
    """루비 {본문:루비}는 본문 폭만 계산"""
    m = re.fullmatch(r'\{(.*?):(.*?)\}', u)
    if m:
        u = m.group(1)
    return sum(ch_w(c) for c in u)


def tokens(s):
    """루비 묶음을 하나의 단위로 하는 토큰열"""
    return re.findall(r'\{[^{}]*\}|.', s, re.S)


def wrap_para(s, limit):
    """공백 기준 탐욕적 줄바꿈. 단어가 한 줄보다 길면 글자 단위로 자른다."""
    words = s.split(' ')
    lines = []
    cur = []
    cw = 0
    sp = ch_w(' ')
    for w in words:
        if w == '':
            continue
        ww = sum(unit_w(t) for t in tokens(w))
        if cur and cw + sp + ww <= limit:
            cur.append(w)
            cw += sp + ww
            continue
        if cur:
            lines.append(' '.join(cur))
        if ww <= limit:
            cur = [w]
            cw = ww
        else:
            # 긴 단어 강제 분할
            buf = ''
            bw = 0
            for t in tokens(w):
                tw = unit_w(t)
                if bw + tw > limit and buf:
                    lines.append(buf)
                    buf = ''
                    bw = 0
                buf += t
                bw += tw
            cur = [buf]
            cw = bw
    if cur:
        lines.append(' '.join(cur))
    return lines


def orig_lines(key, sep):
    body = key.rstrip('\n') if sep == '\n' else key
    return body.count(sep) + 1


def layout(ko, key, kind):
    """반환: (배치된 텍스트, 제한 준수 여부)"""
    ko = ko.replace('\r', '')
    if kind == 'stage':
        ok = all(sum(unit_w(t) for t in tokens(line)) <= LIMIT['stage']
                 for line in re.split(r'[|\n]', ko))
        return ko, ok
    sep = '\n' if kind == 'codec' else '|'
    # 번역자가 넣은 명시적 줄바꿈('\n' 또는 '|' 단독 사용)은 문단 구분으로 존중
    paras = re.split(r'\n|\|', ko.strip('\n'))
    lines = []
    for p in paras:
        lines += wrap_para(p.strip(), LIMIT[kind]) or ['']
    text = sep.join(lines)
    if kind == 'codec' and key.endswith('\n'):
        text += '\n'
    ok = len(lines) <= max(MAXLINES[kind], orig_lines(key, sep))
    return text, ok
