"""교체한 텍스처의 바뀐 조각(원본->한글)을 다른 묶음의 동일 원본 조각에도 적용
같은 그림이 여러 묶음에 GS 배치 그대로 복사돼 있는 경우(오프닝 크레디트 등)를 잡는다.
입력: work/texrep.pkl (묶음해시 -> 새 블롭)  출력: work/texrep.pkl 갱신(사본 추가)
"""
import os, sys, pickle, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tex13
from texbuild import collect_blobs
from stagecrypt import toc, STAGE
from stage import read_stage, pages
from stagepack import page_decode_full

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLK = 64


def all_blobs():
    w0, t = toc(os.path.join(R, STAGE))
    f = open(os.path.join(R, STAGE), 'rb')
    end = os.path.getsize(os.path.join(R, STAGE)) // 0x800
    seen = set()
    for si, (name, off) in enumerate(t):
        nxt = t[si + 1][1] if si + 1 < len(t) else end
        raw, hsz, ents = read_stage(f, w0, name, off, nxt)
        for pg in pages(raw, hsz, ents):
            fl = sorted(pg['files'], key=lambda x: x[2])
            if not any(x[0] == 0x13 for x in fl):
                continue
            u = page_decode_full(raw[hsz + pg['comp'][0]:], pg['comp'][1])
            for k, (ty, h, o) in enumerate(fl):
                if ty != 0x13:
                    continue
                e = fl[k + 1][2] if k + 1 < len(fl) else pg['usize']
                fb = u[o:e]
                try:
                    p = tex13.parse(fb)
                except Exception:
                    p = None
                if not p or p['doff'] + p['dsz'] > len(fb):
                    continue
                blob = fb[p['doff']:p['doff'] + p['dsz']]
                hh = hashlib.md5(blob).hexdigest()[:12]
                if hh not in seen:
                    seen.add(hh)
                    yield hh, blob


def main():
    src = os.path.join(R, 'work/texrep_base.pkl')
    if not os.path.exists(src):
        os.replace(os.path.join(R, 'work/texrep.pkl'), src)
    rep = pickle.load(open(src, 'rb'))
    orig = collect_blobs(set(rep))
    # 교체 묶음별 바뀐 조각 목록 (잉크가 있는 조각만)
    per = {}
    for hh, nb in rep.items():
        ob = orig[hh]
        img = len(ob) - 0xc00
        lst = []
        for i in range(0, img - BLK + 1, BLK):
            a, b = ob[i:i + BLK], nb[i:i + BLK]
            if a != b and a.count(0) < BLK // 2:
                lst.append((a, b))
        per[hh] = lst
    blobs = dict(all_blobs())
    # 조각이 등장하는 묶음 수 (흔한 패턴 제외용)
    keyset = set(a for lst in per.values() for a, b in lst)
    freq = {}
    for hh, blob in blobs.items():
        img = len(blob) - 0xc00
        seen = set()
        for i in range(0, img - BLK + 1, BLK):
            c = blob[i:i + BLK]
            if c in keyset and c not in seen:
                seen.add(c)
                freq[c] = freq.get(c, 0) + 1
    added = 0
    for hh, blob in blobs.items():
        if hh in rep:
            continue
        img = len(blob) - 0xc00
        chunks = {}
        for i in range(0, img - BLK + 1, BLK):
            chunks.setdefault(blob[i:i + BLK], []).append(i)
        nb = bytearray(blob)
        hit_src = []
        for sh, lst in per.items():
            good = [(a, b) for a, b in lst if freq.get(a, 0) <= 30]
            if len(good) < 16:
                continue
            m = [(a, b) for a, b in good if a in chunks]
            if len(m) >= 0.5 * len(good):
                for a, b in m:
                    for i in chunks[a]:
                        nb[i:i + BLK] = b
                hit_src.append((sh, len(m), len(good)))
        if hit_src:
            rep[hh] = bytes(nb)
            added += 1
            print('사본', hh, hit_src)
    pickle.dump(rep, open(os.path.join(R, 'work/texrep.pkl'), 'wb'))
    print('추가 묶음', added, '전체', len(rep))


if __name__ == '__main__':
    main()
