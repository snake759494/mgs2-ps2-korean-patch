"""STAGE.DAT 해석: TOC/스테이지 헤더 복호화, 페이지 해제"""
import struct,zlib,sys,os
sys.path.insert(0,os.path.dirname(__file__))
from stagecrypt import *
def read_stage(f,w0,name,off,nxt):
    f.seek(off*0x800); raw=f.read((nxt-off)*0x800)
    k,i=stage_key(w0,name); hdr,_=crypt(raw[:0x800],k,i)
    n=struct.unpack_from('<I',hdr,0)[0]
    hsz=(n*8+4+0x7ff)&~0x7ff
    hdr,_=crypt(raw[:hsz],k,i)
    ents=[struct.unpack_from('<II',hdr,4+j*8) for j in range(n)]
    hsz=(n*8+4+0x7ff)&~0x7ff
    return raw,hsz,ents
def pages(raw,hsz,ents):
    """yield (group_idx, comp_off, comp_size, usize, files[(type,hash,off)])"""
    out=[];cur=None
    for a,b in ents:
        t=a>>24
        if a>>16==0x7f01 or (t==0x7f and (a&0xffffff) in (1,2,3) ):
            cur={'kind':a,'usize':b,'files':[],'comp':None}
        elif t==0x7e:
            cur['comp']=(b,a&0xffffff)
        elif t==0x7f:
            if cur: out.append(cur); cur=None
        else:
            if cur is not None: cur['files'].append((t,a&0xffffff,b))
    return out
def decode_page(raw,hsz,pg):
    if pg['comp']:
        off,cl=pg['comp']; p=page_decode(raw[hsz+off:hsz+off+cl])
        return zlib.decompressobj(-15).decompress(p[2:])
    return None
if __name__=='__main__':
    w0,t=toc(); f=open(STAGE,'rb')
    end=os.path.getsize(STAGE)//0x800
    os.makedirs('work/stage',exist_ok=True)
    for si,(name,off) in enumerate(t):
        nxt=t[si+1][1] if si+1<len(t) else end
        raw,hsz,ents=read_stage(f,w0,name,off,nxt)
        ps=pages(raw,hsz,ents)
        for pi,pg in enumerate(ps):
            u=decode_page(raw,hsz,pg)
            if u is None: print(name,pi,'uncompressed?',hex(pg['kind'])); continue
            open(f'work/stage/{name}_{pi}.bin','wb').write(u)
        print(name,len(ents),[ (hex(p['kind']),hex(p['usize']),len(p['files'])) for p in ps])
