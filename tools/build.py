"""MGS2(일본판) 한글패치 빌드: 번역 적용 -> 패치 ISO 생성"""
import os, sys, json, struct, pickle, shutil, collections, glob, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
from gcx import parse, rebuild, split_codec, has_local
from decode_all import block_kanji
from mgstext import decode
from encode import Encoder, CAP
from hfont import render_glyph, pack
from elfpatch import patch as elf_patch
from stagecrypt import toc, STAGE, crypt
from stage import read_stage, pages
from stagepack import page_decode_full, rebuild_stage
from chunks import walk
from wrap import layout
import hashlib
import tex13
TEXREP = {}
_tr = os.path.join(R, 'work/texrep.pkl')
if os.path.exists(_tr):
    TEXREP = pickle.load(open(_tr, 'rb'))

ISO = os.path.join(R, "Metal Gear Solid 2 - Sons of Liberty (Japan).iso")
OUT = os.path.join(R, "Metal Gear Solid 2 - Sons of Liberty (Korean).iso")
FONT = os.path.join(R, 'NanumSquareNeo-dEb.ttf')
LBA = {'SLPM': 284, 'DEMO': 470469, 'STAGE': 1345910, 'CODEC': 1658605, 'VOX': 1695572}
SIZE = {'SLPM': 831608, 'DEMO': 1792903168, 'STAGE': 640399360, 'CODEC': 44612672, 'VOX': 1174542336}


def log(*a):
    print(time.strftime('%H:%M:%S'), *a, flush=True)


def load_tr():
    tr = {}
    for p in sorted(glob.glob(os.path.join(R, 'translation/ko/*.json'))):
        for k, v in json.load(open(p, encoding='utf8')).items():
            if v:
                tr[k] = v
    return tr


class Ctx:
    def __init__(s, tr):
        s.tr = tr
        s.miss = collections.Counter()
        s.over = []

    def charset(s):
        cnt = collections.Counter()
        for v in s.tr.values():
            for ch in v:
                if '가' <= ch <= '힣':
                    cnt[ch] += 1
        chars = [c for c, _ in cnt.most_common()]
        if len(chars) > CAP:
            raise SystemExit('한글 %d자 > 용량 %d' % (len(chars), CAP))
        return chars


def conv(ctx, enc, kind, key):
    """원문 디코드 문자열 key -> 새 바이트 (번역 없으면 None)"""
    ko = ctx.tr.get(key)
    if ko is None:
        ctx.miss[key] += 1
        return None
    text, ok = layout(ko, key, kind)
    if not ok:
        ctx.over.append((kind, key, ko, text))
    return enc.enc(text, ruby_tail=('⟩}#' in key))


def do_gcx(ctx, enc, g, blk, kind):
    k = block_kanji(blk)
    new = {}
    for i, s in enumerate(blk['strs']):
        if s is None:
            continue
        b = conv(ctx, enc, kind, decode(s, k))
        if b is not None:
            new[i] = b
    if not new:
        return g
    while True:
        try:
            return rebuild(g, new)
        except OverflowError:
            grow = max(new, key=lambda i: len(new[i]) - len(blk['strs'][i]))
            ctx.over.append((kind, decode(blk['strs'][grow], k), 'GCX크기초과-원문유지', ''))
            del new[grow]


def sub_rebuild(c, blk, ctx, enc, kind, skip=None):
    fo = struct.unpack_from('<I', c, 0x10)[0]
    F = 0x14 + fo
    xtra = struct.unpack_from('<I', c, 0xc)[0]
    k = block_kanji(blk)
    p = 0x14
    ents = []
    while p < F - xtra:
        st, en, spk, ln = struct.unpack_from('<4I', c, p)
        ents.append((st, en, spk))
        p += ln
    out = bytearray(c[:0x14])
    changed = False
    texts = []
    skip = skip or set()
    for n_, ((st, en, spk), s) in enumerate(zip(ents, blk['strs'])):
        b = None if n_ in skip else conv(ctx, enc, kind, decode(s, k))
        if b is None:
            b = s
        else:
            changed = True
        texts.append(b)
        body = b + b'\0'
        body += b'\0' * ((-len(body)) % 4)
        out += struct.pack('<4I', st, en, spk, 16 + len(body)) + body
    if not changed:
        return c
    keep = any(has_local(t) for t in texts)
    out += c[F - xtra:F]
    struct.pack_into('<I', out, 0x10, len(out) - 0x14)
    glyph = c[F + 4:F + 4 + struct.unpack_from('<I', c, F)[0]] if keep else b''
    out += struct.pack('<I', len(glyph)) + glyph
    if len(out) > len(c):
        grow = max((i for i in range(len(texts)) if i not in skip),
                   key=lambda i: len(texts[i]) - len(blk['strs'][i]))
        ctx.over.append((kind, decode(blk['strs'][grow], k), '청크크기초과-원문유지', ''))
        return sub_rebuild(c, blk, ctx, enc, kind, skip | {grow})
    out += b'\0' * (len(c) - len(out))
    return bytes(out)


