"""전 스테이지 0x13 스프라이트 전수 추출 -> work/spr/*.png + work/spr_index.json"""
import sys, os, json, hashlib, struct
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tex13
from stagecrypt import toc, STAGE
from stage import read_stage, pages
from stagepack import page_decode_full

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(R, 'work/spr')
os.makedirs(OUT, exist_ok=True)


def render_pack(f, p):
    """팩의 각 스프라이트 -> (인덱스배열, RGBA)"""
    img_sz = p['dsz'] - 0xc00 if p['dsz'] > 0xc00 else p['dsz']
    vm, _ = tex13.upload(f[p['doff']:p['doff'] + img_sz])
    cl = np.frombuffer(f[p['doff'] + img_sz:p['doff'] + p['dsz']], np.uint8).reshape(-1, 4)
    res = []
    for e in p['ents']:
        t = tex13.tex0(e['t0'])
        x0, y0, w, h = tex13.sprite_box(t, e['rect'])
        if w <= 0 or h <= 0 or w > 1024 or h > 1024 or t['psm'] != 0x14:
            res.append(None)
            continue
        a = tex13.a4(t['tbp'], t['tbw'], t['tw'], t['th'])[y0:y0 + h, x0:x0 + w]
        b = vm[a >> 1]
        ix = np.where(a & 1, b >> 4, b & 15)
        base = t['csa'] * 16
        if base + 16 > len(cl):
            res.append(None)
            continue
        pal = cl[base:base + 16]
        res.append((ix, pal[ix]))
    return res


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
                if not p or p['doff'] + p['dsz'] > len(fb):
                    continue
                for si2, r in enumerate(render_pack(fb, p)):
                    if r is None:
                        continue
                    ix, rgba = r
                    hsh = hashlib.md5(ix.tobytes() + rgba.tobytes()).hexdigest()[:12]
                    ref = [name, pj, h, si2]
                    if hsh in index:
                        index[hsh]['refs'].append(ref)
                        continue
                    a = rgba.astype(np.uint16)
                    a[..., 3] = np.minimum(a[..., 3] * 2, 255)
                    Image.fromarray(a.astype(np.uint8), 'RGBA').save(os.path.join(OUT, hsh + '.png'))
                    index[hsh] = dict(size=list(ix.shape[::-1]), refs=[ref])
        print(name, len(index), flush=True)
    json.dump(index, open(os.path.join(R, 'work/spr_index.json'), 'w'), indent=0)


if __name__ == '__main__':
    main()
