"""STAGE.DAT 재패킹"""
import struct,zlib,os,sys
sys.path.insert(0,os.path.dirname(__file__))
from stagecrypt import *
from stage import read_stage,pages
def crypt_full(buf,key,inc):
    pad=(-len(buf))%4
    o,k=crypt(buf+b'\0'*pad,key,inc); return o,k
def page_decode_full(raw,cl):
    seg=raw[:((cl+3)&~3)]
    h=struct.unpack_from('<H',seg,0)[0]; k,i=keyinit(h)
    o,_=crypt(seg,k,i); o=bytearray(o[:cl]); v=(struct.unpack_from('<H',o,0)[0]+0x8f3)&0xffff; struct.pack_into('<H',o,0,v)
    return zlib.decompress(bytes(o))
def page_encode(u,seed=0x5a5a):
    c=bytearray(zlib.compress(u,9)); c[0]=0x78; c[1]=0x9c
    v=(struct.unpack_from('<H',c,0)[0]-0x8f3)&0xffff; struct.pack_into('<H',c,0,v)
    assert v==0x9385
    k,i=keyinit(seed)
    o,_=crypt_full(bytes(c),k,i)
    return o,len(c)   # o는 4바이트 정렬 길이
def rebuild_stage(raw,name,w0,newpages):
    """newpages: {페이지번호: 새 비압축 데이터}. 새 스테이지 바이트(섹터 정렬) 반환"""
    k,i=stage_key(w0,name); hdr,_=crypt(raw[:0x800],k,i)
    n=struct.unpack_from('<I',hdr,0)[0]; hsz=(n*8+4+0x7ff)&~0x7ff
    hdr,_=crypt(raw[:hsz],k,i); hdr=bytearray(hdr)
    ents=[list(struct.unpack_from('<II',hdr,4+j*8)) for j in range(n)]
    # 페이지 순서대로 7e 항목 찾기
    out=bytearray(); pi=-1
    for j,(a,b) in enumerate(ents):
        if a>>24==0x7e:
            pi+=1; cl=a&0xffffff; off=b
            src=raw[hsz+off:hsz+off+((cl+3)&~3)]
            if pi in newpages:
                enc,ncl=page_encode(newpages[pi],struct.unpack_from('<H',src,0)[0])
            else:
                enc,ncl=src,cl
            noff=len(out); out+=enc
            while len(out)%0x800: out+=b'\0'
            ents[j]=[(0x7e<<24)|ncl,noff]
    for j,(a,b) in enumerate(ents): struct.pack_into('<II',hdr,4+j*8,a,b)
    eh,_=crypt(bytes(hdr),k,i)
    return eh+bytes(out)
def build_stagedat(stages,w0):
    """stages: [(name,bytes)] -> STAGE.DAT"""
    n=len(stages)
    toc=bytearray(); off=1
    for name,b in stages:
        toc+=name.encode().ljust(8,b'\0')+struct.pack('<I',off); off+=len(b)//0x800
    head=bytearray(struct.pack('<I',w0))
    # 원본 헤더 12바이트 구조 유지: (1,1,n,0x4010?) -> 원본에서 복사
    return head,toc