def patch_dir(iso, name, lba, size):
    """ISO9660 디렉터리 레코드에서 이름을 찾아 LBA/크기 수정"""
    nb = name.encode()
    for sec in DIRSECS:
        iso.seek(sec * 2048)
        blk = bytearray(iso.read(2048))
        p = 0
        hit = False
        while p < 2048:
            L = blk[p]
            if L == 0:
                break
            nl = blk[p + 32]
            if blk[p + 33:p + 33 + nl] == nb:
                struct.pack_into('<I', blk, p + 2, lba)
                struct.pack_into('>I', blk, p + 6, lba)
                struct.pack_into('<I', blk, p + 10, size)
                struct.pack_into('>I', blk, p + 14, size)
                hit = True
            p += L
        if hit:
            iso.seek(sec * 2048)
            iso.write(blk)
            return
    raise SystemExit('디렉터리 레코드 없음: ' + name)


def _crc_itu(b):
    crc = 0
    for x in b:
        crc ^= x << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xffff if crc & 0x8000 else (crc << 1) & 0xffff
    return crc


def patch_udf(iso, old_lba, lba, size):
    """UDF 파일 항목(태그 261)에서 old_lba 를 가리키는 단일 short_ad 를 새 위치·크기로 수정"""
    iso.seek(256 * 2048)
    a = iso.read(2048)
    vlen, vloc = struct.unpack_from('<II', a, 16)
    ps = None
    for s in range(vloc, vloc + vlen // 2048):
        iso.seek(s * 2048)
        b = iso.read(2048)
        if struct.unpack_from('<H', b, 0)[0] == 5:
            ps = struct.unpack_from('<I', b, 188)[0]
            break
    for s in range(ps, ps + 4000):
        iso.seek(s * 2048)
        b = bytearray(iso.read(2048))
        if struct.unpack_from('<H', b, 0)[0] != 261:
            continue
        l_ea = struct.unpack_from('<I', b, 168)[0]
        ln, pos = struct.unpack_from('<II', b, 176 + l_ea)
        if pos + ps != old_lba:
            continue
        struct.pack_into('<Q', b, 56, size)                          # Information Length
        struct.pack_into('<Q', b, 64, (size + 2047) // 2048)         # Logical Blocks Recorded
        struct.pack_into('<II', b, 176 + l_ea, (ln & 0xc0000000) | size, lba - ps)
        crclen = struct.unpack_from('<H', b, 10)[0]
        struct.pack_into('<H', b, 8, _crc_itu(bytes(b[16:16 + crclen])))
        b[4] = sum(b[i] for i in range(16) if i != 4) & 0xff
        iso.seek(s * 2048)
        iso.write(b)
        return
    raise SystemExit('UDF 파일 항목 없음')


DIRSECS = []


def main():
    import pycdlib
    pi = pycdlib.PyCdlib()
    pi.open(ISO)
    DIRSECS.extend([pi.pvd.root_directory_record().extent_location(),
                    pi.get_record(iso_path='/MGS2').extent_location()])
    pi.close()
    tr = load_tr()
    ctx = Ctx(tr)
    chars = ctx.charset()
    log('번역', len(tr), '한글 글자수', len(chars))
    json.dump(chars, open(os.path.join(R, 'translation/charset.json'), 'w', encoding='utf8'), ensure_ascii=False)
    enc = Encoder(chars)
    font = b''.join(pack(render_glyph(c, FONT, 23)) for c in chars)
    blocks = pickle.load(open(os.path.join(R, 'work/blocks.pkl'), 'rb'))
    byid = {}
    for b in blocks:
        bid = b['id']
        byid[(b['src'], tuple(bid) if isinstance(bid, list) else bid)] = b
    log('ISO 복사')
    shutil.copyfile(ISO, OUT)
    iso = open(OUT, 'r+b')
    # CODEC.DAT
    d = bytearray(open(os.path.join(R, 'extract/CODEC.DAT'), 'rb').read())
    for j, (a, b) in enumerate(split_codec(bytes(d))):
        d[a:b] = do_gcx(ctx, enc, bytes(d[a:b]), byid[('codec', j)], 'codec')
    iso.seek(LBA['CODEC'] * 2048)
    iso.write(d)
    log('CODEC 완료')
    # STAGE.DAT
    w0, t = toc(os.path.join(R, STAGE))
    f = open(os.path.join(R, STAGE), 'rb')
    end = SIZE['STAGE'] // 0x800
    f.seek(0)
    orig_head = f.read(0x800)
    for si, (name, off) in enumerate(t):
        nxt = t[si + 1][1] if si + 1 < len(t) else end
        raw, hsz, ents = read_stage(f, w0, name, off, nxt)
        newpages = {}
        for pj, pg in enumerate(pages(raw, hsz, ents)):
            gf = [x for x in pg['files'] if x[0] == 6]
            tf = [x for x in pg['files'] if x[0] == 0x13]
            if not gf and not (tf and TEXREP):
                continue
            co, cl = pg['comp']
            u = bytearray(page_decode_full(raw[hsz + co:], cl))
            fl = sorted(pg['files'], key=lambda x: x[2])
            ch = False
            for ty, h, o in tf:
                kk = [x[2] for x in fl].index(o)
                e = fl[kk + 1][2] if kk + 1 < len(fl) else pg['usize']
                fb = bytes(u[o:e])
                try:
                    p = tex13.parse(fb)
                except Exception:
                    p = None
                if not p or p['doff'] + p['dsz'] > len(fb):
                    continue
                blob = fb[p['doff']:p['doff'] + p['dsz']]
                nb = TEXREP.get(hashlib.md5(blob).hexdigest()[:12])
                if nb is not None:
                    assert len(nb) == p['dsz'], '텍스처 길이 불일치'
                    u[o + p['doff']:o + p['doff'] + p['dsz']] = nb
                    ch = True
            for ty, h, o in gf:
                kk = [x[2] for x in fl].index(o)
                e = fl[kk + 1][2] if kk + 1 < len(fl) else pg['usize']
                g = bytes(u[o:e])
                ng = do_gcx(ctx, enc, g, byid[('stage', (name, pj, h))], 'stage')
                if ng != g:
                    u[o:e] = ng
                    ch = True
            if ch:
                newpages[pj] = bytes(u)
        if newpages:
            sb = rebuild_stage(raw, name, w0, newpages)
            if len(sb) > len(raw):
                raise SystemExit('스테이지 증가: %s %d > %d' % (name, len(sb), len(raw)))
            sb = sb + b'\0' * (len(raw) - len(sb))
            # 길이가 원본과 같으므로 TOC 오프셋도 그대로: 원래 위치에 바로 기록(메모리 절약)
            iso.seek(LBA['STAGE'] * 2048 + off * 0x800)
            iso.write(sb)
        del raw
    log('STAGE 완료')
    # DEMO/VOX 자막
    for nm in ('DEMO', 'VOX'):
        n = 0
        for pos, ty, s, get in walk(nm, ISO):
            if ty != 4:
                continue
            blk = byid.get((nm.lower(), pos))
            if blk is None:
                continue
            c = get()
            nc = sub_rebuild(c, blk, ctx, enc, nm.lower())
            if nc != c:
                iso.seek(LBA[nm] * 2048 + pos)
                iso.write(nc)
                n += 1
        log(nm, '청크 수정', n)
    # ELF: VOX.DAT 뒤 빈 공간(마지막 UDF 앵커 앞)에 배치. ISO 크기는 원본 그대로.
    elf = open(os.path.join(R, 'extract/SLPM_650.78'), 'rb').read()
    ne = elf_patch(elf, font)
    newlba = LBA['VOX'] + SIZE['VOX'] // 2048
    iso.seek(0, 2)
    total = iso.tell() // 2048
    nsec = (len(ne) + 2047) // 2048
    if newlba + nsec > total - 1:
        raise SystemExit('ELF 가 빈 공간을 넘침: %d 섹터' % nsec)
    iso.seek(newlba * 2048)
    iso.write(ne + b'\0' * ((-len(ne)) % 2048))
    patch_dir(iso, 'SLPM_650.78;1', newlba, len(ne))
    patch_udf(iso, 284, newlba, len(ne))
    iso.close()
    log('미번역', len(ctx.miss), '줄넘침', len(ctx.over))
    json.dump([list(x) for x in ctx.over], open(os.path.join(R, 'work/overflow.json'), 'w', encoding='utf8'),
              ensure_ascii=False, indent=0)
    json.dump(list(ctx.miss), open(os.path.join(R, 'work/missing.json'), 'w', encoding='utf8'),
              ensure_ascii=False, indent=0)


if __name__ == '__main__':
    main()
