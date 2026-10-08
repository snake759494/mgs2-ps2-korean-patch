"""원본 ISO 추출본에서 문자열 번호->원문 키(translation/keys.json, 비공개) 생성
선행: python tools/extract.py
"""
import os, sys, json, pickle, subprocess
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
subprocess.check_call([sys.executable, os.path.join(R, 'tools/decode_all.py')], cwd=R)
uniq = pickle.load(open(os.path.join(R, 'work/uniq.pkl'), 'rb'))
json.dump({str(i): k for i, k in enumerate(uniq)}, open(os.path.join(R, 'translation/keys.json'), 'w', encoding='utf8'),
          ensure_ascii=False)
print('keys', len(uniq))
