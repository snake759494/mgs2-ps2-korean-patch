"""0x13 묶음의 텍스처 영역(view)별 인덱스 이미지 생성 (전수조사용)
출력: work/views/{blob}_{tbp}_{tbw}_{psm}.png (원시 인덱스), work/view_index.json
"""
import sys, os, json, hashlib
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tex13
import texpatch
from stagecrypt import toc, STAGE
from stage import read_stage, pages
from stagepack import page_decode_full

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(R, 'work/views')
os.makedirs(OUT, exist_ok=True)


def blob_views(fb, p, blob):
    img = len(blob) - 0xc00
    vm, idx = tex13.upload(blob[:img])
    vs = texpatch.views_of(fb, p)
    if not vs:
        npages = max(1, (img + 8191) // 8192)
        vs = [(0, texpatch.best_tbw(vm, npages), 0x14)]
    out = []
    for tbp, tbw, psm in vs:
        a, ix = texpatch.view_render(vm, img, tbp, tbw, psm)
        out.append(((tbp, tbw, psm), ix))
    return out


def main():
    w0, t = toc(os.path.join(R, STAGE))
    f = open(os.path.join(R, STAGE), 'rb')
    end = os.path.getsize(os.path.join(R, STAGE)) // 0x800
    index = {}
    for si, (name, off) in enumerate(t):
        nxt = t[si + 1][1] if si + 1 < len(t) else end
        raw, hsz, ents = read_stage(f, w0, name, off, nxt)
        for pj, pg in enumerate(pages(raw, hsz, ents)):
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
                if not p or p['doff'] + p['dsz'] > len(fb) or p['dsz'] < 0x1000:
                    continue
                blob = fb[p['doff']:p['doff'] + p['dsz']]
                hsh = hashlib.md5(blob).hexdigest()[:12]
                if any(v['blob'] == hsh for v in index.values()):
                    continue
                tex13._cache.clear()
                for (tbp, tbw, psm), ix in blob_views(fb, p, blob):
                    vid = '%s_%d_%d_%d' % (hsh, tbp, tbw, psm)
                    Image.fromarray(ix).save(os.path.join(OUT, vid + '.png'))
                    index[vid] = dict(blob=hsh, view=[tbp, tbw, psm])
        print(name, len(index), flush=True)
    json.dump(index, open(os.path.join(R, 'work/view_index.json'), 'w'), indent=0)


if __name__ == '__main__':
    main()
