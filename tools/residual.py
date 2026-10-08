"""교체 후 페이지(및 전체 후보 페이지)의 남은 일본어 줄 탐지 준비
사용: python residual.py prep  -> work/resimg/*.png, work/res_boxes.json
      (PowerShell OCR) -> work/ocr_res.tsv
      python residual.py list  -> work/res_lines.json, work/res_sheet/*.png
"""
import os, sys, json, pickle, re, hashlib, collections
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import texpatch
from linefind import boxes_of

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def cur_pages():
    rep = pickle.load(open(os.path.join(R, 'work/texrep.pkl'), 'rb'))
    pages = json.load(open(os.path.join(R, 'work/cand_pages.json')))
    out = {}
    for pg in pages:
        if pg in rep:
            _, _, _, ix = texpatch.page_indices(rep[pg])
        else:
            ix = np.asarray(Image.open(os.path.join(R, 'work/pages/%s.png' % pg))) // 17
        out[pg] = ix
    return out


def prep():
    od = os.path.join(R, 'work/resimg')
    os.makedirs(od, exist_ok=True)
    for f in os.listdir(od):
        os.remove(os.path.join(od, f))
    allb = {}
    for pg, ix in cur_pages().items():
        bs = boxes_of(ix)
        allb[pg] = bs
        for k, (x0, y0, x1, y1) in enumerate(bs):
            c = ix[max(0, y0 - 2):y1 + 2, max(0, x0 - 2):x1 + 2].astype(np.float32)
            c = 255 - np.clip(c * 255 / max(1, c.max()), 0, 255)
            im = Image.fromarray(c.astype(np.uint8))
            sc = max(2, int(60 / im.height))
            im = im.resize((im.width * sc, im.height * sc), Image.LANCZOS)
            pad = Image.new('L', (im.width + 40, im.height + 40), 255)
            pad.paste(im, (20, 20))
            pad.save(os.path.join(od, '%s_%d.png' % (pg, k)))
    json.dump(allb, open(os.path.join(R, 'work/res_boxes.json'), 'w'))
    print(sum(len(v) for v in allb.values()))


def listing():
    B = json.load(open(os.path.join(R, 'work/res_boxes.json')))
    txt = collections.defaultdict(str)
    for l in open(os.path.join(R, 'work/ocr_res.tsv'), encoding='utf-8-sig'):
        r = l.rstrip('\n').split('\t')
        if len(r) >= 2:
            txt[r[0]] += r[-1]
    pages = cur_pages()
    U = collections.OrderedDict()
    for name, t in txt.items():
        if len(re.findall(r'[\u3040-\u30ff\u4e00-\u9fff]', t)) < 2:
            continue
        pg, k = name.rsplit('_', 1)
        x0, y0, x1, y1 = B[pg][int(k)]
        c = pages[pg][y0:y1, x0:x1]
        h = hashlib.md5(c.tobytes() + str(c.shape).encode()).hexdigest()[:10]
        U.setdefault(h, dict(ocr=re.sub(r'\s', '', t), locs=[]))['locs'].append([pg, [x0, y0, x1, y1]])
    items = list(U.items())
    json.dump(items, open(os.path.join(R, 'work/res_lines.json'), 'w', encoding='utf8'), ensure_ascii=False)
    with open(os.path.join(R, 'work/res_lines.txt'), 'w', encoding='utf8') as f:
        for i, (h, v) in enumerate(items):
            f.write('%d\t%d\t%s\n' % (i, len(v['locs']), v['ocr']))
    sd = os.path.join(R, 'work/res_sheet')
    os.makedirs(sd, exist_ok=True)
    for f in os.listdir(sd):
        os.remove(os.path.join(sd, f))
    fnt = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 14)
    per = 40
    for s in range(0, len(items), per):
        sh = Image.new('RGB', (900, per * 40), (25, 25, 45))
        d = ImageDraw.Draw(sh)
        for i, (h, v) in enumerate(items[s:s + per]):
            pg, (x0, y0, x1, y1) = v['locs'][0]
            c = Image.fromarray((pages[pg][y0:y1, x0:x1] * 17).astype(np.uint8)).convert('RGB')
            sc = min(2, 36 / max(1, c.height))
            c = c.resize((max(1, int(c.width * sc)), max(1, int(c.height * sc))))
            if c.width > 840:
                c = c.crop((0, 0, 840, c.height))
            sh.paste(c, (55, i * 40 + 2))
            d.text((4, i * 40 + 10), str(s + i), font=fnt, fill=(255, 255, 0))
        sh.save(os.path.join(sd, 'r_%03d.png' % s))
    print(len(items))


if __name__ == '__main__':
    prep() if sys.argv[1] == 'prep' else listing()
