"""translation/ko_raw/*.json(번호->번역) -> translation/ko/main.json(원문키->번역) + 검사"""
import json, glob, os, re, sys
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(R, 'tools'))
from encode import SYM
keys = json.load(open(os.path.join(R, 'translation/keys.json'), encoding='utf8'))
ALLOWED = set(SYM) | set(chr(c) for c in range(0x20, 0x7f)) | {'\n'}
FIX = {'。': '.', '、': ', ', '！': '!', '？': '?', '～': '~', '〜': '~', '：': ':', '（': '(', '）': ')',
       '·': ' ', '∞': '무한', '—': '―', '–': '-', '…': '…', '％': '%', '／': '/', '＋': '+', '・': ' '}
out = {}
bad = []
for p in sorted(glob.glob(os.path.join(R, 'translation/ko_raw/*.json'))):
    for i, v in json.load(open(p, encoding='utf8')).items():
        if not isinstance(v, str):
            continue
        v = v.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
        v = ''.join(FIX.get(c, c) for c in v)
        v = re.sub(r'[ \t]+', ' ', v).replace('#', '')
        v = re.sub(r'(\d)\s*~\s*', r'\1~', v)
        # 전각 숫자/영문 -> 반각
        v = ''.join(chr(ord(c) - 0xfee0) if 0xff01 <= ord(c) <= 0xff5e else c for c in v)
        for c in v:
            if not ('가' <= c <= '힣' or c in ALLOWED):
                bad.append((i, c))
                v = v.replace(c, '')
        out[keys[i]] = v
os.makedirs(os.path.join(R, 'translation/ko'), exist_ok=True)
json.dump(out, open(os.path.join(R, 'translation/ko/main.json'), 'w', encoding='utf8'), ensure_ascii=False, indent=0)
print('병합', len(out), '제거한 문자', len(bad), sorted(set(c for _, c in bad))[:40])

# 번호 키 수정본(ko_fix.json) -> 원문 키 수정본(ko/zz_fix.json, 빌드가 마지막에 덮어씀)
fix = json.load(open(os.path.join(R, 'translation/ko_fix.json'), encoding='utf8'))
json.dump({keys[i]: v for i, v in fix.items()}, open(os.path.join(R, 'translation/ko/zz_fix.json'), 'w', encoding='utf8'),
          ensure_ascii=False, indent=0)
print('수정본', len(fix))
