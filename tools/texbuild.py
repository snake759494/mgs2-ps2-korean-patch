"""텍스처 교체 사양 -> work/texrep.pkl
판정 소스:
  work/all_lines.json  + translation/texall_*.json      (전체 고유 줄 전수 판정)
  work/res_lines{n}.json + translation/texres{n}_*.json (교체 후 새로 생긴 줄 잔여 판정)
"""
import os, sys, json, pickle, hashlib, glob
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tex13, texpatch
from stagecrypt import toc, STAGE
from stage import read_stage, pages
from stagepack import page_decode_full

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_ko(pattern):
    ko = {}
    for p in sorted(glob.glob(os.path.join(R, pattern))):
        for k, v in json.load(open(p, encoding='utf8')).items():
            if v:
                ko[k] = v
    return ko


def rounds():
    out = [('work/all_lines2.json', 'translation/texall2_*.json')]
    n = 1
    while os.path.exists(os.path.join(R, 'work/res_lines%d.json' % n)):
        out.append(('work/res_lines%d.json' % n, 'translation/texres%d_*.json' % n))
        n += 1
    return out


def make_spec():
    spec = {}
    for lp, kp in rounds():
        L = json.load(open(os.path.join(R, lp), encoding='utf8'))
        ko = load_ko(kp)
        for i, (h, v) in enumerate(L):
            t = ko.get(str(i))
            if not t:
                continue
            for pg, (x0, y0, x1, y1) in v['locs']:
                spec.setdefault(pg, []).append([x0 - 1, y0 - 1, x1 + 1, y1 + 1, t])
    json.dump(spec, open(os.path.join(R, 'translation/tex_spec.json'), 'w', encoding='utf8'),
              ensure_ascii=False, indent=0)
    return spec


def collect_blobs(targets):
    w0, t = toc(os.path.join(R, STAGE))
    f = open(os.path.join(R, STAGE), 'rb')
    end = os.path.getsize(os.path.join(R, STAGE)) // 0x800
    found = {}
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
                if hh in targets and hh not in found:
                    found[hh] = blob
        if len(found) == len(targets):
            break
    return found


def main():
    final = os.path.join(R, 'translation/tex_boxes.json')
    if os.path.exists(final) and '--rejudge' not in sys.argv:
        spec = json.load(open(final, encoding='utf8'))      # 확정된 최종 상자 목록(수동 지정 포함)
        man = ''
    else:
        spec = make_spec()
        man = os.path.join(R, 'translation/tex_manual.json')
    vix = json.load(open(os.path.join(R, 'work/view_index.json')))
    if man and os.path.exists(man):
        for vid, boxes in json.load(open(man, encoding='utf8')).items():
            def hit(b):
                return any(not (b[2] <= m[0] or b[0] >= m[2] or b[3] <= m[1] or b[1] >= m[3]) for m in boxes)
            spec[vid] = [b for b in spec.get(vid, []) if not hit(b)] + boxes   # 수동 영역과 겹치는 자동 상자 제거
    byblob = {}
    for vid, boxes in spec.items():
        byblob.setdefault(vix[vid]['blob'], []).append((vid, boxes))
    blobs = collect_blobs(set(byblob))
    rep = {}
    od = os.path.join(R, 'work/views_mod')
    os.makedirs(od, exist_ok=True)
    for bh, items in byblob.items():
        blob = blobs[bh]
        img = len(blob) - 0xc00
        vm, idx = tex13.upload(blob[:img])
        for vid, boxes in items:
            tbp, tbw, psm = vix[vid]['view']
            a, ix = texpatch.view_render(vm, img, tbp, tbw, psm)
            H, W = ix.shape
            for x0, y0, x1, y1, t in boxes:
                texpatch.repaint(ix, (max(0, x0), max(0, y0), min(W, x1), min(H, y1)), t)
            texpatch.view_write(vm, a, ix, psm, img)
            Image.fromarray(ix).save(os.path.join(od, vid + '.png'))
        new = tex13.download(vm, idx)[:img]
        out = new + blob[len(new):]
        assert len(out) == len(blob)
        rep[bh] = out
    pickle.dump(rep, open(os.path.join(R, 'work/texrep.pkl'), 'wb'))
    print('교체 묶음', len(rep), '영역', len(spec), '상자', sum(len(b) for b in spec.values()))


if __name__ == '__main__':
    main()
