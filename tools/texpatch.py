"""텍스처 페이지(4bpp, tbw16) 글자 교체 -> 새 블롭"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tex13

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT = os.path.join(R, 'NanumSquareNeo-cBd.ttf')


def _render(vm, tbw, npages):
    pw = tbw // 2                      # 가로 4bpp 페이지 수
    rows = max(1, (npages + pw - 1) // pw)
    a = tex13.a4(0, tbw, tbw * 64, rows * 128)
    b = vm[a >> 1]
    return a, np.where(a & 1, b >> 4, b & 15).astype(np.uint8)


def _discont(ix):
    """페이지 경계(128px)에서 잉크 불연속 정도"""
    v, c = np.unique(ix, return_counts=True)
    m = ix != v[c.argmax()]
    s = 0.0
    n = 0
    for y in range(128, m.shape[0], 128):
        s += (m[y - 1] != m[y]).sum()
        n += m.shape[1]
    for x in range(128, m.shape[1], 128):
        s += (m[:, x - 1] != m[:, x]).sum()
        n += m.shape[0]
    return s / max(1, n)


def best_tbw(vm, npages):
    best = None
    for tbw in (16, 8, 4, 2):
        a, ix = _render(vm, tbw, npages)
        sc = _discont(ix)
        if best is None or sc < best[0] - 1e-4:
            best = (sc, tbw)
    return best[1]


def page_indices(blob, tbw=None):
    img = len(blob) - 0xc00
    vm, idx = tex13.upload(blob[:img])
    npages = max(1, (img + 8191) // 8192)
    if tbw is None:
        tbw = best_tbw(vm, npages)
    a, ix = _render(vm, tbw, npages)
    return vm, idx, a, ix


def render_text(text, w, h):
    """w x h 상자에 맞춘 커버리지(0~1) 배열"""
    size = max(6, int(h * 0.92))
    while True:
        f = ImageFont.truetype(FONT, size * 4)
        bb = f.getbbox(text)
        tw, th = bb[2] - bb[0], bb[3] - bb[1]
        if tw <= w * 4 or size <= 6:
            break
        size -= 1
    im = Image.new('L', (w * 4, h * 4), 0)
    d = ImageDraw.Draw(im)
    asc, desc = f.getmetrics()
    d.text(((w * 4 - tw) // 2 - bb[0], (h * 4 - th) // 2 - bb[1]), text, font=f, fill=255)
    return np.asarray(im.resize((w, h), Image.LANCZOS), np.float32) / 255


def repaint(ix, box, text):
    """ix: 페이지 인덱스 배열(수정됨). box=(x0,y0,x1,y1). text에 줄바꿈이 있으면 상자를 세로로 나눠 여러 줄"""
    NL = chr(10)
    if NL in text:
        lines = text.split(NL)
        x0, y0, x1, y1 = box
        hh = (y1 - y0) / len(lines)
        # 배경/잉크 인덱스는 전체 상자 기준으로 먼저 결정
        H, W = ix.shape
        reg = ix[max(0, y0):min(H, y1), max(0, x0):min(W, x1)]
        border = np.concatenate([reg[0], reg[-1], reg[:, 0], reg[:, -1]])
        vals, cnt = np.unique(border, return_counts=True)
        bg = int(vals[cnt.argmax()])
        v2, c2 = np.unique(reg[reg != bg], return_counts=True)
        order = v2[np.argsort(-c2)] if len(v2) else [bg]
        core = int(order[0]); edge = int(order[1]) if len(order) > 1 else core
        reg[:] = bg
        for k, ln in enumerate(lines):
            a, b = int(round(y0 + k * hh)), int(round(y0 + (k + 1) * hh))
            sub = ix[max(0, a):min(H, b), max(0, x0):min(W, x1)]
            cov = render_text(ln, sub.shape[1], sub.shape[0])
            sub[cov > 0.25] = edge
            sub[cov > 0.55] = core
        return
    H, W = ix.shape
    x0, y0, x1, y1 = max(0, box[0]), max(0, box[1]), min(W, box[2]), min(H, box[3])
    if x1 - x0 < 2 or y1 - y0 < 2:
        return
    reg = ix[y0:y1, x0:x1]
    border = np.concatenate([reg[0], reg[-1], reg[:, 0], reg[:, -1]])
    vals, cnt = np.unique(border, return_counts=True)
    bg = int(vals[cnt.argmax()])
    v2, c2 = np.unique(reg[reg != bg], return_counts=True)
    if len(v2) == 0:
        return
    order = v2[np.argsort(-c2)]
    core = int(order[0])
    edge = int(order[1]) if len(order) > 1 else core
    cov = render_text(text, x1 - x0, y1 - y0)
    out = np.full(reg.shape, bg, np.uint8)
    out[cov > 0.25] = edge
    out[cov > 0.55] = core
    ix[y0:y1, x0:x1] = out


def write_back(vm, idx, a, ix, blob):
    flat_a = a.ravel()
    flat_i = ix.ravel().astype(np.uint8)
    byte = flat_a >> 1
    hi = (flat_a & 1).astype(bool)
    cur = vm[byte]
    vm[byte[~hi]] = (cur[~hi] & 0xf0) | flat_i[~hi]
    cur = vm[byte]
    vm[byte[hi]] = (cur[hi] & 0x0f) | (flat_i[hi] << 4)
    img = len(blob) - 0xc00
    new = tex13.download(vm, idx)[:img]
    out = new + blob[len(new):]          # 256바이트 미만 자투리와 CLUT은 원본 유지
    assert len(out) == len(blob)
    return out


# ---- 묶음 내 텍스처 영역(view)별 처리 ----
def views_of(fb, p):
    """스프라이트 항목의 (tbp, tbw, psm) 집합. 없으면 None"""
    vs = set()
    for e in p['ents']:
        t = tex13.tex0(e['t0'])
        if t['psm'] in (0x13, 0x14) and t['tbw'] > 0:
            vs.add((t['tbp'], t['tbw'], t['psm']))
    return sorted(vs) if vs else None


def view_render(vm, img, tbp, tbw, psm):
    """해당 영역을 데이터 범위 안에서 렌더링 -> (주소배열, 인덱스배열)"""
    total_blocks = img // 256
    if psm == 0x14:
        pw, ph = 128, 128
        fn = tex13.a4
    else:
        pw, ph = 128, 64
        fn = tex13.a8
    pages_per_row = max(1, tbw // 2)
    npages = max(1, (total_blocks - tbp + 31) // 32)
    rows = max(1, (npages + pages_per_row - 1) // pages_per_row)
    a = fn(tbp, tbw, tbw * 64, rows * ph)
    if psm == 0x14:
        valid = (a >> 1) < img
        b = vm[np.minimum(a >> 1, len(vm) - 1)]
        ix = np.where(a & 1, b >> 4, b & 15).astype(np.uint8)
    else:
        valid = a < img
        ix = vm[np.minimum(a, len(vm) - 1)].astype(np.uint8)
    ix[~valid] = 0
    return a, ix


def view_write(vm, a, ix, psm, img):
    fa = a.ravel()
    fi = ix.ravel().astype(np.uint8)
    if psm == 0x14:
        byte = fa >> 1
        ok = byte < img
        byte, fa, fi = byte[ok], fa[ok], fi[ok]
        hi = (fa & 1).astype(bool)
        cur = vm[byte]
        vm[byte[~hi]] = (cur[~hi] & 0xf0) | fi[~hi]
        cur = vm[byte]
        vm[byte[hi]] = (cur[hi] & 0x0f) | (fi[hi] << 4)
    else:
        ok = fa < img
        vm[fa[ok]] = fi[ok]
