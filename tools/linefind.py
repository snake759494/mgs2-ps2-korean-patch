"""텍스처 페이지에서 글자 줄 후보 상자 분할 -> 줄별 OCR 입력 이미지"""
import os, sys, json, glob
import numpy as np
from PIL import Image
from scipy import ndimage

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(R, 'work/lineimg')
os.makedirs(OUT, exist_ok=True)


def boxes_of(ix):
    vals, cnt = np.unique(ix, return_counts=True)
    bg = vals[cnt.argmax()]
    ink = ix != bg
    d = ndimage.binary_dilation(ink, structure=np.ones((3, 9), bool))
    lab, n = ndimage.label(d)
    out = []
    for sl in ndimage.find_objects(lab):
        y0, y1 = sl[0].start, sl[0].stop
        x0, x1 = sl[1].start, sl[1].stop
        h, w = y1 - y0, x1 - x0
        if not (7 <= h <= 90 and w >= 12 and w / h >= 0.8):
            continue
        reg = ink[y0:y1, x0:x1]
        if reg.mean() > 0.6 or reg.mean() < 0.05:
            continue
        out.append([int(x0), int(y0), int(x1), int(y1)])
    return merge(out)


def merge(bs):
    """같은 기준선 + 가까운 간격의 상자를 한 줄로 합침"""
    bs = sorted(bs)
    changed = True
    while changed:
        changed = False
        for i in range(len(bs)):
            for j in range(i + 1, len(bs)):
                a, b = bs[i], bs[j]
                ov = min(a[3], b[3]) - max(a[1], b[1])
                hh = min(a[3] - a[1], b[3] - b[1])
                xov = min(a[2], b[2]) - max(a[0], b[0])
                # 세로로 쪼개진 조각(가로가 크게 겹치고 세로 간격 2px 이하)
                if xov > 0.5 * min(a[2] - a[0], b[2] - b[0]) and -2 <= ov <= hh:
                    bs[i] = [min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3])]
                    del bs[j]
                    changed = True
                    break
                if ov < 0.6 * hh:
                    continue
                gap = max(a[0], b[0]) - min(a[2], b[2])
                if gap < 1.6 * max(a[3] - a[1], b[3] - b[1]):
                    bs[i] = [min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3])]
                    del bs[j]
                    changed = True
                    break
            if changed:
                break
    return bs


def main():
    pages = [f[:-4] for f in os.listdir(os.path.join(R, 'work/views'))]
    allb = {}
    for pg in pages:
        ix = np.asarray(Image.open(os.path.join(R, 'work/views/%s.png' % pg)))
        if ix.max() == 0:
            continue
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
            pad.save(os.path.join(OUT, '%s_%d.png' % (pg, k)))
    json.dump(allb, open(os.path.join(R, 'work/line_boxes.json'), 'w'))
    print(sum(len(v) for v in allb.values()))


if __name__ == '__main__':
    main()
